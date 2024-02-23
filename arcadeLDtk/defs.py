
import os
from typing import Any, Optional
from typing import TypedDict
import arcade


def read_tilesets(sheet_path:str, tileset:dict) -> list[arcade.Texture]:
    assert tileset["relPath"], "tileset has no path"
    
    c_hei = tileset["__cHei"]
    c_wid = tileset["__cWid"]
    nb = c_hei * c_wid
    size = tileset["tileGridSize"]
    if tileset["padding"] > 0:
        raise NotImplementedError("padding in tileset is not implemeted")
    
    return arcade.load_spritesheet(sheet_path, size, size, c_wid, nb, margin=tileset["spacing"])


class TileRect(TypedDict):
    tilesetUid: int
    x: int
    y: int
    h: int
    w: int


class TileSet:
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

    path: str

    def __init__(self, path:str, ts:dict[str, Any]) -> None:
        self.path = os.path.join(path, ts["relPath"])

        self.set = read_tilesets(self.path, ts)
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

        self.identifier = ts["identifier"] # TODO: allow user to find tileset by identifier

        self.tags = ts["tags"]

    def __getitem__(self, id: int) -> arcade.Texture:
        return self.set[id]
    
    def get_texture(self, rect:TileRect) -> arcade.Texture:
        return arcade.load_texture(self.path, x=rect["x"], y=rect["y"], width=rect["w"], height=rect["h"])


class Enum:
    identifier: str
    tags: list[str]
    uid: int
    values: list[str]

    def __init__(self, dict:dict[str, Any]):
        self.identifier = dict["identifier"]
        self.tags = dict["tags"]
        self.uid = dict["uid"]
        self.values = [v["id"] for v in dict["values"]]


class EntityDefinition:
    uid: int
    identifier: str
    color: arcade.types.Color
    height: int
    width: int
    nine_slice_borders: Optional[tuple[int, int, int, int]]
    pivot_x: float
    pivot_y: float
    tileset_id: int
    tile_rect: Optional[TileRect]
    tile: Optional[arcade.Texture]
    tile_render_mode: str #TODO: may be use the list from the docs
    ui_tile_rect: Optional[TileRect]
    ui_tile: Optional[arcade.Texture]

    def __init__(self, ts:dict[str, Any], defs:"Defs") -> None:
        self.uid = ts["uid"]
        self.identifier = ts["identifier"]
        self.color = ts["color"]
        self.height = ts["height"]
        self.width = ts["width"]
        self.nine_slice_borders = ts["nineSliceBorders"]
        self.pivot_x = ts["pivotX"]
        self.pivot_y = ts["pivotY"]
        #TODO: read the arcade texture from the tileset
        self.tileset_id = ts["tilesetId"] 
        self.tile_rect = ts["tileRect"]
        self.tile = defs.get_texture(self.tile_rect) if self.tile_rect else None
        self.tile_render_mode = ts["tileRenderMode"]
        self.ui_tile_rect = ts["uiTileRect"]
        self.ui_tile = defs.get_texture(self.ui_tile_rect) if self.ui_tile_rect else None


class Defs:
    tilesets : dict[int, TileSet]
    """a dict from uid to tilesets"""
    enums: dict[int, Enum]
    entities: dict[int, EntityDefinition]
    def __init__(self, path:str, dict:dict[str, Any]) -> None:
        self.tilesets = { }
        for ts in dict["tilesets"]:
            if "identifier" in ts and ts["identifier"] == 'Internal_Icons':
                print("Internal_Icons are not implemeted")
                continue
            tileset = TileSet(path, ts)
            self.tilesets[tileset.uid] = tileset

        self.enums = {}
        for en in dict["enums"]:
            enum = Enum(en)
            self.enums[enum.uid] = enum
        
        self.entities = {}
        for ent in dict["entities"]:
            entity = EntityDefinition(ent, self)
            self.entities[entity.uid] = entity

    def get_texture(self, rect:TileRect) -> Optional[arcade.Texture]:
        if rect["tilesetUid"] in self.tilesets:
            return self.tilesets[rect["tilesetUid"]].get_texture(rect)

