import json
import requests
import asyncio
import time
from networktables import NetworkTables

from typing import ClassVar, Mapping, Sequence

from typing_extensions import Self

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
from viam.service.generic import Generic
from viam import logging
# from viam.utils import sensor_readings_value_to_native

from threading import Thread
from threading import Event

import microcontroller
import board
import neopixel
from ntcore import NetworkTableInstance, NetworkTable, Event, EventFlags

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

# class RoborioNetworkTableSensorServer(Generic):
#     MODEL: ClassVar[Model] = Model.from_string("michaellee1019:roborio:nt-sensor-server")

#     nt = None
#     sensors = list()
#     thread = None
#     event = None

#     def thread_run(self):
#         loop = asyncio.get_event_loop()
#         loop.create_task(self.capture_images())

#     def start_thread(self):
#         self.thread = Thread(target=self.thread_run())
#         self.event = Event()
#         self.thread.start()

#     def stop_thread(self):
#         if self.thread is not None and self.event is not None:
#             self.event.set()
#             self.thread.join()

#     @classmethod
#     def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
#         nt_server = cls(config.name)
#         nt_server.reconfigure(config, dependencies)
#         return nt_server
    
#     async def capture_images(self):
#         while True:
#             if self.event.is_set():
#                 return
            
#             for (sensor_name, sensor_resource) in self.sensors:
#                 #try:
#                     readings = await sensor_resource.get_readings()
#                     readings_prim = sensor_readings_value_to_native(readings)
#                     LOGGER.error("readings type: {}".format(type(readings_prim)))
#                     LOGGER.error("readings: {}".format(str(readings_prim)))
#                     for reading_name, reading in readings.items():
#                         LOGGER.error("reading type: ", type(reading_prim))
#                         if isinstance(reading_prim, dict):
#                             for subreading_name, subreading in reading_prim:
#                                 LOGGER.error("subreading_name: ", subreading_name)
#                                 self.nt.putValue("{}-{}-{}".format(sensor_name, reading_name, subreading_name), subreading)
#                         else:
#                             LOGGER.error("reading_name: ", reading_name)
#                             self.nt.putValue("{}-{}".format(sensor_name, reading_name), reading_prim)
#                 #except Exception as e:
#                 #    LOGGER.error("failed to update network table: {}".format(e))
#                 #    continue
#                 #LOGGER.info("processed {} sensors.".format(len(self.sensors)))

#             time.sleep(5)

#     @classmethod
#     def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
#         if "team_number" not in config.attributes.fields:
#             raise Exception("A team_number attribute is required for nt-sensor-server component.")

#         if "address" not in config.attributes.fields:
#             raise Exception("A address attribute is required for nt-sensor-server component.")

#         return None
    
#     def reconfigure(self,
#                     config: ComponentConfig,
#                     dependencies: Mapping[ResourceName, ResourceBase]):
#         self.stop_thread()

#         self.sensors = dependencies.items()

#         # connect to a specific host/port
#         NetworkTables.initialize(server=config.attributes.fields["address"].string_value)
#         self.nt = NetworkTables.getTable("VIAM")

#         self.start_thread()

#     def __del__(self):
#         LOGGER.info("Stopping nt-sensor-server...")
#         self.stop_thread()
#         #ntcore.NetworkTableInstance.destroy(self.nt)

class RoborioNetworkTableLightStrip(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:roborio:nt-light-strip")

    # NetworkTable settings
    nt: NetworkTable = None
    pixels: neopixel.NeoPixel = None

    # Animation settings
    speed: float = 0.1
    colors: list(str)= [RED]
    tail_length: int = 1
    bounce: bool = False
    size: int = 1
    spacing: int = 1
    period: int = 1
    num_sparkles: int = 1
    step: int = 1

    # Animation configuration
    animation_name: str = 'blink'
    blink: Animation = Blink(pixels, speed=speed, color=colors[0])
    colorcycle: Animation = ColorCycle(pixels, speed=speed, colors=colors)
    comet: Animation = Comet(pixels, speed=speed, color=colors[0], tail_length=tail_length, bounce=bounce)
    chase: Animation = Chase(pixels, speed=speed, size=size, spacing=spacing, color=colors[0])
    pulse: Animation = Pulse(pixels, speed=speed, period=period, color=colors[0])
    sparkle: Animation = Sparkle(pixels, speed=speed, color=colors[0], num_sparkles=num_sparkles)
    solid: Animation = Solid(pixels, color=colors[0])
    rainbow: Animation = Rainbow(pixels, speed=speed, period=period)
    sparkle_pulse: Animation = SparklePulse(pixels, speed=speed, period=period, color=colors[0])
    rainbow_comet: Animation = RainbowComet(pixels, speed=speed, tail_length=tail_length, bounce=bounce)
    rainbow_chase: Animation = RainbowChase(pixels, speed=speed, size=size, spacing=spacing, step=step)
    rainbow_sparkle: Animation = RainbowSparkle(pixels, speed=speed, num_sparkles=num_sparkles)
    custom_color_chase: Animation = CustomColorChase(pixels, speed=speed, size=size, spacing=spacing, colors=colors)

    # Animation thread settings
    thread = None
    event = None

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.animate())

    def start_thread(self):
        self.thread = Thread(target=self.thread_run())
        self.event = Event()
        self.thread.start()

    def stop_thread(self):
        if self.thread is not None and self.event is not None:
            self.event.set()
            self.thread.join()

    async def animate(self):
        while True:
            if self.event.is_set():
                return
            
            animation = self.get_animation(self.annimation_name)
            animation.animate()
    
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
        self.inst.startClient4("ViamLightStrip")
        self.inst.setServerTeam(team_number)
        # TODO: Keep/Remove/Attribute? Works if not set.
        # self.inst.setServer("host", NetworkTableInstance.kDefaultPort4)
        table = self.inst.getTable("ViamLightStrip")
        table.addListener(EventFlags.kValueAll, self.update_state)

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
        num_pixels: int = config.attributes.fields["num_pixels"].number_value
        pixel_order: str = config.attributes.fields["pixel_order"].string_value
        brightness: float = config.attributes.fields["brightness"].float_value
        pin: microcontroller.Pin = self.initialize_pin(pin_number)
        order: any = self.initialize_pixel_order(pixel_order)
        self.pixels = neopixel.NeoPixel(
            pin, num_pixels, brightness=brightness, auto_write=False, pixel_order=order
        )

        team_number: int = config.attributes.fields["team_number"].number_value
        self.regenerate_animations()
        self.connect(team_number)

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping nt-light-strip...")
        self.stop_thread()
