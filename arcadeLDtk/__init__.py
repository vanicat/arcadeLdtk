import json
import os
from typing import Any, Literal, Optional

from attr import dataclass
import arcade

def read_tilesets(path:str, tileset:dict) -> list[arcade.Texture]:
    assert tileset["relPath"], "tileset has no path"
    
    sheet_path = os.path.join(tileset["relPath"], path)
    c_hei = tileset["__cHei"]
    c_wid = tileset["__cWid"]
    nb = c_hei * c_wid
    size = tileset["tileGridSize"]
    if tileset["padding"] > 0:
        raise NotImplementedError("padding in tileset is not implemeted")
    
    return arcade.load_spritesheet(sheet_path, size, size, c_wid, nb, margin=tileset["spacing"])

class TileSets:
    """Representation of a ldtk tileset"""

    set:list[arcade.Texture]
    """the list of texture read from the tileset"""

    identifier:str
    """User defined unique identifier"""
    
    uid:int
    """Unique Intidentifier"""

    custom_data:dict[int, list[str]]
    """custom data for tile"""

    source_enum_id: Optional[int]

    enum_tag:dict[str, list[int]]
    "dict from tag to tagged texture id"

    tags:list[str]

    def __init__(self, path:str, ts:dict) -> None:
        self.set = read_tilesets(path, ts)
        self.tag_source_enum_uid = ts["tagsSourceEnumUid"]
        self.uid = ts["uid"]

        self.custom_data = {}
        for data in ts["customData"]:
            li = self.custom_data.setdefault(data["tileId"], [])
            li.append(data["data"])

        if ts["embedAtlas"] is not None:
            raise NotImplementedError("embedAtlas is not implemented")

        self.source_enum_id = ts["tagsSourceEnumUid"]
        self.enum_tag = { obj["enumValueId"]: obj["tileIds"] for obj in ts["enumTags"]}       

        self.identifier = ts["identifier"]

        self.tags = ts["tags"]


    def __getitem__(self, id:int) -> arcade.Texture:
        return self.set[id]


class Defs:
    tilesets : dict[int, TileSets]
    """a dict from uid to tilesets"""
    def __init__(self, path:str, dict:dict[str, Any]) -> None:
        self.tilesets = { }
        for ts in dict["tilesets"]:
            tileset = TileSets(path, ts)
            self.tilesets[tileset.uid] = tileset


def read_field_instances(*args):
    raise NotImplementedError("cannot read field instance yet")


class EntityInstance:
    def __init__(self, *args):
        raise NotImplementedError("Entity not implemeted yet")
    
class TileInstance:
    alpha: float
    flip_x: bool
    flip_y: bool
    flip_both: bool
    position: tuple[int, int]
    texture: arcade.Texture

    def __init__(self, dict:dict[str, Any], texture:TileSets):
        self.alpha = dict["a"]
        self.flip_x = dict["f"] == 1
        self.flip_y = dict["f"] == 2
        self.flip_both = dict["f"] == 3
        x, y = dict["px"]
        self.position = (x, y)
        self.texture = texture[dict["t"]]

