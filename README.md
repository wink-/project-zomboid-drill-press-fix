# Drill Press Fix B42

A separate Project Zomboid mod that reconnects the standing drill press to the game's existing crafting system and makes it movable.

**Version 0.1.0 — experimental, offline validated against Build 42.21 (Steam build 25485521). In-game acceptance testing is still required.** Compatibility is deliberately limited to 42.21 until newer versions are checked. No game was launched during development.

## Install

1. Close Project Zomboid and any dedicated server.
2. Download `ProjectZomboidDrillPressFix-0.1.0.zip` from [Releases](https://github.com/wink-/project-zomboid-drill-press-fix/releases).
3. Extract it. Copy the **ProjectZomboidDrillPressFix** folder into your user `Zomboid/mods` directory. The result must contain `ProjectZomboidDrillPressFix/42/mod.info` and `ProjectZomboidDrillPressFix/common/`.
4. Enable **Drill Press Fix B42**, mod ID `WinkDrillPressFixB42`. For an existing save, enable it through that save's mod selection as well.
5. Follow [TESTING.md](TESTING.md) on a disposable world or a backup copy first.

Do not extract into the game's installation or overwrite another mod directory. This is a local mod package, not a Steam Workshop upload. Multiplayer is unverified; both server and clients would need the same package.

## Changed behavior

- Only the four standing drill-press sprites `industry_02_268` (east), `269` (south), `270` (west), and `271` (north) are targeted.
- The normal furniture pickup/place/rotate interface recognizes the machine. Pickup and placement require a **wrench or pipe wrench** through the vanilla `Wrench` tool definition. Inventory weight is **40**, subject to normal carry and placement checks.
- A native `CraftBench` selects the game's `StandingDrillPress` recipe tag. Right-click/use the placed machine to open the native crafting window.
- Existing world presses gain components as their squares load, provided they do not already have components. Newly placed presses use the game's own component creation/transfer path.
- No vanilla functions, items, recipes, textures, collision flags, or placement checks are replaced. Other equipment, including the adjacent bandsaw tiles, is untouched.

Vanilla 42.21 has no drill-press movement values. The 40 weight and wrench requirement are explicit mod choices, not recovered developer specifications. There is no added pickup skill or random break chance. Existing tile-specific tool/skill values are retained if another patch supplies them without claiming the tile as its own moveable/entity.

## Existing recipes and requirements

The mod exposes these **existing** recipes without changing them:

| Recipe | Ingredient → output | Welding level |
| --- | --- | --- |
| Drill_Steel_Ingot | SteelIngot → PiercedSteelIngot | 4 |
| Drill_Iron_Ingot | IronIngot → PiercedIronIngot | 3 |
| Drill_Steel_Block | SteelBlock → PiercedSteelBlock | 3 |
| Drill_Iron_Block | IronBlock → PiercedIronBlock | 2 |
| Drill_Steel_Chunk | SteelChunk → PiercedSteelChunk | 2 |
| Drill_Iron_Chunk | IronChunk → PiercedIronChunk | 1 |
| Drill_Draw_Plate | SteelBarQuarter → DrawPlate | 3 + learned recipe |
| Drill_Heading_Tool | item tagged `base:barstockquarter` → HeadingTool | 3 + learned recipe |

The internal skill name is `MetalWelding`. The two learned recipes can be granted by the vanilla Welder profession or learned through the applicable vanilla smithing literature. All quantities, durations, XP, learning, ingredient, and skill checks remain with vanilla. The first six recipes specify the vanilla `Welding` timed action, which this mod also leaves unchanged.

**Power ambiguity:** these eight installed recipes specify no electrical power input or electricity check; the corresponding workstation entity is absent. This mod preserves that exact recipe behavior and therefore adds no power requirement or generator load. It does not disable a vanilla power check. A stricter electrically powered implementation would require a separate decision about supply rules and consumption; it is outside this repair. Likewise, no additional crafting-tool requirement is invented where the installed recipes have none.

## How the repair works

The shared Lua hook adds missing metadata in memory after tile definitions load. It uses existing property dictionary values (`Standing` + `Press`), translated in English to **Standing Drill Press**. The mod-owned `Base.WinkDrillPress` entity and `ES_WinkDrillPress` UI style use the standard `CraftBench`/`ISCraftBenchPanel` flow. The incomplete vanilla style targets `CraftLogic`, so a separate style explicitly binds the correct component.

`LoadGridsquare` and `OnObjectAdded` attach the entity only to the exact targeted objects that still lack components. The vanilla movement code transfers components from world object to furniture item and back. No per-tick scan, save migration script, admin command, new recipe, or custom furniture item is needed. The carried types are the vanilla dynamic `Moveables.industry_02_268` through `271`.

If another mod or future vanilla data already marks a tile as movable, supplies a custom item, or assigns a different entity, this patch yields for that tile. Load order still matters if another mod changes the same tiles after this hook. That combination needs user testing.

## Removal and save behavior

Development and packaging never edit game files or save files. During play, normal game saves can persist the newly attached entity components. Disabling the mod restores the original tile metadata on restart, but does not actively remove saved components. Keep your pre-test backup if you need a complete rollback. Move any press to its intended location before disabling the mod; it may lose furniture/workstation behavior without the patch. Removing a mod from an already modified save is not a tested rollback mechanism.

## Validation and development

See [TESTING.md](TESTING.md) for offline commands, runtime steps, and explicit limits, [docs/INVESTIGATION.md](docs/INVESTIGATION.md) for installed-code findings, and [CHANGELOG.md](CHANGELOG.md) for release changes.

No license has been selected. No license grant is supplied by this repository. Game assets and code remain with their respective owners; the download contains only original mod files and documentation.
