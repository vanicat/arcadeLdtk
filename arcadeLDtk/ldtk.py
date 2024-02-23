
from typing import Any, Literal, Optional
import json
import os.path

import arcade

from .levels import Level
from .defs import Defs


class LDtk:
    bg_color: arcade.types.Color
    defs: Defs
    iid: str
    json_version: str
    levels: list[Level] | dict[tuple[int, int], Level]
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

        self.world_grid_height = dict["worldGridHeight"]
        self.world_grid_width = dict["worldGridWidth"]
        self.world_layout = dict["worldLayout"]

        if dict["worlds"]:
            raise NotImplementedError("multi world is not implemented yet")
        
        self.world = None
        
        self.toc = {
            elem["identifier"]: elem for elem in dict["toc"]
        }


def read_LDtk(path:str) -> LDtk:
    directory = os.path.dirname(path)

    with(open(path)) as f:
        dict = json.load(f)
        return LDtk(directory, dict)