"""Write a layer-tree report for any PSD supplied on the command line."""

from __future__ import annotations

import argparse
from pathlib import Path

from psd_tools import PSDImage


def readable_name(name: str) -> str:
    """Recover legacy GBK names decoded through a single-byte code page."""

    try:
        return name.encode("latin1").decode("gbk")
    except UnicodeError:
        return name


def write_layers(layers, depth: int, index_path: list[int], lines: list[str]) -> None:
    for index, layer in enumerate(layers):
        left, top, right, bottom = layer.bbox
        path = [*index_path, index]
        lines.append(
            f"{'  ' * depth}{path} | {readable_name(layer.name)} | {layer.kind} | "
            f"visible={layer.visible} | bounds=({left}, {top}, {right}, {bottom})"
        )
        if layer.is_group():
            write_layers(layer, depth + 1, path, lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psd", type=Path, help="PSD source file")
    parser.add_argument("--output", type=Path, required=True, help="UTF-8 report path")
    args = parser.parse_args()

    psd = PSDImage.open(args.psd)
    lines = [f"source={args.psd}", f"canvas={psd.width}x{psd.height}", ""]
    write_layers(psd, 0, [], lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
