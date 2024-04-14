from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Self, TypedDict
import os.path

import arcade

from .defs import Defs, EntityDefinition, TileSet


Converter = Callable[[float, float], tuple[float, float]]


class EntityRef(TypedDict):
    entityIid: str
    layerIid: str
    levelIid: str
    worldIid: str


@dataclass(frozen=True, slots=True)
class FieldInstance[T]:
    parent: T
    identifier: str
    type: str
    value: Any

    @classmethod
    def from_json(cls, parent: T, dict:dict[str, Any], converter:Converter) -> Self:
        identifier = dict["__identifier"]
        type = dict["__type"]
        if dict["__value"] is None:
            value = None
        else:
            match type:
                case "Color":
                    value = arcade.types.Color.from_hex_string(dict["__value"])
                case "Point":
                    value = converter(dict["__value"]["cx"], dict["__value"]["cy"])
                case "Array<Point>":
                    value = [converter(pt["cx"], pt["cy"]) for pt in dict["__value"]]
                case _:
                    value = dict["__value"]

        return cls(parent, identifier, type, value)


    def __str__(self) -> str:
        return f"FieldInstance:(id: {self.identifier}, type: {self.type}, value: {self.value!r})"
    
    @classmethod
    def build_instance_dict(cls, parent:T, di:dict, converter:Converter) -> dict[str, Self]:
        fields:dict[str, Self] = {}
        for f in di:
            fi = cls.from_json(parent, f, converter)
            if fi.identifier in fields:
                raise ValueError(f"{fi.identifier} is set twice")
            fields[fi.identifier] = fi
        return fields


@dataclass(slots=True)
class EntityInstance:
    #TODO: convert
    parent: "LayerInstance"
    identifier: str
    "Entity definition identifier"
    grid: tuple[int, int]
    "Grid-based coordinates "
    def_uid: int
    "Reference of the Entity definition UID"
    def_: EntityDefinition
    "Reference of the Entity definition UID"
    tags: list[str]
    "Array of tags defined in this Entity definition"
    fields: dict[str, FieldInstance[Self]]
    "An array of all custom fields and their values."
    iid: str
    "Unique instance identifier"
    world_x: Optional[int]
    "X world coordinate in pixels. Only available in GridVania or Free world layouts."
    world_y: Optional[int]
    "Y world coordinate in pixels Only available in GridVania or Free world layouts."
    px: tuple[float, float]
    "Pixel coordinates ([x,y] format) in current level coordinate space. Don't forget optional layer offsets, if they exist!"
    height: int
    "Entity height in pixels. For non-resizable entities, it will be the same as Entity definition."
    width: int
    "Entity width in pixels. For non-resizable entities, it will be the same as Entity definition."

    @classmethod
    def from_json(cls, parent: "LayerInstance", dict:dict[str, Any], defs: "Defs", converter:Converter) -> Self:
        grid = (dict["__grid"][0], dict["__grid"][1])
        def_uid = dict["defUid"] 
        def_ = defs.entities[def_uid]
        tags = dict["__tags"]
        iid = dict["iid"]
        identifier = dict["__identifier"]
        world_x = dict["__worldX"] if "__worldX" in dict else None
        world_y = dict["__worldY"] if "__worldY" in dict else None
        height = dict["height"]
        width = dict["width"]
        px = converter(dict["px"][0], dict["px"][1])

        self = cls(parent, identifier, grid, def_uid, def_, tags, {}, iid, world_x, world_y, px, height, width)
        self.fields = FieldInstance.build_instance_dict(self, dict["fieldInstances"], converter)
        return self


