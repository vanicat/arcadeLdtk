import arcadeLDtk
import arcade
import os.path

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
