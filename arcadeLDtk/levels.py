from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, Self, TypedDict
import os.path

import arcade

if TYPE_CHECKING:
    from . import LDtk

from .defs import Defs, EntityDefinition, TileSet


class HasDef:
    @property
    def defs(self) -> Defs:
        return self.parent.defs


class EntityRef(TypedDict):
    entityIid: str
    layerIid: str
    levelIid: str
    worldIid: str


@dataclass(frozen=True, slots=True)
class FieldInstance[T](HasDef):
    parent: T
    identifier: str
    type: str
    value: Any

    @classmethod
    def from_json(cls, parent: T, level: "Level", dict:dict[str, Any]) -> Self:
        identifier = dict["__identifier"]
        type = dict["__type"]
        if dict["__value"] is None:
            value = None
        else:
            match type:
                case "Color":
                    value = arcade.types.Color.from_hex_string(dict["__value"])
                case "Point":
                    value = level.convert_coord(dict["__value"]["cx"], dict["__value"]["cy"])
                case "Array<Point>":
                    value = [level.contains_coord(pt["cx"], pt["cy"]) for pt in dict["__value"]]
                case _:
                    value = dict["__value"]

        return cls(parent, identifier, type, value)


    def __str__(self) -> str:
        return f"FieldInstance:(id: {self.identifier}, type: {self.type}, value: {self.value!r})"
    
    @classmethod
    def build_instance_dict(cls, parent:T, level:"Level", di:dict) -> dict[str, Self]:
        fields:dict[str, Self] = {}
        for f in di:
            fi = cls.from_json(parent, level, f)
            if fi.identifier in fields:
                raise ValueError(f"{fi.identifier} is set twice")
            fields[fi.identifier] = fi
        return fields


@dataclass(slots=True)
class EntityInstance(HasDef):
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
    def from_json(cls, parent: "LayerInstance", dict:dict[str, Any]) -> Self:
        grid = (dict["__grid"][0], dict["__grid"][1])
        def_uid = dict["defUid"] 
        def_ = parent.parent.parent.defs.entities[def_uid]
        tags = dict["__tags"]
        iid = dict["iid"]
        identifier = dict["__identifier"]
        world_x = dict["__worldX"] if "__worldX" in dict else None
        world_y = dict["__worldY"] if "__worldY" in dict else None
        height = dict["height"]
        width = dict["width"]
        px = parent.parent.convert_coord(dict["px"][0], dict["px"][1])

        new = cls(parent, identifier, grid, def_uid, def_, tags, {}, iid, world_x, world_y, px, height, width)
        new.fields = FieldInstance.build_instance_dict(new, parent.parent, dict["fieldInstances"])
        return new


@dataclass(slots=True, frozen=True)
class TileInstance(HasDef):
    parent: "LayerInstance"
    alpha: float
    flip_x: bool
    flip_y: bool
    position: tuple[float, float]
    texture: arcade.Texture

    @classmethod
    def from_json(cls, parent:"LayerInstance", dict:dict[str, Any], tileSet:TileSet) -> Self:
        alpha = dict["a"]
        flip_x = dict["f"] & 1 != 0
        flip_y = dict["f"] & 2 != 0
        x, y = parent.parent.convert_coord(dict["px"][0], dict["px"][1])
        position = (x, y)
        texture = tileSet[dict["t"]]
        return cls(parent, alpha, flip_x, flip_y, position, texture)


@dataclass(slots=True, kw_only=True)
class LayerInstance(HasDef):
    parent: "Level"
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
        
    @classmethod
    def from_json(cls, parent: "Level", dict:dict[str, Any]) -> Self:
        new:Self = cls(
            parent = parent, 
            c_height = dict["__cHei"], 
            c_width = dict["__cWid"],
            grid_size = dict["__gridSize"],
            identifier = dict["__identifier"],
            opacity = dict["__opacity"],
            px_total_offset_x = dict["__pxTotalOffsetX"],
            px_total_offset_y = -dict["__pxTotalOffsetY"],
            tileset = None,
            auto_layer_tiles = None,
            grid_tiles = None,
            type = dict["__type"],
            entity_list = [],
            entity_by_iid = {},
            entity_by_identifier = {},
            int_grid_csv = dict["intGridCsv"],
            iid = dict["iid"],
            layer_def_uid = dict["layerDefUid"],
            level_id = dict["levelId"],
            override_tileset_uid = dict["overrideTilesetUid"],
            px_offset_x = dict["pxOffsetX"],
            px_offset_y = -dict["pxOffsetY"],
            visible = dict["visible"]
        )

        tileset_uid = dict["__tilesetDefUid"]
        if tileset_uid is not None:
            new.tileset = parent.parent.defs.tilesets[tileset_uid]
            new.auto_layer_tiles = [TileInstance.from_json(new, t, new.tileset) for t in dict["autoLayerTiles"]]
            new.grid_tiles = [TileInstance.from_json(new, t, new.tileset) for t in dict["gridTiles"]]

        new.entity_list = [EntityInstance.from_json(new, e) for e in dict["entityInstances"]]
        new.entity_by_iid = { e.iid: e for e in new.entity_list }

        for e in new.entity_list:
            elem = new.entity_by_identifier.setdefault(e.identifier, [])
            elem.append(e)

        return new


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


@dataclass(slots=True, kw_only=True)
class Level(HasDef):
    parent: "LDtk"
    level:dict[str, Any]
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

    @classmethod
    def from_json(cls, parent: "LDtk", path:str, level:dict[str, Any]) -> Self:
        if level["externalRelPath"] is not None:
            raise NotImplementedError("Save level separately is not implemeted")
        
        new = cls(
            parent = parent,
            level = level,
            # set height and width first to be able to convert in init
            height = level["pxHei"],
            width = level["pxWid"],
            bg_color = arcade.types.Color.from_hex_string(level["__bgColor"]),
            bg_pos = level["__bgPos"],
            # crop_x, crop_y, crop_width, crop_height = level["__bgPos"]["cropRect"]
            # scale_x, scale_y = level["__bgPos"]["scale"]
            bg_texture = arcade.load_texture(os.path.join(path, level["bgRelPath"])) if level["bgRelPath"] is not None else None,
            field_instances = {},
            identifier = level["identifier"],
            iid = level["iid"],
            uid = level["uid"],
            layers = [], layers_by_iid = {}, layers_by_identifier = {},
            world_depth = level["worldDepth"],
            # TODO: convert here ?
            world_x = level["worldX"],
            world_y = level["worldY"]
        ) 
     

        new.field_instances = FieldInstance.build_instance_dict(new, new, level["fieldInstances"])

        new.layers = [LayerInstance.from_json(new, l) for l in level["layerInstances"]]
        new.layers_by_iid = { l.iid:l for l in new.layers }
        new.layers_by_identifier = { l.identifier:l for l in new.layers }

        
        if new.bg_pos:
            new.bg_pos["topLeftPx"] =  new.convert_coord(*new.bg_pos["topLeftPx"])

        return new



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
    