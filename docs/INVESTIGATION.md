# Installed-code findings

Inspected Build **42.21**, Steam build **25485521**, on 2026-10-20. Version was read from the installed `zombie/core/Core.class` game-version initializer; the Steam build ID came from the installation manifest. No vanilla source, binary, texture or extracted screenshot is distributed here.

## Tile identity

The installed `media/newtiledefinitions.tiles.txt` entries for `industry_02_268`–`271` contain `BlocksPlacement`, `MaterialType=Metal`, `Surface=32` and `solidtrans`. They do not contain `CustomName`, `Facing`, `IsMoveAble`, pickup/placement tools, pickup weight or `CustomItem`.

Private visual inspection of the installed `Tiles2x.pack` sprites established that these four sprites are the standing drill press. Their orientations follow the adjacent bandsaw: 268 east, 269 south, 270 west, 271 north. Adjacent `264`–`267` are bandsaws, not targets.

There is no dedicated drill-press inventory item in the installed generated item definitions. The game's `InventoryItemFactory` supports dynamic `Moveables.<sprite>` identifiers through `Moveables.Moveable`, so this repair needs no new item definition or duplicate sprite asset.

## Missing workstation link

`media/scripts/generated/entities/blacksmith/craftRecipes/recipes_blacksmith_standingdrill.txt` defines eight recipes tagged `StandingDrillPress`. No standing-drill-press entity is defined in the installed scripts. `media/scripts/xui/defaultskin/x_entity_blacksmithfurnace.txt` contains `ES_StandingDrillPress`, but its component style targets `CraftLogic`. The neighboring `entity_metalbandsaw.txt` and `entity_keyduplicator.txt` demonstrate the installed `CraftBench` tag-query pattern.

The fix uses an original, separately named `Base.WinkDrillPress` entity and matching `CraftBench` style. It preserves every installed recipe, including time, ingredients, outputs, skill levels and two learned-recipe requirements. The installed recipe file supplies no electricity input, power check or crafting-tool input. No authoritative power consumption or extra-tool policy can be recovered from this missing entity; see the explicit release limitation in the README.

## Verified engine integration contracts

Installed classes were inspected privately without starting the client or server:

- `IsoWorld` runs `OnLoadedTileDefinitions(spriteManager)` after script post-tile processing. It generates `Noffset`, `Soffset`, `Woffset`, `Eoffset` property values from -96 through 96.
- `TilePropertyAliasMap` registers names of all game entity scripts for `EntityScriptName`. Unknown property values otherwise silently map to value zero, so the patch uses known vanilla name/tool/weight/facing values and reads back its entity name before marking tiles.
- `GameEntityFactory.CreateIsoEntityFromCellLoading` resolves the `EntityScript` flag and `EntityScriptName` metadata, creates the script's components, and refuses a target that already has components.
- `CraftBenchScript` accepts `Recipes` and uses it as a native recipe-tag query.
- `ISMoveableSpriteProps` reads the patched movement metadata; pickup calls `TransferComponents(worldObject, item)`, and placement calls component creation if necessary followed by `TransferComponents(item, worldObject)`.
- `ISEntityUI` requires a style for the actual component type. The mod explicitly maps `CraftBench` to `ISCraftBenchPanel`.
- The `LoadGridsquare` and `OnObjectAdded` hooks repair exact matching objects that lack components, including previously saved map objects. No event replaces components on a functioning workstation.

The release is intentionally limited to the inspected version. Static inspection and mock-based offline validation are not runtime certification.
