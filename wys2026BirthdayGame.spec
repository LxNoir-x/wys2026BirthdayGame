# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
assets_root = project_root / "assets"

# 仅用于制作、运行时不需要随包分发的资源。
EXCLUDED_ASSET_SUFFIXES = {".psd"}
# 美术/校准比对用的参考图；运行时只按代码内写死的坐标绘制，不加载这些素材。
EXCLUDED_ASSET_NAME_PARTS = ("_expect",)
EXCLUDED_ASSET_NAMES = {
    "11_【黑流树海】主界面曲变奏_误入奇境.ogg",
}


def asset_datas():
    """展开 assets 目录，跳过 PSD 源文件、参考图与已停用的音频。"""

    datas = []
    for path in sorted(assets_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in EXCLUDED_ASSET_SUFFIXES:
            continue
        if any(part in path.name for part in EXCLUDED_ASSET_NAME_PARTS):
            continue
        if path.name in EXCLUDED_ASSET_NAMES:
            continue
        datas.append((str(path), str(path.parent.relative_to(project_root))))
    return datas


a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=asset_datas(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="wys2026BirthdayGame",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(project_root / "assets" / "images" / "app_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=False,
    name="wys2026BirthdayGame",
)