@dataclass(slots=True)
class TileInstance:
    parent: "LayerInstance"
    alpha: float
    flip_x: bool
    flip_y: bool
    position: tuple[float, float]
    texture: arcade.Texture

    @classmethod
    def from_json(cls, parent:"LayerInstance", dict:dict[str, Any], tileSet:TileSet, converter:Converter) -> Self:
        alpha = dict["a"]
        flip_x = dict["f"] & 1 != 0
        flip_y = dict["f"] & 2 != 0
        x, y = converter(dict["px"][0], dict["px"][1])
        position = (x, y)
        texture = tileSet[dict["t"]]
        return cls(parent, alpha, flip_x, flip_y, position, texture)


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
    tileset: Optional[TileSet]
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
    entity_list: list[EntityInstance]
    entity_by_iid: dict[str, EntityInstance]
    entity_by_identifier: dict[str, list[EntityInstance]]
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

    _sprite_list: Optional[arcade.SpriteList] = None
        

    def __init__(self, dict:dict[str, Any], defs:Defs, converter:Converter) -> None:
        self.c_height = dict["__cHei"]
        self.c_width = dict["__cWid"]
        self.grid_size = dict["__gridSize"]
        self.identifier = dict["__identifier"]
        self.opacity = dict["__opacity"]
        self.px_total_offset_x = dict["__pxTotalOffsetX"]
        self.px_total_offset_y = -dict["__pxTotalOffsetY"]
        
        tileset_uid = dict["__tilesetDefUid"]
        if tileset_uid is None:
            self.tileset = None
            self.auto_layer_tiles = None
            self.grid_tiles = None
        else:
            self.tileset = defs.tilesets[tileset_uid]
            self.auto_layer_tiles = [TileInstance.from_json(self, t, self.tileset, converter) for t in dict["autoLayerTiles"]]
            self.grid_tiles = [TileInstance.from_json(self, t, self.tileset, converter) for t in dict["gridTiles"]]

        self.type = dict["__type"]
        self.entity_list = [EntityInstance.from_json(self, e, defs, converter) for e in dict["entityInstances"]]
        self.entity_by_iid = { e.iid: e for e in self.entity_list }
        self.entity_by_identifier = {}
        for e in self.entity_list:
            elem = self.entity_by_identifier.setdefault(e.identifier, [])
            elem.append(e)

        self.int_grid_csv = dict["intGridCsv"]

        self.iid = dict["iid"]
        self.layer_def_uid = dict["layerDefUid"]
        self.level_id = dict["levelId"]
        self.override_tileset_uid = dict["overrideTilesetUid"]
        self.px_offset_x = dict["pxOffsetX"]
        self.px_offset_y = -dict["pxOffsetY"]
        self.visible = dict["visible"]

    def has_tiles(self) -> bool:
        return self.auto_layer_tiles is not None or self.grid_tiles is not None

    def sprite_list(self, regenerate: bool = False, **kwargs) -> arcade.SpriteList:
        if not regenerate and self._sprite_list:
            return self._sprite_list
        elif self.auto_layer_tiles is not None:
            tiles = self.auto_layer_tiles
        elif self.grid_tiles is not None:
            tiles = self.grid_tiles
        else:
            raise ValueError("this layer has no sprite")

        self._sprite_list = arcade.SpriteList(**kwargs)
    
        for t in tiles:
            texture = t.texture
            if t.flip_x:
                texture = texture.flip_horizontally()
            if t.flip_y:
                texture = texture.flip_vertically()

            sprite = arcade.Sprite(
                texture,
                center_x=t.position[0] + self.grid_size/2 + self.px_total_offset_x,
                center_y=t.position[1] - self.grid_size/2 + self.px_total_offset_y
            )
            self._sprite_list.append(sprite)

        return self._sprite_list
        


class Level:
    bg_color: arcade.types.Color
    
    bg_pos: Optional[dict[str, Any]]
    """TODO: convert to something arcade use"""


    bg_texture: Optional[arcade.Texture]

    field_instances: dict[str,FieldInstance[Self]]
    layers: list[LayerInstance]
    layers_by_iid: dict[str, LayerInstance]
    layers_by_identifier: dict[str, LayerInstance]

    identifier: str
    iid: str
    uid: int

    height: int
    width: int
    world_depth: int
    world_x: int
    world_y: int

    def __init__(self, path:str, level:dict, defs:Defs) -> None:
        self.level = level

        # set height and width first to be able to convert in init
        self.height = level["pxHei"]
        self.width = level["pxWid"]

        if level["externalRelPath"] is not None:
            raise NotImplementedError("Save level separately is not implemeted")
        
        self.bg_color = arcade.types.Color.from_hex_string(level["__bgColor"])

        if level["__bgPos"] is None:
            self.bg_pos = None
        else:
            self.bg_pos = level["__bgPos"]
            # crop_x, crop_y, crop_width, crop_height = level["__bgPos"]["cropRect"]
            # scale_x, scale_y = level["__bgPos"]["scale"]
            topLeft_x, topLeft_y = level["__bgPos"]["topLeftPx"]
            self.bg_pos["topLeftPx"] =  self.convert_coord(topLeft_x, topLeft_y)
         
        if level["bgRelPath"] is None:
            self.bg_texture = None
        else:
            self.bg_texture = arcade.load_texture(os.path.join(path, level["bgRelPath"]))

        self.field_instances = FieldInstance.build_instance_dict(self, level["fieldInstances"], self.convert_coord)

        self.identifier = level["identifier"]
        self.iid = level["iid"]
        self.uid = level["uid"]

        self.layers = [LayerInstance(l, defs, self.convert_coord) for l in level["layerInstances"]]
        self.layers_by_iid = { l.iid:l for l in self.layers }
        self.layers_by_identifier = { l.identifier:l for l in self.layers }

        # TODO: convert here ?
        self.world_depth = level["worldDepth"]
        self.world_x = level["worldX"]
        self.world_y = level["worldY"]

    def make_scene(self, regenerate=False) -> arcade.Scene:
        scene = arcade.Scene()
        for l in self.layers:
            if l.has_tiles():
                scene.add_sprite_list(l.identifier, sprite_list=l.sprite_list(regenerate=regenerate))

        return scene
    
    def convert_coord(self, x:float, y:float) -> tuple[float, float]:
        """Convert coord from or to arcade convention
        (0, 0) is at bottom left for aracade!"""
        return (x, (self.height - y))
        
    def to_world_coord(self, x:float, y:float) -> tuple[float, float]:
        """Convert coord from arcade convention to world coordinate"""
        x, y = self.convert_coord(x, y)
        return (self.world_x + x, self.world_y + y)
    
    def from_world_coord(self, x:float, y:float) -> tuple[float, float]:
        """Convert coord from arcade convention to world coordinate"""
        return self.convert_coord(x - self.world_x, y - self.world_y)
    
    def contains_world_coord(self, x:float, y:float) -> bool:
        return self.contains_coord(*self.from_world_coord(x, y))
    
    def contains_coord(self, x:float, y:float) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
    