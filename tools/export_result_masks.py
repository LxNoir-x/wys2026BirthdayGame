"""Export per-character silhouette masks for the level-result screen.

The result art (``assets/images/ui/result/characters/<set>/<name>.png``) is a
already-composited screenshot: interface + character, with the character drawn
on top of the action buttons. The runtime needs to know which pixels belong to
the character so it can draw the buttons underneath the sleeve instead of over
it, which the previous brightness heuristic could not do for dark sleeves.

The silhouette is derived from the PSD: composite every interface layer (with
the button selection frames enabled, matching how the export was produced) and
keep the pixels where the exported art differs from that interface-only frame.
Character masks are stored as RGBA PNGs whose alpha channel is the silhouette.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from psd_tools import PSDImage

# 单通道差值超过该值即视为"角色改动了这里"。界面参考与立绘稿在角色以外的
# 区域逐像素一致（实测最大差 1），所以阈值取得低一些，尽量多收角色的边缘。
DEFAULT_THRESHOLD = 8
# 闭运算半径：只补掉轮廓上的小缺口，不让剪影整体外扩。
DEFAULT_CLOSE = 2
# 剪影外扩像素数。默认 0：立绘稿里角色之外就是按钮本身，外扩会把按钮边框
# 一起还原到角色上层。抗锯齿边本身与按钮底色的差值已足够大，会被直接保留。
DEFAULT_DILATE = 0
# 允许填补的封闭洞面积上限（px）：只填角色内部的小洞。更大的封闭区域通常是
# 角色轮廓在画布边缘围出的整片背景（或按钮区），把它算进剪影会让剪影不"紧"。
DEFAULT_HOLE_MAX_AREA = 5000
# 判定"所有立绘稿在该像素颜色完全一致"的容差（RGB 通道最大差）。用于识别被烘进
# 每张立绘稿、但界面参考里已不存在的废弃界面元素。
DEFAULT_ART_ONLY_UI_TOLERANCE = 4
# 剔除废弃界面元素时向外多扩的像素数：这类元素的抗锯齿边缘在各立绘稿间可能有
# ±几的色差而漏判，外扩一点确保擦干净。
DEFAULT_ART_ONLY_UI_EXPAND = 2
# 按钮组里默认隐藏、但导出立绘稿时是打开的界面层。
INTERFACE_SUB_LAYERS = ("选中光框", "选择光框")
# 装饰框（红框）是叠加在立绘稿之外的独立装饰，导出立绘稿时不包含它；界面参考
# 也必须同样隐藏，否则整块框会被当成角色写进剪影，回贴时留下一块硬边矩形痕迹。
DECORATION_LAYERS = ("装饰框", "装饰框 拷贝")


def build_interface_reference(psd) -> np.ndarray:
    """合成只含界面的参考图（RGB，与导出素材同分辨率）。"""

    for layer in psd:
        if layer.name in DECORATION_LAYERS:
            layer.visible = False
        if layer.is_group():
            for child in layer.descendants():
                if child.name in INTERFACE_SUB_LAYERS:
                    child.visible = True
    return np.asarray(psd.composite(force=True).convert("RGB")).astype(np.int16)


def find_layer(psd, name: str):
    for layer in psd:
        if layer.name == name:
            return layer
        if layer.is_group():
            for child in layer.descendants():
                if child.name == name:
                    return child
    return None


def drop_text_components(mask: np.ndarray, text_bbox) -> np.ndarray:
    """去掉完全落在关卡标题区内的连通域。

    每关立绘稿里的"…行动完成"标题与 PSD 当前显示的标题不同名，做差会把它
    整段识别成角色。关卡标题是独立的小连通域，整体落在标题框内即可安全剔除。
    """

    if text_bbox is None:
        return mask
    left, top, right, bottom = text_bbox
    total, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), 8
    )
    for index in range(1, total):
        x = stats[index, cv2.CC_STAT_LEFT]
        y = stats[index, cv2.CC_STAT_TOP]
        width = stats[index, cv2.CC_STAT_WIDTH]
        height = stats[index, cv2.CC_STAT_HEIGHT]
        if x >= left and y >= top and x + width <= right and y + height <= bottom:
            mask[labels == index] = False
    return mask


def fill_enclosed_holes(mask: np.ndarray, max_area: int = DEFAULT_HOLE_MAX_AREA) -> np.ndarray:
    """填掉被角色包围的小洞（角色内部与按钮同色的像素会漏判）。

    只填面积不超过 ``max_area`` 的封闭洞：更大的封闭区域通常不是角色内部的小
    洞，而是角色轮廓在画布边缘围出的整片背景/按钮区，一起写进剪影会让回贴把
    整块背景盖回底图。传 0 表示不限制（全部填）。
    """

    # 先补一圈"背景"，保证 floodFill 的种子一定落在背景上。
    padded = np.pad((~mask).astype(np.uint8), 1, constant_values=1)
    flood = padded.copy()
    flood_mask = np.zeros((padded.shape[0] + 2, padded.shape[1] + 2), np.uint8)
    cv2.floodFill(flood, flood_mask, (0, 0), 2)
    holes = flood[1:-1, 1:-1] == 1
    if max_area > 0:
        total, labels, stats, _ = cv2.connectedComponentsWithStats(
            holes.astype(np.uint8), 8
        )
        keep = np.zeros_like(holes)
        for index in range(1, total):
            if stats[index, cv2.CC_STAT_AREA] <= max_area:
                keep[labels == index] = True
        holes = keep
    return mask | holes


def close_gaps(mask: np.ndarray, radius: int) -> np.ndarray:
    """闭运算：补掉轮廓上的小缺口，不改变剪影的整体大小。"""

    if radius <= 0:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1,) * 2)
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel) > 0


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1,) * 2)
    return cv2.dilate(mask.astype(np.uint8), kernel) > 0


def iter_art_sets(art_dir: Path, out_dir: Path):
    """依次产出每套立绘的目录与其 PNG 列表，跳过剪影输出目录自身。"""

    out_resolved = out_dir.resolve()
    for set_dir in sorted(path for path in art_dir.iterdir() if path.is_dir()):
        if set_dir.resolve() == out_resolved:
            continue
        yield set_dir, sorted(set_dir.glob("*.png"))


def find_art_only_ui(sets, reference, args):
    """找出被烘进所有立绘稿、但界面参考里已不存在的非角色像素。

    典型例子是从工程里删掉、却仍留在每张立绘稿上的界面小元素（如已退役的主播
    模式音量图标）：这类像素在每张立绘稿上都与界面参考不同，且各立绘稿之间颜色
    完全一致。角色在不同立绘稿上的位置、形状、颜色都不同，因此不会被误判。
    """

    diff_all = None
    low = None
    high = None
    for _set_dir, paths in sets:
        for path in paths:
            art = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
            if art.shape != reference.shape:
                raise ValueError(
                    f"{path} 尺寸 {art.shape} 与界面参考 {reference.shape} 不一致"
                )
            diff = np.abs(art - reference).max(axis=2) > args.threshold
            diff_all = diff if diff_all is None else (diff_all & diff)
            low = art if low is None else np.minimum(low, art)
            high = art if high is None else np.maximum(high, art)
    if diff_all is None:
        return None
    art_only = diff_all & ((high - low).max(axis=2) <= args.art_only_ui_tolerance)
    # 外扩一点盖住这类元素的抗锯齿边缘，避免残留零碎像素。
    return dilate(art_only, DEFAULT_ART_ONLY_UI_EXPAND)


def export_set(paths, target_dir: Path, reference, text_bbox, args, art_only_ui) -> int:
    """为一个立绘目录下的每张图导出剪影。"""

    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in paths:
        art = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
        if art.shape != reference.shape:
            raise ValueError(f"{path} 尺寸 {art.shape} 与界面参考 {reference.shape} 不一致")
        mask = np.abs(art - reference).max(axis=2) > args.threshold
        mask = drop_text_components(mask, text_bbox)
        mask = close_gaps(mask, args.close)
        mask = fill_enclosed_holes(mask, args.hole_max_area)
        mask = dilate(mask, args.dilate)
        if art_only_ui is not None:
            # 最后一步剔除烘进立绘稿的废弃界面元素，避免被当成角色。
            mask = mask & ~art_only_ui

        rgba = np.zeros((*mask.shape, 4), np.uint8)
        rgba[..., :3] = 255
        rgba[..., 3] = np.where(mask, 255, 0)
        Image.fromarray(rgba, "RGBA").save(target_dir / path.name)
        count += 1
        print(
            f"  {target_dir.name}/{path.name}: 剪影 {int(mask.sum())} px"
        )
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--psd", type=Path, required=True, help="结算ui.psd 路径")
    parser.add_argument("--art-dir", type=Path, required=True, help="立绘稿根目录")
    parser.add_argument("--out-dir", type=Path, required=True, help="剪影输出根目录")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--close", type=int, default=DEFAULT_CLOSE)
    parser.add_argument("--dilate", type=int, default=DEFAULT_DILATE)
    parser.add_argument("--hole-max-area", type=int, default=DEFAULT_HOLE_MAX_AREA)
    parser.add_argument(
        "--art-only-ui-tolerance",
        type=int,
        default=DEFAULT_ART_ONLY_UI_TOLERANCE,
    )
    args = parser.parse_args()

    psd = PSDImage.open(args.psd)
    reference = build_interface_reference(psd)

    text_layer = find_layer(psd, "文案")
    text_bbox = None
    if text_layer is not None:
        left, top, right, bottom = text_layer.bbox
        pad = 8
        text_bbox = (left - pad, top - pad, right + pad, bottom + pad)
    print(f"界面参考 {reference.shape[1]}x{reference.shape[0]}，标题区 {text_bbox}")

    sets = list(iter_art_sets(args.art_dir, args.out_dir))
    art_only_ui = find_art_only_ui(sets, reference, args)
    if art_only_ui is not None:
        print(f"立绘稿共有的废弃界面元素 {int(art_only_ui.sum())} px，已从剪影中剔除")

    total = 0
    for set_dir, paths in sets:
        print(f"[{set_dir.name}]")
        total += export_set(
            paths,
            args.out_dir / set_dir.name,
            reference,
            text_bbox,
            args,
            art_only_ui,
        )
    print(f"完成，共导出 {total} 张剪影到 {args.out_dir}")


if __name__ == "__main__":
    main()
