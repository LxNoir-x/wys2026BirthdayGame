"""Export a PSD level into reusable assets and a runtime map from a JSON config."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image
from psd_tools import PSDImage

ROOT = Path(__file__).resolve().parents[1]


def project_path(value: str) -> Path:
    """Resolve a config path relative to the repository root."""

    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "layer"


def layer_at(psd, path: list[int]):
    layer = psd
    try:
        for index in path:
            layer = layer[index]
    except (IndexError, TypeError) as error:
        raise ValueError(f"Invalid PSD layer index path: {path}") from error
    return layer


def layer_image(layer):
    image = layer.composite()
    if image is None:
        return None
    left, top, right, bottom = (int(value) for value in layer.bbox)
    expected_size = (right - left, bottom - top)
    if image.size != expected_size and right <= image.width and bottom <= image.height:
        image = image.crop((left, top, right, bottom))
    return image.convert("RGBA")


def alpha_fingerprint(image) -> tuple[tuple[int, int], str] | None:
    alpha_bounds = image.getchannel("A").getbbox()
    if not alpha_bounds:
        return None
    cropped = image.crop(alpha_bounds)
    return cropped.size, hashlib.sha256(cropped.tobytes()).hexdigest()


def asset_relative(path: Path, asset_root: Path) -> str:
    try:
        return path.relative_to(asset_root).as_posix()
    except ValueError as error:
        raise ValueError(f"Asset path must be within {asset_root}: {path}") from error


def portable_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sync_components(config: dict, asset_root: Path) -> dict[tuple[tuple[int, int], str], str]:
    fingerprints = {}
    for component in config.get("components", []):
        source = project_path(component["source"])
        destination = project_path(component["asset"])
        if not source.is_file():
            raise FileNotFoundError(f"Missing component source: {source}")
        with Image.open(source) as image:
            fingerprint = alpha_fingerprint(image.convert("RGBA"))
        if fingerprint is None:
            raise ValueError(f"Component has no visible pixels: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        fingerprints[fingerprint] = asset_relative(destination, asset_root)
    return fingerprints


def write_layer_asset(layer, destination: Path) -> None:
    image = layer_image(layer)
    if image is None:
        raise ValueError(f"Layer has no bitmap: {layer.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def layer_content_image_and_bbox(layer, *, alpha_bounds_global: bool = False):
    """Return a trimmed RGBA image and the matching PSD-space content bbox."""

    image = layer.composite()
    if image is None:
        raise ValueError(f"Layer has no bitmap: {layer.name}")
    image = image.convert("RGBA")
    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise ValueError(f"Layer has no visible pixels: {layer.name}")
    left, top, right, bottom = (int(value) for value in layer.bbox)
    x1, y1, x2, y2 = alpha_bbox
    if alpha_bounds_global:
        # Transformed smart/pixel layers can composite onto the complete PSD canvas.
        # This is declared by the export configuration after visually checking the PSD.
        content_bbox = alpha_bbox
    elif image.size == (right - left, bottom - top):
        # Normal layers are composited in their local bounding-box coordinate system.
        content_bbox = (left + x1, top + y1, left + x2, top + y2)
    else:
        # Transformed smart/pixel layers can composite onto the complete PSD canvas.
        # Their alpha bounds are already in PSD coordinates; applying layer.bbox again
        # displaces keys and markers, which was the original export defect.
        content_bbox = alpha_bbox
    return image.crop(alpha_bbox), content_bbox


def scaled_rect_from_bbox(
    bbox, source_canvas: tuple[int, int], target_canvas: tuple[int, int]
) -> dict[str, int]:
    """Scale a PSD bbox by its edges to preserve shared pixel boundaries."""

    left, top, right, bottom = (int(value) for value in bbox)
    source_width, source_height = source_canvas
    target_width, target_height = target_canvas
    x1 = round(left * target_width / source_width)
    y1 = round(top * target_height / source_height)
    x2 = round(right * target_width / source_width)
    y2 = round(bottom * target_height / source_height)
    return {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}


def source_rect_from_bbox(bbox) -> dict[str, int]:
    """Return a JSON-friendly rectangle from a PSD bbox."""

    left, top, right, bottom = (int(value) for value in bbox)
    return {"x": left, "y": top, "width": right - left, "height": bottom - top}


def export_static_source(
    layer,
    index_path: list[int],
    source: dict,
    entries: list[dict],
    component_assets: dict,
    fallback_assets: dict,
    output_dir: Path,
    asset_root: Path,
    source_canvas: tuple[int, int],
    target_canvas: tuple[int, int],
    excluded_paths: set[tuple[int, ...]],
    ancestors_visible: bool = True,
) -> None:
    if not ancestors_visible or not layer.visible:
        # PSD 中隐藏的图层与隐藏组的内容都不属于运行时场景。
        return
    if tuple(index_path) in excluded_paths:
        return
    if layer.is_group():
        for index, child in enumerate(layer):
            export_static_source(
                child,
                [*index_path, index],
                source,
                entries,
                component_assets,
                fallback_assets,
                output_dir,
                asset_root,
                source_canvas,
                target_canvas,
                excluded_paths,
                ancestors_visible=True,
            )
        return

    if source.get("trim_transparent"):
        try:
            image, content_bbox = layer_content_image_and_bbox(
                layer, alpha_bounds_global=source.get("alpha_bounds_global", False)
            )
        except ValueError as error:
            if "no visible pixels" in str(error):
                return
            raise
    else:
        image = layer_image(layer)
        content_bbox = layer.bbox
    if image is None:
        return
    fingerprint = alpha_fingerprint(image)
    if fingerprint is None:
        return
    asset = component_assets.get(fingerprint) or fallback_assets.get(fingerprint)
    if asset is None:
        filename = f"psd_{fingerprint[1][:16]}.png"
        fallback_path = output_dir / filename
        image.save(fallback_path)
        asset = asset_relative(fallback_path, asset_root)
        fallback_assets[fingerprint] = asset

    collision_type = source.get("collision_type")
    entries.append(
        {
            "source_layer_indices": index_path,
            "asset": asset,
            "element_type": source["element_type"],
            "collision": {"type": collision_type} if collision_type else None,
            "source_psd_rect": source_rect_from_bbox(content_bbox),
            "rect": scaled_rect_from_bbox(content_bbox, source_canvas, target_canvas),
        }
    )


def annotate_layer_paths(psd, entries: list[dict]) -> None:
    """Attach readable layer labels after export without using them as identifiers."""

    for entry in entries:
        labels = []
        layer = psd
        for index in entry["source_layer_indices"]:
            layer = layer[index]
            labels.append(f"{index}_{safe_name(layer.name)}")
        entry["layer_path"] = labels


def export_layouts(
    psd,
    config: dict,
    asset_root: Path,
    source_canvas: tuple[int, int],
    target_canvas: tuple[int, int],
) -> list[dict]:
    """Export non-static scene layout records and their optional visual assets."""

    layouts = []
    layout_ids = set()
    for export in config.get("layout_exports", []):
        layout_id = export.get("id")
        if not isinstance(layout_id, str) or not layout_id:
            raise ValueError("Each layout export requires a non-empty string id")
        if layout_id in layout_ids:
            raise ValueError(f"Duplicate layout export id: {layout_id}")
        layout_ids.add(layout_id)

        layer_path = export["layer_path"]
        layer = layer_at(psd, layer_path)
        if export.get("source_psd_rect"):
            # 杂散像素会撑大 alpha 包围盒（如人物占位格周围的反走样碎点），
            # 视觉确认后允许配置直接声明 PSD 矩形。
            left, top, width, height = (int(v) for v in export["source_psd_rect"])
            bbox = (left, top, left + width, top + height)
        else:
            bbox = layer.bbox
        entry = {
            "id": layout_id,
            "element_type": export["element_type"],
            "source_layer_indices": layer_path,
            "source_psd_rect": source_rect_from_bbox(bbox),
            "rect": scaled_rect_from_bbox(bbox, source_canvas, target_canvas),
        }
        collision_type = export.get("collision_type")
        if collision_type:
            entry["collision"] = {"type": collision_type}
        explicit_rect = bool(export.get("source_psd_rect"))
        if asset_value := export.get("asset"):
            destination = project_path(asset_value)
            if export.get("trim_transparent") and not explicit_rect:
                image, bbox = layer_content_image_and_bbox(
                    layer, alpha_bounds_global=export.get("alpha_bounds_global", False)
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.save(destination)
                entry["source_psd_rect"] = source_rect_from_bbox(bbox)
                entry["rect"] = scaled_rect_from_bbox(bbox, source_canvas, target_canvas)
            else:
                write_layer_asset(layer, destination)
            entry["asset"] = asset_relative(destination, asset_root)
        elif export.get("trim_transparent") and not explicit_rect:
            _, bbox = layer_content_image_and_bbox(
                layer, alpha_bounds_global=export.get("alpha_bounds_global", False)
            )
            entry["source_psd_rect"] = source_rect_from_bbox(bbox)
            entry["rect"] = scaled_rect_from_bbox(bbox, source_canvas, target_canvas)
        annotate_layer_paths(psd, [entry])
        layouts.append(entry)
    return layouts


def clean_generated_assets(output_dir: Path) -> None:
    for pattern in ("scene_*.png", "psd_*.png"):
        for path in output_dir.glob(pattern):
            path.unlink()


def export_level(
    config_path: Path,
    *,
    psd_override: Path | None = None,
    output_override: Path | None = None,
    map_override: Path | None = None,
) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    asset_root = project_path(config.get("asset_root", "assets"))
    psd_path = project_path(str(psd_override)) if psd_override else project_path(config["source_psd"])
    output_dir = project_path(str(output_override)) if output_override else project_path(config["output_dir"])
    map_path = project_path(str(map_override)) if map_override else project_path(
        config.get("map_path", f"{config['output_dir']}/map.json")
    )
    target_canvas = tuple(config["target_canvas"])
    if len(target_canvas) != 2:
        raise ValueError("target_canvas must contain [width, height]")
    if not psd_path.is_file():
        raise FileNotFoundError(f"Missing PSD source: {psd_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    clean_generated_assets(output_dir)
    psd = PSDImage.open(psd_path)
    source_canvas = (psd.width, psd.height)
    component_assets = sync_components(config, asset_root)
    fallback_assets: dict = {}

    for export in config.get("asset_exports", []):
        write_layer_asset(layer_at(psd, export["layer_path"]), project_path(export["asset"]))

    layouts = export_layouts(psd, config, asset_root, source_canvas, target_canvas)

    entries: list[dict] = []
    for source in config["static_sources"]:
        root_path = source["layer_path"]
        excluded_paths = {
            (*root_path, *relative_path)
            for relative_path in source.get("exclude_relative_paths", [])
        }
        export_static_source(
            layer_at(psd, root_path),
            root_path,
            source,
            entries,
            component_assets,
            fallback_assets,
            output_dir,
            asset_root,
            source_canvas,
            target_canvas,
            excluded_paths,
        )
    annotate_layer_paths(psd, entries)

    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        json.dumps(
            {
                "source_psd": portable_path(psd_path),
                "source_canvas": {"width": psd.width, "height": psd.height},
                "target_canvas": {"width": target_canvas[0], "height": target_canvas[1]},
                "elements": entries,
                "layouts": layouts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    component_count = sum(entry["asset"] in component_assets.values() for entry in entries)
    print(
        f"Wrote {len(entries)} map elements and {len(layouts)} layouts using "
        f"{component_count} component references and {len(fallback_assets)} unique PSD fallback assets."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="JSON export config")
    parser.add_argument("--psd", type=Path, help="Override the config PSD source")
    parser.add_argument("--output-dir", type=Path, help="Override the generated asset directory")
    parser.add_argument("--map", type=Path, help="Override the generated map JSON path")
    args = parser.parse_args()
    export_level(
        args.config,
        psd_override=args.psd,
        output_override=args.output_dir,
        map_override=args.map,
    )


if __name__ == "__main__":
    main()