class LayerInstance:
    c_height: int
    """Grid-based height"""
    c_width: int
    """Grid-based width"""
    grid_size: int
    """Grid size"""
    identifier: str 
    """Layer definition identifier"""
    opacity: float
    """Layer opacity as Float [0-1]"""
    px_total_offset_x: int
    """Total layer X pixel offset, including both instance and definition offsets."""
    px_total_offset_y: int
    """Total layer Y pixel offset, including both instance and definition offsets."""
    tileset: Optional[TileSets]
    """The corresponding Tileset, if any."""
    type: Literal["IntGrid"] | Literal["Entities"] | Literal["Tiles"] | Literal["AutoLayer"] 
    """Layer type (possible values: IntGrid, Entities, Tiles or AutoLayer)"""
    auto_layer_tiles: Optional[list[TileInstance]]
    """An array containing all tiles generated by Auto-layer rules.
The array is already sorted in display order
(ie. 1st tile is beneath 2nd, which is beneath 3rd etc.).

Note: if multiple tiles are stacked in the same cell as the result of different rules,
all tiles behind opaque ones will be discarded.
"""
    entity_instances: Optional[list[EntityInstance]]
    grid_tiles: Optional[list[TileInstance]]
    iid: str 
    """Unique layer instance identifier"""
    int_grid_csv: Optional[list[int]]
    """A list of all values in the IntGrid layer, stored in CSV format (Comma Separated Values).
Order is from left to right, and top to bottom (ie. first row from left to right, followed by second row, etc).
0 means "empty cell" and IntGrid values start at 1.
The array size is c_width x c_height cells."""
    layer_def_uid: int
    """Reference the Layer definition UID"""
    level_id: int
    """Reference to the UID of the level containing this layer instance"""
    override_tileset_uid: Optional[int]
    """This layer can use another tileset by overriding the tileset UID here."""
    px_offset_x: int
    """X offset in pixels to render this layer, usually 0
(IMPORTANT: this should be added to the LayerDef optional offset, so you should probably prefer using 
px_total_offset_x which contains the total offset value)"""
    px_offset_y: int
    """Y offset in pixels to render this layer, usually 0
(IMPORTANT: this should be added to the LayerDef optional offset, so you should probably prefer using 
px_total_offset_y which contains the total offset value)"""
    visible: bool
    """Layer instance visibility"""
        

    def __init__(self, dict:dict[str, Any], defs:Defs):
        self.c_height = dict["__cHei"]
        self.c_width = dict["__cWid"]
        self.grid_size = dict["__gridSize"]
        self.identifier = dict["__identifier"]
        self.opacity = dict["__opacity"]
        self.px_total_offset_x = dict["__pxTotalOffsetX"]
        self.px_total_offset_y = dict["__pxTotalOffsetY"]
        
        tileset_uid = dict["__tilesetDefUid"]
        self.tileset = defs.tilesets[tileset_uid]

        self.type = dict["__type"]
        self.auto_layer_tiles = [TileInstance(t, self.tileset) for t in dict["autoLayerTiles"]]
        if dict["entityInstances"]:
            raise NotImplementedError("entity Instance not implemeted yet")
        self.entity_instances = [EntityInstance(e) for e in dict["entityInstances"]]
        self.grid_tiles = self.auto_layer_tiles = [TileInstance(t, self.tileset) for t in dict["autoLayerTiles"]]
        self.int_grid_csv = dict["intGridCsv"]

        self.iid = dict["iid"]
        self.layer_def_uid = dict["layerDefUid"]
        self.level_id = dict["levelId"]
        self.override_tileset_uid = dict["overrideTilesetUid"]
        self.px_offset_x = dict["pxOffsetX"]
        self.px_offset_y = dict["pxOffsetY"]
        self.visible = dict["visible"]

class Level:
    bg_color: arcade.types.Color
    
    bg_pos: Optional[dict[str, Any]]
    """TODO: convert to something arcade use"""

    #TODO: __neighbours

    bg_texture: Optional[arcade.Texture]

    #TODO: fieldInstances

    identifier: str
    iid: str
    uid: int

    height: int
    width: int
    world_depth: int
    world_x: int
    world_y: int

    def __init__(self, level:dict, defs:Defs) -> None:
        self.level = level

        if level["externalRelPath"] is not None:
            raise NotImplementedError("Save leves separately is not implemeted")
        
        self.bg_color = arcade.types.Color.from_hex_string(level["__bgColor"])

        self.bg_pos = level["__bgPos"]
         
        if level["bgRelPath"] is None:
            self.bg_texture = None
        else:
            self.bg_texture = arcade.load_texture(level["bg_rel_path"])

        # in true, not implemeted
        self.field_instances = [read_field_instances(f) for f in level["fieldInstances"]]

        self.identifier = level["identifier"]
        self.iid = level["iid"]
        self.uid = level["uid"]

        # TODO
        self.layers = [LayerInstance(l, defs) for l in level["layerInstances"]]

        self.height = level["pxHei"]
        self.width = level["pxWid"]
        self.world_depth = level["worldDepth"]

        self.world_x = level["worldX"]
        self.world_y = level["worldY"]

class Instance:
    pass





class LDtk:
    bg_color: arcade.types.Color
    defs: Defs
    iid: str
    json_version: str
    levels: list[Level] | dict[tuple[int, int], Level]
    toc: dict[str, list[Instance]]
    world_grid_height: Optional[int]
    world_grid_widtht: Optional[int]
    world_layout: Optional[Literal["Free"] | Literal["GridVania"] | Literal["LinearHorizontal"] | Literal["LinearVertical"]]
    world: None

    def __init__(self, path:str, dict:dict[str, Any]) -> None:
        self.bg_color = arcade.types.Color.from_hex_string(dict["bgColor"])
        self.defs = Defs(path, dict["defs"])

        if dict["externalLevels"]:
            raise NotImplementedError("external levels are not implemented")
        
        self.iid = dict["iid"]
        self.json_version = dict["jsonVersion"]
        self.levels = [Level(l, self.defs) for l in dict["levels"]]
        
        if dict["toc"]:
            raise NotImplementedError("toc is not implemented")
        
        self.toc = {}

        self.world_grid_height = dict["worldGridHeight"]
        self.world_grid_width = dict["worldGridWidth"]
        self.world_layout = dict["worldLayout"]

        if dict["worlds"]:
            raise NotImplementedError("multi world is not implemented yet")
        
        self.world = None

def read_LDtk(path):
    directory = os.path.dirname(path)

    with(open(path)) as f:
        dict = json.load(f)
        return LDtk(directory, dict)