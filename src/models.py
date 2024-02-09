import json
import requests
import asyncio
import time
import ntcore

from typing import ClassVar, Mapping, Sequence

from typing_extensions import Self

from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model
from viam.components.generic import Generic
from viam import logging

from threading import Thread
from threading import Event

LOGGER = logging.getLogger(__name__)

class RoborioNetworkTableSensorServer(Generic):
    MODEL: ClassVar[Model] = Model.from_string("michaellee1019:roborio:nt-sensor-server")

    nt = None
    sensors = list()
    thread = None
    event = None

    def thread_run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.capture_images())

    def start_thread(self):
        self.thread = Thread(target=self.thread_run())
        self.event = Event()
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
    
    async def capture_images(self):
        while True:
            if self.event.is_set():
                return
            
            network_table = self.nt.getTable("VIAM")
            for sensor_name, sensor_resource in self.sensors:
                try:
                    readings = await sensor_resource.get_readings()
                    for reading_name, reading in readings:
                        network_table.putValue("{}-{}".format(sensor_name, reading_name), reading.value_to_primitive())
                except Exception as e:
                    LOGGER.error("failed to update network table: {}".format(e))
                    continue
                LOGGER.info("processed {} sensors.".format(len(self.sensors)))

            time.sleep(5)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        if "team_number" not in config.attributes.fields:
            raise Exception("A team_number attribute is required for nt-sensor-server component.")

        if "address" not in config.attributes.fields:
            raise Exception("A address attribute is required for nt-sensor-server component.")

        return None
    
    def reconfigure(self,
                    config: ComponentConfig,
                    dependencies: Mapping[ResourceName, ResourceBase]):
        self.nt = ntcore.NetworkTableInstance.getDefault()
        self.stop_thread()

        self.sensors = dependencies
        # start a NT4 client
        self.nt.startClient4("RoborioNetworkTableSensorServer")

        # connect to a roboRIO with team number TEAM
        self.nt.setServerTeam(config.attributes.fields["team_number"].string_value)

        # starting a DS client will try to get the roboRIO address from the DS application
        self.nt.startDSClient()

        # connect to a specific host/port
        self.nt.setServer(config.attributes.fields["address"].string_value, ntcore.NetworkTableInstance.kDefaultPort4)

        self.start_thread()

    def __del__(self):
        LOGGER.info("Stopping nt-sensor-server...")
        self.stop_thread()
        ntcore.NetworkTableInstance.destroy(self.nt)
