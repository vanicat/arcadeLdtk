import arcadeLDtk
import arcade
import os.path

from arcadeLDtk import Level

samples = [
    "AutoLayers_1_basic.ldtk",
    "AutoLayers_2_stamps.ldtk",
    "AutoLayers_3_Mosaic.ldtk",
    "AutoLayers_4_Assistant.ldtk",
    "AutoLayers_5_Advanced.ldtk", 
    "AutoLayers_6_OptionalRules.ldtk",
    "AutoLayers_7_Biomes.ldtk",
    "Entities.ldtk",
    # "SeparateLevelFiles.ldtk", # external levels are not implemented
    "Test_file_for_API_showing_all_features.ldtk",
    "Typical_2D_platformer_example.ldtk",
    "Typical_TopDown_example.ldtk",
    # "WorldMap_Free_layout.ldtk", # PIL doesn't know about aseprite
    "WorldMap_GridVania_layout.ldtk",
]

def test_load_sample():
    for path in samples:
        arcadeLDtk.read_LDtk(os.path.join("test/samples/", path))

def test_many_features():
    example = arcadeLDtk.read_LDtk("test/samples/Test_file_for_API_showing_all_features.ldtk")
    assert isinstance(example.levels, list)
    assert len(example.levels) == 4
    assert isinstance(example.levels[0], Level)
    fst_level = example.levels[0]
    assert fst_level.identifier == "Everything"
    scene = fst_level.make_scene()
    for layer in fst_level.layers:
        match layer.identifier:
            case "Entities":
                assert layer.type == "Entities"
                assert layer.auto_layer_tiles is None
                assert layer.grid_tiles is None
                assert layer.int_grid_csv == []
                for instance in layer.entity_list:
                    if "target" in instance.fields:
                        target = instance.fields["target"]
                        assert isinstance(target.value, dict)
                        example.get_entity(target.value) # type: ignore

            case "IntGrid_8px_grid":
                assert layer.type == "IntGrid"
            case "PureAutoLayer":
                assert layer.type == "AutoLayer"
            case "IntGrid_without_rules":
                assert layer.type == "IntGrid"
                assert layer.has_tiles() is False
            case "IntGrid_with_rules":
                assert layer.type == "IntGrid"
                assert layer.has_tiles()
            case "Tiles":
                assert layer.type == "Tiles"
                assert layer.has_tiles()
            case _:
                assert False, f"unkonw layer: {layer.identifier}"
