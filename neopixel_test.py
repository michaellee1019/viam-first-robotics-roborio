import board
import neopixel
from ntcore import NetworkTableInstance, NetworkTable, Event, EventFlags

import adafruit_led_animation
from adafruit_led_animation.color import AMBER, AQUA, BLACK, BLUE, GREEN, ORANGE, PINK, PURPLE, RED, WHITE, YELLOW, GOLD, JADE, MAGENTA, OLD_LACE, TEAL
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.colorcycle import ColorCycle
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.customcolorchase import CustomColorChase
from adafruit_led_animation.animation import Animation

# The number of NeoPixels
num_pixels = 30

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

def initialize_pin(pin_name):
    pin_object = getattr(board, pin_name, None)
    if pin_object is None:
        raise ValueError("Invalid pin_name: {}".format(pin_name))
    return pin_object

class nt_handler:

    inst = NetworkTableInstance.getDefault()
    pixel_pin = initialize_pin("D18")
    pixel_num = 32
    pixels = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=1, auto_write=False, pixel_order=ORDER
    )

    speed = 0.1
    colors = [RED]
    tail_length = 1
    bounce= False
    size = 1
    spacing = 1
    period = 1
    num_sparkles = 1
    step = 1

    blink = Blink(pixels, speed=speed, color=colors[0])
    colorcycle = ColorCycle(pixels, speed=speed, colors=colors)
    comet = Comet(pixels, speed=speed, color=colors[0], tail_length=tail_length, bounce=bounce)
    chase = Chase(pixels, speed=speed, size=size, spacing=spacing, color=colors[0])
    pulse = Pulse(pixels, speed=speed, period=period, color=colors[0])
    sparkle = Sparkle(pixels, speed=speed, color=colors[0], num_sparkles=num_sparkles)
    solid = Solid(pixels, color=colors[0])
    rainbow = Rainbow(pixels, speed=speed, period=period)
    sparkle_pulse = SparklePulse(pixels, speed=speed, period=period, color=colors[0])
    rainbow_comet = RainbowComet(pixels, speed=speed, tail_length=tail_length, bounce=bounce)
    rainbow_chase = RainbowChase(pixels, speed=speed, size=size, spacing=spacing, step=step)
    rainbow_sparkle = RainbowSparkle(pixels, speed=speed, num_sparkles=num_sparkles)
    custom_color_chase = CustomColorChase(pixels, speed=speed, size=size, spacing=spacing, colors=colors)

    annimation_name = 'blink'

    def __init__(self):
        self.regenerate_animations()
        self.connect()

    def regenerate_animations(self):
        self.blink = Blink(self.pixels, speed=self.speed, color=self.colors[0])
        self.colorcycle = ColorCycle(self.pixels, speed=self.speed, colors=self.colors)
        self.comet = Comet(self.pixels, speed=self.speed, color=self.colors[0], tail_length=self.tail_length, bounce=self.bounce)
        self.chase = Chase(self.pixels, speed=self.speed, size=self.size, spacing=self.spacing, color=self.colors[0])
        self.pulse = Pulse(self.pixels, speed=self.speed, period=self.period, color=self.colors[0])
        self.sparkle = Sparkle(self.pixels, speed=self.speed, color=self.colors[0], num_sparkles=self.num_sparkles)
        self.solid = Solid(self.pixels, color=self.colors[0])
        self.rainbow = Rainbow(self.pixels, speed=self.speed, period=self.period)
        self.sparkle_pulse = SparklePulse(self.pixels, speed=self.speed, period=self.period, color=self.colors[0])
        self.rainbow_comet = RainbowComet(self.pixels, speed=self.speed, tail_length=self.tail_length, bounce=self.bounce)
        self.rainbow_chase = RainbowChase(self.pixels, speed=self.speed, size=self.size, spacing=self.spacing, step=self.step)
        self.rainbow_sparkle = RainbowSparkle(self.pixels, speed=self.speed, num_sparkles=self.num_sparkles)
        self.custom_color_chase = CustomColorChase(self.pixels, speed=self.speed, size=self.size, spacing=self.spacing, colors=self.colors)

    def get_animation(self, animation: str) -> Animation:
        animation_map = {
            "blink": self.blink,
            "colorcycle": self.colorcycle,
            "comet": self.comet,
            "chase": self.chase,
            "pulse": self.pulse,
            "sparkle": self.sparkle,
            "solid": self.solid,
            "rainbow": self.rainbow,
            "sparkle_pulse": self.sparkle_pulse,
            "rainbow_comet": self.rainbow_comet,
            "rainbow_chase": self.rainbow_chase,
            "rainbow_sparkle": self.rainbow_sparkle,
            "custom_color_chase": self.custom_color_chase
        }
        return animation_map.get(animation.lower(), self.blink)  # Default to blink if animation is not found

    def get_color(self, color: str) -> adafruit_led_animation.color:
        color_map = {
            "amber": AMBER,
            "aqua": AQUA,
            "black": BLACK,
            "blue": BLUE,
            "green": GREEN,
            "orange": ORANGE,
            "pink": PINK,
            "purple": PURPLE,
            "red": RED,
            "white": WHITE,
            "yellow": YELLOW,
            "gold": GOLD,
            "jade": JADE,
            "magenta": MAGENTA,
            "old_lace": OLD_LACE,
            "teal": TEAL
        }
        return color_map.get(color.lower(), BLACK)  # Default to black if color is not found


# animations = AnimationSequence(
#     comet,
#     blink,
#     rainbow_sparkle,
#     chase,
#     pulse,
#     sparkle,
#     rainbow,
#     solid,
#     rainbow_comet,
#     sparkle_pulse,
#     rainbow_chase,
#     custom_color_chase,
#     advance_interval=5,
#     auto_clear=True,
# )

# while True:
#     animations.animate()

    table: NetworkTable = None

    def connect(self):
        self.inst.startClient4("VIAM")
        self.inst.setServerTeam(1234)
        # self.inst.setServer("host", NetworkTableInstance.kDefaultPort4)
        table = self.inst.getTable("VIAM")
        table.addListener(EventFlags.kValueAll, self.update_state)

    def is_connected(self):
        return self.inst.isConnected()
    
    def animate(self):
        animation = self.get_animation(self.annimation_name)
        animation.animate()
        # print("animating")

    def update_state(self, new_table: NetworkTable, field_name: str, event: Event):
        match field_name:
            case "animation":
                self.annimation_name = event.data.value.getString()
            case "speed":
                self.speed = event.data.value.getDouble()
            case "colors":
                new_colors = []
                for color in event.data.value.getStringArray():
                    new_colors.append(self.get_color(color))
                self.colors = new_colors
            case "tail_length":
                self.tail_length = event.data.value.getInteger()
            case "bounce":
                self.bounce = event.data.value.getBoolean()
            case "size":
                self.size = event.data.value.getInteger()
            case "spacing":
                self.spacing = event.data.value.getInteger()
            case "period":
                self.period = event.data.value.getInteger()
            case "num_sparkles":
                self.num_sparkles = event.data.value.getInteger()
            case "step":
                self.step = event.data.value.getInteger()

        self.regenerate_animations()

nt = nt_handler()

while True:
    nt.animate()