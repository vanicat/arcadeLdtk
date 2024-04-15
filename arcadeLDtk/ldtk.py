
from dataclasses import dataclass
from typing import Any, Literal, Optional, Self
import json
import os.path

import arcade

from .levels import LayerInstance, Level, EntityRef, EntityInstance
from .defs import Defs


@dataclass(slots=True, kw_only=True)
class LDtk:
    bg_color: arcade.types.Color
    defs: Defs
    iid: str
    json_version: str
    levels: list[Level]# | dict[tuple[int, int], Level]
    levels_by_iid: dict[str, Level]
    toc: dict[str, Any] #TODO: typing
    world_grid_height: Optional[int]
    world_grid_width: Optional[int]
    world_layout: Optional[Literal["Free"] | Literal["GridVania"] | Literal["LinearHorizontal"] | Literal["LinearVertical"]]
    world: None
    default_grid_size: int

    @classmethod
    def from_json(cls, path:str, dict:dict[str, Any]) -> Self:
        if dict["externalLevels"]:
            raise NotImplementedError("external levels are not implemented")
        if dict["worlds"]:
            raise NotImplementedError("multi world is not implemented yet")
        
        new = cls(
            bg_color = arcade.types.Color.from_hex_string(dict["bgColor"]),
            defs = Defs.from_json(path, dict["defs"]),
            iid = dict["iid"],
            json_version = dict["jsonVersion"],
            levels = [],
            levels_by_iid = { },

            world_grid_height = dict["worldGridHeight"],
            world_grid_width = dict["worldGridWidth"],
            world_layout = dict["worldLayout"],
            
            world = None,
                toc = {
                elem["identifier"]: elem for elem in dict["toc"]
            },
            default_grid_size = dict["defaultGridSize"]
        )
        new.levels = [Level.from_json(new, path, l) for l in dict["levels"]]
        new.levels_by_iid = { l.iid: l for l in new.levels }
        return new

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
        return LDtk.from_json(directory, dict)