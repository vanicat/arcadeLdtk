
import os
from typing import Any, Optional
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

    def __init__(self, path:str, ts:dict[str, Any]) -> None:
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


class Defs:
    tilesets : dict[int, TileSet]
    """a dict from uid to tilesets"""
    enums: dict[int, Enum]
    def __init__(self, path:str, dict:dict[str, Any]) -> None:
        self.tilesets = { }
        for ts in dict["tilesets"]:
            tileset = TileSet(path, ts)
            self.tilesets[tileset.uid] = tileset
        self.enums = {}
        for en in dict["enums"]:
            enum = Enum(en)
            self.enums[enum.uid] = enum

