-- In-memory metadata repair. No vanilla function replacements or recipe changes.
local entityName = "WinkDrillPress"
local prefix = "industry_02_"
local faces = { [268] = "E", [269] = "S", [270] = "W", [271] = "N" }
local faceTiles = { E = 268, S = 269, W = 270, N = 271 }
local targets = {}
for id in pairs(faces) do targets[prefix .. id] = true end

local function isOurEntity(props)
    return props:has(IsoFlagType.EntityScript)
        and props:get("EntityScriptName") == entityName
        and not props:has("CustomItem")
end

local function setMissing(props, key, value)
    if not props:has(key) then props:set(key, value) end
end

local function patchTiles(spriteManager)
    for id, facing in pairs(faces) do
        local sprite = spriteManager:getSprite(prefix .. id)
        if sprite then
            local props = sprite:getProperties()
            -- Yield to another mod or a future vanilla implementation of the tile.
            local foreignEntity = props:has(IsoFlagType.EntityScript) and not isOurEntity(props)
            local foreignMoveable = props:has("IsMoveAble") and not isOurEntity(props)
            if not foreignEntity and not foreignMoveable and not props:has("CustomItem") then
                -- Use existing tile-property dictionary values. Unknown strings are
                -- silently mapped to another value by B42's PropertyContainer.
                setMissing(props, "CustomName", "Press")
                setMissing(props, "GroupName", "Standing")
                setMissing(props, "Facing", facing)
                setMissing(props, "PickUpWeight", "400") -- 40 inventory weight
                setMissing(props, "PickUpTool", "Wrench")
                setMissing(props, "PlaceTool", "Wrench")
                for face, tile in pairs(faceTiles) do
                    setMissing(props, face .. "offset", tostring(tile - id))
                end
                props:set("EntityScriptName", entityName)
                -- Read back before marking the tile: fail closed on an unknown
                -- alias (e.g. a future engine change or script load failure).
                if props:get("EntityScriptName") == entityName then
                    props:set(IsoFlagType.EntityScript)
                    props:set("IsMoveAble", "")
                end
            end
        end
    end
end

local function repairObject(object)
    if not object or not object:getSprite() then return end
    if not targets[object:getSprite():getName()] then return end
    local props = object:getProperties()
    -- Never replace existing components, including another mod's workstation.
    if props and isOurEntity(props) and not object:hasComponents() then
        GameEntityFactory.CreateIsoEntityFromCellLoading(object)
    end
end

local function repairSquare(square)
    if not square then return end
    local objects = square:getObjects()
    for i = 0, objects:size() - 1 do repairObject(objects:get(i)) end
end

Events.OnLoadedTileDefinitions.Add(patchTiles)
Events.LoadGridsquare.Add(repairSquare)
Events.OnObjectAdded.Add(repairObject)
