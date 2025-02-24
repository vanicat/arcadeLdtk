import arcade
from arcade.types.rect import Rect, Viewport
from arcadeLDtk import read_LDtk, EntityInstance
from pyglet.math import Vec2

from arcadeLDtk.levels import LayerInstance

ZOOM = 3

class GameWindow(arcade.Window):
    """ Main Window """

    def __init__(self, path, width, height, title):
        """ Create the variables """

        # Init the parent class
        super().__init__(width, height, title)

        self.game = read_LDtk(path)

        self.level = self.game.levels[0]

        arcade.set_background_color(self.game.bg_color)

        self.keys = [False, False, False, False]

    
    def setup(self):
        self.scene = self.level.make_scene()
        entities = self.level.layers_by_identifier["Entities"]
        self.setup_player(entities)
        self.setup_mob(entities)
        self.camera = arcade.camera.Camera2D(viewport=Viewport(0, 0, 1024, 768), zoom=ZOOM)
        self.camera_dx = 1024 / 2
        self.camera_dy = 768 / 2


    def setup_player(self, entities:LayerInstance):
        start = entities.entity_by_identifier["Player"][0]
        self.player = arcade.SpriteCircle(min(start.height, start.width) // 3, color = arcade.color.YELLOW_ROSE)
        self.player.center_x = start.px[0] + start.height / 2
        self.player.center_y = start.px[1] + start.width / 2


    def setup_mob(self, entities:LayerInstance):
        self.mobs = arcade.SpriteList()
        self.mob_texture = arcade.load_texture(
            ":resources:/images/animated_characters/robot/robot_idle.png"
        )
        for mob in entities.entity_by_identifier["Mob"]:
            x, y = mob.px
            sprite = arcade.Sprite(self.mob_texture, center_x=x, center_y=y)
            sprite.scale = mob.height / sprite.height
            sprite.center_x = x + (mob.def_.pivot_x - 0.5) * mob.width
            sprite.center_y = y + (mob.def_.pivot_y - 0.5) * mob.height
             
            

            self.mobs.append(sprite)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.UP:
                self.keys[1] = True
            case arcade.key.DOWN:
                self.keys[2] = True
            case arcade.key.LEFT:
                self.keys[0] = True
            case arcade.key.RIGHT:
                self.keys[3] = True

        return super().on_key_press(symbol, modifiers)


    def on_key_release(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.UP:
                self.keys[1] = False
            case arcade.key.DOWN:
                self.keys[2] = False
            case arcade.key.LEFT:
                self.keys[0] = False
            case arcade.key.RIGHT:
                self.keys[3] = False

        return super().on_key_release(symbol, modifiers)

    
    def on_update(self, delta_time: float):
        x, y = (self.player.center_x, self.player.center_y)
        if self.keys[0]:
            self.player.center_x -= 1
        if self.keys[3]:
            self.player.center_x += 1
        if self.keys[1]:
            self.player.center_y += 1
        if self.keys[2]:
            self.player.center_y -= 1

        # print(self.player.collides_with_list(self.scene["Collisions"]))

        self.camera.position = (self.player.center_x, self.player.center_y)
        return super().on_update(delta_time)

    def on_draw(self):
        self.camera.use()
        self.scene.draw()
        self.scene.get_sprite_list("Collisions").draw() # TODO ? the order of loaded sprite list seem to be a problem
        self.mobs.draw()
        arcade.draw_sprite(self.player)


def main() -> None:
    win = GameWindow("test/samples/Typical_2D_platformer_example.ldtk", 1024, 768, "test game")
    win.setup()
    arcade.run()

if __name__ == "__main__":
    main()
