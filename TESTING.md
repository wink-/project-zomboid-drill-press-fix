# Validation and acceptance tests

## Offline checks

Requires Python 3.10+ and the `lupa` package with its Lua 5.1 backend. Install dependencies in an isolated environment if needed. From the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install lupa
.venv/Scripts/python tests/test_offline.py --game-dir "$GAME_DIR"
```

Set `$GAME_DIR` to your installed Project Zomboid directory. The test suite only reads that directory. It does not initialize Java game classes, launch the client/server, or access saves.

Checks exercise the mod's Lua hooks using mocks, with the **actual installed** `ISMoveableSpriteProps.lua` loaded into a Lua 5.1 interpreter. They verify item selection, weight, tool metadata, all four rotations, idempotent loaded-object repair, unrelated/foreign objects, missing-alias handling, existing property dictionary values, recipe requirements, package structure, and expected API/event symbols inside the installed JAR. Engine-generated rotation offset aliases are accounted for separately.

Mocks do not simulate the whole game: these checks do not prove native entity parsing, crafting UI behavior, pathfinding, physics, saving, network serialization or a successful in-game craft. Those need the manual tests below.

Build the installable archive with:

```powershell
python tools/package.py
```

The packaging script includes only the mod and user documentation, writes `dist/`, and prints the archive SHA-256. It excludes tests, private inspection material, game files, development dependencies and Git metadata.

## Manual acceptance checklist — user to run

Use Build 42.21. Back up the save outside the game, then test a disposable world or backup copy. Enable only this mod initially. Disable crafting/movement cheats for requirement checks.

1. **Baseline:** with the mod disabled, verify the reported machine is a standing drill press. The targeted tile IDs are `industry_02_268`–`271`, not the adjacent bandsaw `264`–`267` or decorative machinery elsewhere.
2. **Existing object:** enable the mod for the test save and reload. Approach a previously visited press. Its furniture tooltip should identify a Standing Drill Press in English. Other languages may display Standing Press.
3. **Missing tools:** try pickup with neither wrench nor pipe wrench anywhere in inventory/bags. It must fail and show the normal missing-tool indication. Repeat for placement after obtaining the furniture item.
4. **Pickup:** obtain a wrench or pipe wrench and sufficient carrying capacity for weight 40. Pick up the press using the normal furniture interface. Confirm one furniture item appears, the world object disappears, and no duplicate object/item remains.
5. **Placement and rotation:** place on an accessible empty floor square. Check all four orientations. Confirm blocked/occupied placement still fails normally. Rotate a placed press as well. Repeat pickup/place twice and inspect for duplication or errors.
6. **Existing workstation:** before pickup, right-click/use an original press and open its native crafting window. It should offer the eight listed recipes, with unavailable recipes filtered or disabled normally.
7. **Reinstalled workstation:** repeat that check after placement and after rotation. With Welding 1 and one IronChunk, craft Drill_Iron_Chunk; expect one PiercedIronChunk and consumption of one IronChunk.
8. **Skill gates:** at insufficient Welding level, verify ingot/block/steel recipes are unavailable. Raise skill normally or through a disposable debug setup, then turn crafting cheats off and retry.
9. **Ingredient and learning gates:** remove required ingredients and confirm craft fails. With sufficient skill but no learned recipe, Draw Plate and Heading Tool must remain unavailable; learn the proper vanilla recipes and retry with their listed ingredients.
10. **Power observation:** test with and without mains/generator power. This release mirrors the installed recipes, which define no electricity gate or consumption. Unexpected difference/error needs investigation; do not claim powered-machine simulation.
11. **Persistence:** save, quit and reload the test world. Recheck the original, moved and rotated presses, inventory furniture items, UI and crafting. Observe whether any errors mention `WinkDrillPress` or its UI style.
12. **Compatibility:** verify adjacent bandsaws, workbenches and other furniture have unchanged pickup behavior. Only then repeat on a backed-up save with the user's normal mod list. If another mod claims these tiles, this patch intentionally yields.
13. **Multiplayer (optional, unverified):** install the same package on server and clients. Repeat pickup/place/craft/persistence with two players, watching for duplicates, client/server disagreement and serialization errors.

Record game version, mod version, sprite/orientation, original versus moved object, observed error and the shortest reproduction. Do not publish personal save files or full logs without reviewing them for private information.

## Result recorded for 0.1.0

Offline suite: passed on the locally installed Build 42.21. The native Lua movement constructor is exercised, but item inventory/engine methods are mocked. No game was launched or stopped. All manual acceptance checks remain pending user testing.
