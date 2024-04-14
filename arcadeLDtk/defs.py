
from dataclasses import dataclass
import os
from typing import Any, Optional, Self
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


@dataclass(slots=True, frozen=True, kw_only=True)
class TileSet:
    """Representation of a ldtk tileset"""

    set:list[arcade.Texture]
    """the list of texture read from the tileset"""

    identifier:str
    """User defined unique identifier"""
    
    uid:int
    """Unique Intidentifier"""

    tag_source_enum_uid: Optional[int]

    custom_data:dict[int, list[str]]
    """custom data for tile"""

    source_enum_id: Optional[int]

    enum_tag:dict[str, list[int]]
    "dict from tag to tagged texture id"

    tags:list[str]

    path: str

    @classmethod
    def from_json(cls, path:str, ts:dict[str, Any]) -> Self:
        if ts["embedAtlas"] is not None:
            raise NotImplementedError("embedAtlas is not implemented")
        
        path = os.path.join(path, ts["relPath"])
        new = cls(
            path = path,
            set = read_tilesets(path, ts),
            tag_source_enum_uid = ts["tagsSourceEnumUid"],
            uid = ts["uid"],
            custom_data = {},
            source_enum_id = ts["tagsSourceEnumUid"],
            enum_tag = { obj["enumValueId"]: obj["tileIds"] for obj in ts["enumTags"]},
            identifier = ts["identifier"], # TODO: allow user to find tileset by identifier
            tags = ts["tags"]
        )

        for data in ts["customData"]:
            li = new.custom_data.setdefault(data["tileId"], [])
            li.append(data["data"])

        return new

    def __getitem__(self, id: int) -> arcade.Texture:
        return self.set[id]
    
    def get_texture(self, rect:TileRect) -> arcade.Texture:
        return arcade.load_texture(self.path, x=rect["x"], y=rect["y"], width=rect["w"], height=rect["h"])


@dataclass(slots=True, frozen=True, kw_only=True)
class Enum:
    identifier: str
    tags: list[str]
    uid: int
    values: list[str]
    path: Optional[str]

    @classmethod
    def from_json(cls, dict:dict[str, Any]) -> Self:
        new = cls(
            identifier = dict["identifier"],
            tags = dict["tags"],
            uid = dict["uid"],
            values = [v["id"] for v in dict["values"]],
            path = dict["externalRelPath"] if "externalRelPath" in dict else None
        )
        return new


@dataclass(slots=True, frozen=True, kw_only=True)
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

    @classmethod
    def from_json(cls, ts:dict[str, Any], defs:"Defs") -> Self:
        new = cls(
            uid = ts["uid"],
            identifier = ts["identifier"],
            color = ts["color"],
            height = ts["height"],
            width = ts["width"],
            nine_slice_borders = ts["nineSliceBorders"],
            pivot_x = ts["pivotX"],
            pivot_y = ts["pivotY"],
            tileset_id = ts["tilesetId"],
            tile_rect = ts["tileRect"],
            tile = defs.get_texture(ts["tileRect"]) if ts["tileRect"] else None,
            tile_render_mode = ts["tileRenderMode"],
            ui_tile_rect = ts["uiTileRect"],
            ui_tile = defs.get_texture(ts["uiTileRect"]) if ts["uiTileRect"] else None
        )
        return new


@dataclass(slots=True, frozen=True, kw_only=True)
class Defs:
    tilesets : dict[int|str, TileSet]
    """a dict from uid to tilesets"""
    enums: dict[int|str, Enum]
    """merge of enums and externalenums"""
    entities: dict[int|str, EntityDefinition]

    @classmethod
    def from_json(cls, path:str, dict:dict[str, Any]) -> Self:
        new = cls(
            tilesets = { },
            enums = { },
            entities = { }
        )
        for ts in dict["tilesets"]:
            if "identifier" in ts and ts["identifier"] == 'Internal_Icons':
                print("Internal_Icons are not implemeted")
                continue
            tileset = TileSet.from_json(path, ts)
            new.tilesets[tileset.uid] = tileset
            new.tilesets[tileset.identifier] = tileset

        for en in dict["enums"]:
            enum = Enum.from_json(en)
            new.enums[enum.uid] = enum
            new.enums[enum.identifier] = enum

        for en in dict["externalEnums"]:
            enum = Enum.from_json(en)
            new.enums[enum.uid] = enum
            new.enums[enum.identifier] = enum

        for ent in dict["entities"]:
            entity = EntityDefinition.from_json(ent, new)
            new.entities[entity.uid] = entity
            new.entities[entity.identifier] = entity

        return new

    def get_texture(self, rect:TileRect) -> Optional[arcade.Texture]:
        if rect["tilesetUid"] in self.tilesets:
            return self.tilesets[rect["tilesetUid"]].get_texture(rect)

