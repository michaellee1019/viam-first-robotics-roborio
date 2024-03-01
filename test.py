import asyncio

from viam.robot.client import RobotClient
from viam.components.movement_sensor import MovementSensor, Vector3, GeoPoint, Orientation
from viam.components.power_sensor import PowerSensor
from viam.components.sensor import Sensor
from viam.utils import sensor_readings_value_to_native, value_to_primitive, message_to_struct
from google.protobuf.json_format import MessageToDict
from google.protobuf.pyext._message import MessageMapContainer

def convert_to_dict(name, readings):
    if not isinstance(readings, dict):
        readings = sensor_readings_value_to_native(readings)
    for key, value in readings.items():
        match value:
            case Vector3():
                print(f"key: {key}, value_vector: {dict(x=value.x, y=value.y, z=value.z)}")
            case Orientation():
                print(f"key: {key}, value_orientation: {dict(o_x=value.o_x, o_y=value.o_y, o_z=value.o_z)}")
            case GeoPoint():
                print(f"key: {key}, value_geo: {dict(latitude=value.latitude, longitude=value.longitude)}")
            case _:
                print(f"key: {key}, value_prim: {value}")

def convert_to_primative(readings: any) -> dict:
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

def print_nt(name: str, readings_dict: dict) -> dict:
    for key, value in readings_dict.items():
        if isinstance(value, (bool, str, int, float, type(None))):
            print(f"{name}-{key}: {value}")
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                print(f"{name}-{key}-{subkey}: {subvalue}")


async def connect():
    opts = RobotClient.Options.with_api_key(
      api_key='7jzalxkwkemrpu8am8jsl3u59blf9ook',
      api_key_id='2a664e01-bae4-46e2-96dd-e5482755b1ef'
    )
    return await RobotClient.at_address('mac-main.f95uzv5arf.viam.cloud', opts)

async def main():
    robot = await connect()

    # fake_movement
    fake_movement = MovementSensor.from_robot(robot, "fake_movement")
    fake_movement_return_value = await fake_movement.get_readings()
    fake_movement_prim_readings = convert_to_primative(fake_movement_return_value)
    print_nt(fake_movement.name, fake_movement_prim_readings)
  
    # face_power
    face_power = PowerSensor.from_robot(robot, "face_power")
    face_power_return_value = await face_power.get_readings()
    fake_power_prim_readings = convert_to_primative(face_power_return_value)
    print_nt(face_power.name, fake_power_prim_readings)
  
    # fake_sensor
    fake_sensor = Sensor.from_robot(robot, "fake_sensor")
    fake_sensor_return_value = await fake_sensor.get_readings()
    fake_sensor_prim_readings = convert_to_primative(fake_sensor_return_value)
    print_nt(fake_sensor.name, fake_sensor_prim_readings)

    # Don't forget to close the machine when you're done!
    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())
