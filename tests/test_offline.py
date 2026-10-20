"""Offline validation; requires Python 3.10+ and lupa (Lua 5.1).

Reads only the supplied game directory. Does not launch or initialize the game.
"""
import argparse
import json
from pathlib import Path
import re
import unittest
import zipfile
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "ProjectZomboidDrillPressFix/42"
parser = argparse.ArgumentParser()
parser.add_argument("--game-dir", type=Path, required=True)
args, rest = parser.parse_known_args()
GAME = args.game_dir


def read(relative):
    return (GAME / relative).read_text(encoding="utf-8-sig")


def tile_properties():
    text = read("media/newtiledefinitions.tiles.txt")
    result = {}
    for name, body in re.findall(r"// (\w+)\s+tile\s*\{([^}]+)\}", text):
        result[name] = dict(re.findall(r"^\s*(\w+) =([^\r\n]*)", body, re.M))
        result[name] = {k: v.strip() for k, v in result[name].items()}
    return result


class OfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tiles = tile_properties()

    def environment(self, missing_alias=False):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            callbacks = {}
            Events = setmetatable({}, {__index = function(t, k)
                local v = { Add = function(fn) callbacks[k] = fn end }
                rawset(t, k, v); return v
            end})
            IsoFlagType = setmetatable({}, {__index=function(t,k) return k end})
            IsoPropertyType = {FITS_BENEATH_COUNTERTOP='FitsBeneathCountertop'}
            IsoGridSquare = {ignoreBlockingSprites={add=function() end}}
            getCore = function() return {
                getGoodHighlitedColor=function() return {} end,
                getBadHighlitedColor=function() return {} end
            } end
            sprites = {}
            manager = { getSprite=function(self,name) return sprites[name] end }
            getSprite = function(name) return sprites[name] end
            function makeSprite(name, props)
                local p = { values=props }
                function p:has(k) return self.values[k] ~= nil end
                function p:get(k) return self.values[k] end
                function p:set(k,v)
                    if k=='EntityScriptName' and missingAlias then v='OtherEntity' end
                    self.values[k] = v or ''
                end
                local s = { getProperties=function() return p end,
                    getName=function() return name end,
                    getSpriteGrid=function() return nil end }
                sprites[name]=s
                return s
            end
            calls = 0
            GameEntityFactory = {CreateIsoEntityFromCellLoading=function(obj)
                assert(not obj:hasComponents()); calls=calls+1; obj.components=true
            end}
            function makeObject(sprite, components)
                local obj = { components=components }
                function obj:getSprite() return sprite end
                function obj:getProperties() return sprite:getProperties() end
                function obj:hasComponents() return self.components end
                return obj
            end
            function makeSquare(objects)
                return {getObjects=function() return {
                    size=function() return #objects end,
                    get=function(self,i) return objects[i+1] end
                } end}
            end
            instanceof=function(obj,t) return t=='Moveable' and obj.moveable end
            function instanceItem(fullType)
                local item = {moveable=true, fullType=fullType}
                function item:ReadFromWorldSprite(name)
                    self.sprite=name; return sprites[name] ~= nil
                end
                function item:setActualWeight(weight) self.weight=weight end
                return item
            end
        ''')
        lua.globals().missingAlias = missing_alias
        for name in [f"industry_02_{n}" for n in range(264, 272)]:
            lua.globals().makeSprite(name, lua.table_from(self.tiles[name]))
        lua.execute(read("media/lua/shared/Moveables/ISMoveableSpriteProps.lua"))
        lua.execute((MOD / "media/lua/shared/WinkDrillPressFix.lua").read_text())
        return lua

    def test_installed_vanilla_diagnosis(self):
        for n in range(268, 272):
            props = self.tiles[f"industry_02_{n}"]
            self.assertEqual(props["Surface"], "32")
            self.assertNotIn("IsMoveAble", props)
            self.assertNotIn("CustomItem", props)
        entities = GAME / "media/scripts/generated/entities"
        self.assertFalse(any(re.search(r"\bentity\s+StandingDrillPress\b", p.read_text())
                             for p in entities.rglob("*.txt")))

    def test_native_recipes_unchanged(self):
        recipes = read("media/scripts/generated/entities/blacksmith/craftRecipes/recipes_blacksmith_standingdrill.txt")
        self.assertEqual(re.findall(r"craftRecipe (\w+)", recipes), [
            "Drill_Steel_Ingot", "Drill_Iron_Ingot", "Drill_Steel_Block",
            "Drill_Iron_Block", "Drill_Steel_Chunk", "Drill_Iron_Chunk",
            "Drill_Draw_Plate", "Drill_Heading_Tool"])
        self.assertEqual(re.findall(r"SkillRequired = MetalWelding:(\d)", recipes), list("43322133"))
        self.assertEqual(recipes.count("NeedToBeLearn = true"), 2)
        self.assertEqual(recipes.count("Tags = StandingDrillPress"), 8)
        for p in (MOD / "media/scripts").rglob("*.txt"):
            self.assertNotIn("craftRecipe ", p.read_text())
        self.assertIn("Recipes = StandingDrillPress", (MOD / "media/scripts/wink_drill_press.txt").read_text())

    def test_property_values_exist_in_vanilla_alias_dictionary(self):
        # PropertyContainer maps unknown strings to value 0; catch that here.
        values = {}
        for props in self.tiles.values():
            for k,v in props.items(): values.setdefault(k,set()).add(v)
        # IsoWorld.SetCustomPropertyValues generates these rather than reading
        # them from the text tile definitions (verified in installed bytecode).
        for face in "NSEW": values[face + "offset"] = {str(i) for i in range(-96,97)}
        lua = self.environment()
        lua.execute("callbacks.OnLoadedTileDefinitions(manager)")
        for n in range(268,272):
            props = lua.globals().sprites[f"industry_02_{n}"].getProperties()["values"]
            for k,v in props.items():
                if k not in {"EntityScriptName", "EntityScript"}:
                    self.assertIn(v, values[k], (k,v))

    def test_vanilla_constructor_items_and_all_rotations(self):
        lua = self.environment()
        lua.execute('''
            assert(not ISMoveableSpriteProps.new('industry_02_268').isMoveable)
            callbacks.OnLoadedTileDefinitions(manager)
            for id=268,271 do
                local name='industry_02_'..id
                local p=ISMoveableSpriteProps.new(name)
                assert(p.isMoveable and p.type=='Object')
                assert(p.weight==40 and p.pickUpTool=='Wrench' and p.placeTool=='Wrench')
                assert(p.pickUpLevel==0 and not p.canBreak and p.surface==32)
                local item=p:instanceItem()
                assert(item.fullType=='Moveables.'..name and item.sprite==name and item.weight==40)
                local faces=p:getFaces()
                assert(faces.E=='industry_02_268' and faces.S=='industry_02_269')
                assert(faces.W=='industry_02_270' and faces.N=='industry_02_271')
            end
            assert(not ISMoveableSpriteProps.new('industry_02_264').isMoveable)
        ''')

    def test_existing_objects_idempotence_and_no_foreign_component_replacement(self):
        lua = self.environment()
        lua.execute('''
            callbacks.OnLoadedTileDefinitions(manager)
            callbacks.OnLoadedTileDefinitions(manager)
            local fresh=makeObject(sprites.industry_02_268,false)
            local existing=makeObject(sprites.industry_02_269,true)
            local unrelated=makeObject(sprites.industry_02_264,false)
            local square=makeSquare({fresh,existing,unrelated})
            callbacks.LoadGridsquare(square); callbacks.LoadGridsquare(square)
            callbacks.OnObjectAdded(fresh); callbacks.OnObjectAdded(nil)
            callbacks.LoadGridsquare(nil)
            assert(calls==1 and fresh.components and existing.components)
            assert(not unrelated.components)
        ''')

    def test_vanilla_tool_gate_for_pickup_and_placement(self):
        definitions = read("media/lua/shared/Moveables/ISMoveableDefinitions.lua")
        match = re.search(r'addToolDefinition\(\s*"Wrench",\s*\{([^}]+)\}', definitions)
        self.assertIsNotNone(match)
        items = re.findall(r'"([^"]+)"', match.group(1))
        self.assertEqual(items, ["Base.Wrench", "Base.PipeWrench"])
        lua = self.environment()
        lua.globals().wrenchItems = lua.table_from(items)
        lua.execute('''
            callbacks.OnLoadedTileDefinitions(manager)
            ISMoveableDefinitions = {getInstance=function() return {
                getToolDefinition=function(name)
                    assert(name=='Wrench'); return {items=wrenchItems}
                end
            } end}
            local inventory={held=nil}
            function inventory:getFirstTypeRecurse(name)
                if name==self.held then return name end
            end
            local player={isMovablesCheat=function() return false end,
                getInventory=function() return inventory end}
            local p=ISMoveableSpriteProps.new('industry_02_268')
            for _,mode in ipairs({'pickup','place'}) do
                inventory.held=nil; assert(not p:hasTool(player,mode))
                inventory.held='Base.Wrench'; assert(p:hasTool(player,mode))
                inventory.held='Base.PipeWrench'; assert(p:hasTool(player,mode))
                inventory.held='Base.Hammer'; assert(not p:hasTool(player,mode))
            end
        ''')

    def test_foreign_metadata_preserved(self):
        lua = self.environment()
        lua.execute('''
            local p=sprites.industry_02_268:getProperties()
            p:set('IsMoveAble',''); p:set('PickUpWeight','600')
            local q=sprites.industry_02_269:getProperties()
            q:set('EntityScript',''); q:set('EntityScriptName','OtherEntity')
            local r=sprites.industry_02_270:getProperties()
            r:set('CustomItem','OtherMod.Press')
            local s=sprites.industry_02_271:getProperties()
            s:set('PickUpLevel','5'); s:set('PickUpTool','Screwdriver')
            callbacks.OnLoadedTileDefinitions(manager)
            assert(p:get('PickUpWeight')=='600' and not p:has('EntityScript'))
            assert(q:get('EntityScriptName')=='OtherEntity' and not q:has('IsMoveAble'))
            assert(r:get('CustomItem')=='OtherMod.Press' and not r:has('EntityScript'))
            assert(s:get('PickUpLevel')=='5' and s:get('PickUpTool')=='Screwdriver')
        ''')

    def test_missing_entity_alias_fails_closed(self):
        lua = self.environment(missing_alias=True)
        lua.execute('''
            callbacks.OnLoadedTileDefinitions(manager)
            local p=sprites.industry_02_268:getProperties()
            assert(not p:has('IsMoveAble') and not p:has('EntityScript'))
        ''')

    def test_installed_engine_contracts(self):
        # Verify symbols in the actual installed class files, no initialization.
        with zipfile.ZipFile(GAME / "projectzomboid.jar") as z:
            contracts = {
                "zombie/entity/GameEntityFactory.class": [b"CreateIsoEntityFromCellLoading", b"TransferComponents", b"EntityScriptName"],
                "zombie/core/properties/PropertyContainer.class": [b"getIDFromPropertyValue",b"set",b"has"],
                "zombie/core/TilePropertyAliasMap.class": [b"generateEntityProperties", b"getAllGameEntities"],
                "zombie/Lua/LuaEventManager.class": [b"OnLoadedTileDefinitions",b"LoadGridsquare",b"OnObjectAdded"],
                "zombie/scripting/entity/components/crafting/CraftBenchScript.class": [b"recipes",b"FormatAndRegisterRecipeTagsQuery"],
                "zombie/iso/IsoWorld.class": [b"SetCustomPropertyValues",b"Noffset",b"Soffset",b"Woffset",b"Eoffset"],
            }
            for name, symbols in contracts.items():
                for symbol in symbols: self.assertIn(symbol,z.read(name))
        movement = read("media/lua/shared/Moveables/ISMoveableSpriteProps.lua")
        self.assertIn("GameEntityFactory.TransferComponents(_object, item)", movement)
        self.assertIn("GameEntityFactory.TransferComponents(_item, obj)", movement)

    def test_package_metadata_and_script_structure(self):
        info = (MOD / "mod.info").read_text()
        self.assertIn("id=WinkDrillPressFixB42",info)
        for p in (MOD / "media/scripts").rglob("*.txt"):
            text=p.read_text(); self.assertEqual(text.count("{"),text.count("}"))
        skin=(MOD / "media/scripts/xui/wink_drill_press_skin.txt").read_text()
        self.assertIn("LuaPanelClass = ISCraftBenchPanel",skin)
        self.assertIn("CraftBench",skin)
        self.assertEqual(json.loads((MOD / "media/lua/shared/Translate/EN/Moveables.json").read_text()),
                         {"Standing_Press":"Standing Drill Press"})


if __name__ == "__main__":
    unittest.main(argv=[__file__, *rest], verbosity=2)
