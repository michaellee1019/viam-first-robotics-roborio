import asyncio
import sys
from viam import logging

LOGGER = logging.getLogger(__name__)
sys.path.append("..")

from viam.module.module import Module
from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.components.generic import Generic

from models import RoborioNetworkTableLightStrip

# Registry.register_resource_creator(Generic.SUBTYPE, RoborioNetworkTableSensorServer.MODEL, ResourceCreatorRegistration(RoborioNetworkTableSensorServer.new, RoborioNetworkTableSensorServer.validate_config))
Registry.register_resource_creator(Generic.SUBTYPE, RoborioNetworkTableLightStrip.MODEL, ResourceCreatorRegistration(RoborioNetworkTableLightStrip.new, RoborioNetworkTableLightStrip.validate_config))

async def main():
    LOGGER.info("Starting first-robotics-roborio module...")
    module = Module.from_args()

    # module.add_model_from_registry(Generic.SUBTYPE, RoborioNetworkTableSensorServer.MODEL)
    module.add_model_from_registry(Generic.SUBTYPE, RoborioNetworkTableLightStrip.MODEL)
    await module.start()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Need socket path as command line argument")

    asyncio.run(main())