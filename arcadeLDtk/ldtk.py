
from typing import Any, Literal, Optional
import json
import os.path

import arcade

from .levels import LayerInstance, Level, EntityRef, EntityInstance
from .defs import Defs


class LDtk:
    bg_color: arcade.types.Color
    defs: Defs
    iid: str
    json_version: str
    levels: list[Level]# | dict[tuple[int, int], Level]
    levels_by_iid: dict[str, Level]
    toc: dict[str, Any] #TODO: typing
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
        self.levels = [Level(path, l, self.defs) for l in dict["levels"]]
        self.levels_by_iid = { l.iid: l for l in self.levels }

        self.world_grid_height = dict["worldGridHeight"]
        self.world_grid_width = dict["worldGridWidth"]
        self.world_layout = dict["worldLayout"]

        if dict["worlds"]:
            raise NotImplementedError("multi world is not implemented yet")
        
        self.world = None
        
        self.toc = {
            elem["identifier"]: elem for elem in dict["toc"]
        }

    def get_entity(self, it:EntityRef) -> tuple[Level, LayerInstance, EntityInstance]:
        level = self.levels_by_iid[it["levelIid"]]
        layer = level.layers_by_iid[it["layerIid"]]
        entity = layer.entity_by_iid[it["entityIid"]]
        return level, layer, entity

    def get_levels_at_point(self, x:float, y:float) -> list[Level]:
        """Return the levels at point, using word coordinate"""
        return [level for level in self.levels if level.contains_world_coord(x, y)]


def read_LDtk(path:str) -> LDtk:
    directory = os.path.dirname(path)

    with(open(path)) as f:
        dict = json.load(f)
        return LDtk(directory, dict)