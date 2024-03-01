import json
import requests
import asyncio
import time

from typing import ClassVar, Mapping, Sequence

from typing_extensions import Self

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
# TODO: Convert to generic service
from viam.components.generic import Generic
from viam import logging
# from viam.utils import sensor_readings_value_to_native
import threading

import microcontroller
import board
import neopixel
import ntcore
from viam.utils import sensor_readings_value_to_native
from viam.components.movement_sensor import Vector3, GeoPoint, Orientation


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

LOGGER = logging.getLogger(__name__)

class RoborioNetworkTableSensorServer(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:roborio:nt-sensor-server")

    nt: ntcore.NetworkTableInstance = None
    table: ntcore.NetworkTable = None
    sensors = list()
    thread = None
    event = None

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_readings())

    def start_thread(self):
        self.thread = threading.Thread(target=self.thread_run())
        self.event = threading.Event()
        self.thread.start()

    def stop_thread(self):
        if self.thread is not None and self.event is not None:
            self.event.set()
            self.thread.join()

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        nt_server = cls(config.name)
        nt_server.reconfigure(config, dependencies)
        return nt_server

    def convert_to_primative(self, readings: any) -> dict:
        if not isinstance(readings, dict):
            readings = sensor_readings_value_to_native(readings)

        for key, value in readings.items():
            match value:
                case Vector3():
                    readings[key] = dict(x=value.x, y=value.y, z=value.z)
                case Orientation():
                    readings[key] = dict(o_x=value.o_x, o_y=value.o_y, o_z=value.o_z)
                case GeoPoint():
                    readings[key] = dict(latitude=value.latitude, longitude=value.longitude)

        return readings

    async def send_readings(self):
        while True:
            if self.event.is_set():
                return
            
            for (sensor_name, sensor_resource) in self.sensors:
                readings = await sensor_resource.get_readings()
                readings_prim = self.convert_to_primative(readings)
                for reading_name, reading in readings_prim:
                    if isinstance(reading, dict):
                        for subreading_name, subreading in reading:
                            self.nt.putValue("{}-{}-{}".format(sensor_name, reading_name, subreading_name), subreading)
                    else:
                        self.nt.putValue("{}-{}".format(sensor_name, reading_name), reading)

    def connect(self, team_number: int):
        self.nt.startClient4("ViamSensors")
        self.nt.setServerTeam(team_number)
        # TODO: Keep/Remove/Attribute? Works if not set.
        # self.inst.setServer("host", NetworkTableInstance.kDefaultPort4)
        self.table = self.nt.getTable("ViamSensors")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        if "team_number" not in config.attributes.fields:
            raise Exception("A team_number attribute is required for nt-sensor-server component.")

        return None
    
    def reconfigure(self,
                    config: ComponentConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        self.stop_thread()

        self.sensors = dependencies.items()

        # connect to a specific host/port
        self.nt = ntcore.NetworkTableInstance.getDefault()

        team_number: int = int(config.attributes.fields["team_number"].number_value)
        self.connect(team_number)

        self.start_thread()

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping nt-sensor-server...")
        self.stop_thread()
        ntcore.NetworkTableInstance.destroy(self.nt)

class RoborioNetworkTableLightStrip(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:roborio:nt-light-strip")

    # NetworkTable settings
    nt: ntcore.NetworkTableInstance = None
    table: ntcore.NetworkTable = None
    pixels: neopixel.NeoPixel = None

    # Animation settings
    speed: float = 0.1
    colors: list[str]= [RED]
    tail_length: int = 1
    bounce: bool = False
    size: int = 1
    spacing: int = 1
    period: int = 1
    num_sparkles: int = 1
    step: int = 1

    # Animation configuration
    animation_name: str = 'blink'
    blink: Animation = None
    colorcycle: Animation = None
    comet: Animation = None
    chase: Animation = None
    pulse: Animation = None
    sparkle: Animation = None
    solid: Animation = None
    rainbow: Animation = None
    sparkle_pulse: Animation = None
    rainbow_comet: Animation = None
    rainbow_chase: Animation = None
    rainbow_sparkle: Animation = None
    custom_color_chase: Animation = None

    # Animation thread settings
    thread = None
    event = None

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.animate())

    def start_thread(self):
        self.thread = threading.Thread(target=self.thread_run())
        self.event = threading.Event()
        self.thread.start()

    def stop_thread(self):
        if self.thread is not None and self.event is not None:
            self.event.set()
            self.thread.join()

    async def animate(self):
        while True:
            if self.event.is_set():
                LOGGER.info("stopping animation thread")
                return
            
            animation = self.get_animation(self.animation_name)
            animation.animate()
    
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

    def initialize_pin(self, pin_name):
        pin_object = getattr(board, pin_name, None)
        if pin_object is None:
            raise ValueError("Invalid pin_name: {}".format(pin_name))
        return pin_object
    
    def initialize_pixel_order(self, pixel_order):
        order = getattr(neopixel, pixel_order, None)
        if order is None:
            raise ValueError("Invalid pixel_order: {}".format(pixel_order))
        return order

    def connect(self, team_number: int):
        self.nt.startClient4("ViamLightStrip")
        self.nt.setServerTeam(team_number)
        # TODO: Keep/Remove/Attribute? Works if not set.
        # self.inst.setServer("host", NetworkTableInstance.kDefaultPort4)
        self.table = self.nt.getTable("ViamLightStrip")
        self.table.addListener(ntcore.EventFlags.kValueAll, self.update_state)

    def update_state(self, new_table: ntcore.NetworkTable, field_name: str, event: ntcore.Event):
        LOGGER.info("Updating with new network table values...")
        LOGGER.info(f"field: {field_name}")
        LOGGER.info(f"event: {event}")
        match field_name:
            case "animation":
                LOGGER.info(f"field value: {event.data.value.getString()}")
                self.animation_name = event.data.value.getString()
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
        LOGGER.info("new animation_name:", self.animation_name)
        # self.stop_thread()
        # self.start_thread()
               
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        nt_server = cls(config.name)
        nt_server.reconfigure(config, dependencies)
        return nt_server
    
    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        if "team_number" not in config.attributes.fields:
            raise Exception("A team_number attribute is required for nt-light-strip component. Must be a 4 digit integer")

        if "pin" not in config.attributes.fields:
            raise Exception("A pin_number attribute is required for nt-light-strip component. Must be a string in the format like 'D18' and must be connected to must be 'D10', 'D12', 'D18' or 'D21'")

        if "num_pixels" not in config.attributes.fields:
            raise Exception("A num_pixels attribute is required for nt-light-strip component. Must be an integer")
        
        if "brightness" not in config.attributes.fields:
            raise Exception("A brightness attribute is required for nt-light-strip component. Must be a float like 0.2 for 20% brightness")

        if "pixel_order" not in config.attributes.fields:
            raise Exception("A pixel_order attribute is required for nt-light-strip component. Must be a string of: 'GRB', 'GRBW', 'RGB', or 'RGBW'")

        return None

    def reconfigure(self,
                    config: ComponentConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        self.stop_thread()

        pin_number: str = config.attributes.fields["pin"].string_value
        num_pixels: int = int(config.attributes.fields["num_pixels"].number_value)
        pixel_order: str = config.attributes.fields["pixel_order"].string_value
        brightness: float = float(config.attributes.fields["brightness"].number_value)
        pin: microcontroller.Pin = self.initialize_pin(pin_number)
        order: any = self.initialize_pixel_order(pixel_order)
        self.pixels = neopixel.NeoPixel(
            pin, num_pixels, brightness=brightness, auto_write=False, pixel_order=order
        )

        team_number: int = int(config.attributes.fields["team_number"].number_value)
        self.regenerate_animations()

        self.nt = ntcore.NetworkTableInstance.getDefault()
        self.connect(team_number)

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping nt-light-strip...")
        self.stop_thread()
        ntcore.NetworkTableInstance.destroy(self.nt)
