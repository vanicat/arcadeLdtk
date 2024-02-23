from typing import Any, Literal, Optional
import arcade
from .defs import Defs, TileSet


class FieldInstance:
    def __init__(self, dict:dict[str, Any]) -> None:
        self.identifier = dict["__identifier"]
        self.type = dict["__type"]
        if dict["__value"] is None:
            self.value = None
        else:
            match self.type:
                case "Color":
                    self.value = arcade.types.Color.from_hex_string(dict["__value"])
                case "Point":
                    self.value = (dict["__value"]["cx"], dict["__value"]["cy"])
                # case "EntityRef": #TODO: something to load the value later

                case _:
                    self.value = dict["__value"]


class EntityInstance:
    grid: tuple[int, int]
    def_uid: int
    tags: list[str]
    fields: list[FieldInstance]
    iid: str
    world_x: Optional[int]
    world_y: Optional[int]
    px: tuple[int, int]

    def __init__(self, dict:dict[str, Any]) -> None:
        self.grid = (dict["__grid"][0], dict["__grid"][1])
        self.def_uid = dict["defUid"] 
        self.tags = dict["__tags"]
        self.fields = [FieldInstance(f) for f in dict["fieldInstances"]]
        self.iid = dict["iid"]
        self.world_x = dict["__worldX"] if "__worldX" in dict else None
        self.world_y = dict["__worldY"] if "__worldY" in dict else None
        self.height = dict["height"]
        self.width = dict["width"]
        self.px = (dict["px"][0], dict["px"][1])


class TileInstance:
    alpha: float
    flip_x: bool
    flip_y: bool
    position: tuple[int, int]
    texture: arcade.Texture

    def __init__(self, dict:dict[str, Any], texture:TileSet):
        self.alpha = dict["a"]
        self.flip_x = dict["f"] == 1 or dict["f"] == 3
        self.flip_y = dict["f"] == 2 or dict["f"] == 3
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

    _sprite_list: Optional[arcade.SpriteList] = None
        

    def __init__(self, dict:dict[str, Any], defs:Defs):
        self.c_height = dict["__cHei"]
        self.c_width = dict["__cWid"]
        self.grid_size = dict["__gridSize"]
        self.identifier = dict["__identifier"]
        self.opacity = dict["__opacity"]
        self.px_total_offset_x = dict["__pxTotalOffsetX"]
        self.px_total_offset_y = dict["__pxTotalOffsetY"]
        
        tileset_uid = dict["__tilesetDefUid"]
        if tileset_uid is None:
            self.tileset = None
            self.auto_layer_tiles = None
            self.grid_tiles = None
        else:
            self.tileset = defs.tilesets[tileset_uid]
            self.auto_layer_tiles = [TileInstance(t, self.tileset) for t in dict["autoLayerTiles"]]
            self.grid_tiles = [TileInstance(t, self.tileset) for t in dict["gridTiles"]]

        self.type = dict["__type"]
        self.entity_instances = [EntityInstance(e) for e in dict["entityInstances"]]
        self.int_grid_csv = dict["intGridCsv"]

        self.iid = dict["iid"]
        self.layer_def_uid = dict["layerDefUid"]
        self.level_id = dict["levelId"]
        self.override_tileset_uid = dict["overrideTilesetUid"]
        self.px_offset_x = dict["pxOffsetX"]
        self.px_offset_y = dict["pxOffsetY"]
        self.visible = dict["visible"]

    def sprite_list(self, scale = 1, regenerate: bool = False, **kwargs) -> arcade.SpriteList:
        if not regenerate and self._sprite_list:
            return self._sprite_list
        elif self.auto_layer_tiles is not None:
            tiles = self.auto_layer_tiles
        elif self.grid_tiles is not None:
            tiles = self.grid_tiles
        else:
            raise ValueError("this layer has no sprite")

        self._sprite_list = arcade.SpriteList(**kwargs)

        height = self.c_height * self.grid_size
        offset_x = self.px_total_offset_x + self.grid_size/2
        offset_y = height - self.px_total_offset_y - self.grid_size/2
    
        for t in tiles:
            texture = t.texture
            if t.flip_x:
                texture = texture.flip_horizontally()
            if t.flip_y:
                texture = texture.flip_vertically()

            # TODO: offset and scale
            sprite = arcade.Sprite(texture, scale=scale,
                                   center_x=(offset_x + t.position[0]) * scale, center_y= (offset_y - t.position[1]) * scale)
            self._sprite_list.append(sprite)

        return self._sprite_list
        


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
        else: #TODO: correct path
            self.bg_texture = arcade.load_texture(level["bgRelPath"])

        # in true, not implemeted
        self.field_instances = [FieldInstance(f) for f in level["fieldInstances"]]

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

    def make_scene(self, scale=1, regenerate=False):
        scene = arcade.Scene()
        for l in self.layers:
            scene.add_sprite_list(l.identifier, sprite_list=l.sprite_list(scale=scale, regenerate=regenerate))
        return scene