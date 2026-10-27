# PSD Level Export Tools

`report_psd_layers.py` reports a PSD's indexed layer tree. `export_level_map.py` exports the selected static leaf layers into reusable runtime assets and a map JSON that `utils.ui_art` and `levels.level_factory` already understand.

## Inspect a PSD

```powershell
uv run python tools/report_psd_layers.py <source.psd> --output <layer-report.txt>
```

The report includes the complete numeric layer-index path, name, type, visibility and PSD bounds. Use the numeric paths in export configuration: names are only labels for people and may repeat or have legacy encoding.

## Export a map

```powershell
uv run python tools/export_level_map.py --config tools/level_export_configs/huoli.json
```

The config supplies the source PSD, generated resource directory, map JSON path, target canvas, component sources, independent asset exports, and static element categories. Override the three location inputs without editing a config when needed:

```powershell
uv run python tools/export_level_map.py --config <config.json> --psd <source.psd> --output-dir <asset-directory> --map <map.json>
```

All paths in configuration are relative to the repository root unless absolute. `asset` paths must remain inside `asset_root` (default `assets`) because they are runtime resource references.

## Config Shape

```json
{
  "source_psd": "_materials/files/v2/example.psd",
  "asset_root": "assets",
  "output_dir": "assets/images/levels/example",
  "map_path": "assets/images/levels/example/map.json",
  "target_canvas": [1280, 720],
  "components": [{"source": "_materials/component.png", "asset": "assets/images/gameplay/example/tile.png"}],
  "asset_exports": [{"layer_path": [1], "asset": "assets/images/levels/example/background.png"}],
  "layout_exports": [
    {"id": "example_door", "layer_path": [2], "element_type": "door", "asset": "assets/images/levels/example/door.png", "collision_type": "solid"},
    {"id": "example_spawn", "layer_path": [3], "element_type": "spawn"}
  ],
  "static_sources": [
    {"layer_path": [5], "element_type": "terrain_block", "collision_type": "solid"},
    {"layer_path": [6], "exclude_relative_paths": [[0]], "element_type": "decoration"}
  ]
}
```

`components` are copied into the formal asset tree and exact RGBA matches reuse them. Other non-transparent PSD leaves are alpha-cropped, content-hashed, and exported once as `psd_*.png`. Each map entry includes a readable `layer_path`, stable `source_layer_indices`, source bounds, scaled runtime bounds, semantic `element_type`, and optional collision type.

`layout_exports` describes non-static scene components such as doors, keys, levers, gates and spawn markers. They are exported into `map.json.layouts` with a stable `id`, PSD-derived runtime rectangle and optional asset. Gameplay code references that `id` through `layout_id`; it must not repeat `x`, `y`, `w`, `h` or `art_path`. This keeps PSD as the single source of scene layout while code owns behavior and relationships.

For a transformed static layer whose composite alpha bounds are already in full PSD-canvas coordinates, set `trim_transparent: true` and `alpha_bounds_global: true`. This must be based on an explicit visual check; it is not inferred from image dimensions because PSD export metadata is ambiguous for transformed layers.

Coordinates are scaled by converting both PSD edges before subtracting, preserving shared pixel boundaries between adjacent tiles. The exporter removes generated `psd_*.png` files in `output_dir` before writing new fallback assets; it does not remove explicit `asset_exports`.

`tools/level_export_configs/huoli.json` is the checked-in Huo Li example. It encodes the current layer selections and dynamic-resource exports, but running it is optional and will replace Huo Li's generated resources.

## Export result-screen character masks

`export_result_masks.py` derives per-character silhouettes for the level-result screen. Each export under `assets/images/ui/result/characters/` is a flattened screenshot of interface plus character, so the silhouette is recovered by compositing a character-free interface frame from the PSD and keeping the pixels where the export differs from it. The selection frames (`选中光框` / `选择光框`) are enabled because the exports were produced with them visible; the decoration (`装饰框`) layers are hidden because the exports do not contain them, and leaving them visible would bake the whole frame into the silhouette. Pixels that differ from the reference in *every* export while keeping an identical colour across all of them are stale interface elements baked into the artwork (for example a retired icon); they are removed from every silhouette.

```powershell
uv run python tools/export_result_masks.py --psd "assets/images/ui/result/结算ui.psd" --art-dir assets/images/ui/result/characters --out-dir assets/images/ui/result/characters/masks
```

Masks are written as RGBA PNGs whose alpha channel is the silhouette; `states/result_state.py` uses them to composite the character back on top of the action buttons. Re-run this tool after replacing `结算ui.psd` or any result-screen character art.
