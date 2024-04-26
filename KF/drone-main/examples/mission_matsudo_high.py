#!/usr/bin/env python3

import asyncio

from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

# latitude_start=47.398039859999997
# longitude_start=8.5455725400000002
# altitude_start=10

latitude_end=47.397825620791885
longitude_end=8.5450092830163271
altitude_end_hover=2

async def run():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))
    print_altitude_task = asyncio.ensure_future(print_altitude(drone))
    print_flight_mode_task = asyncio.ensure_future(print_flight_mode(drone))

    # running_tasks = [print_mission_progress_task]
    # termination_task = asyncio.ensure_future(
    #     observe_is_in_air(drone, running_tasks))

    mission_items = []
    # mission_items.append(MissionItem(latitude_start,
    #                                  longitude_start,
    #                                  altitude_start,
    #                                  0,
    #                                  False,
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  MissionItem.CameraAction.NONE,
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan')))
    
    mission_items.append(MissionItem(latitude_end,
                                     longitude_end,
                                     altitude_end_hover,
                                     0,
                                     False,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
                               
    
    mission_items.append(MissionItem(latitude_end,
                                     longitude_end,
                                     0.5,
                                     0,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(False)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()


    while True:
        await asyncio.sleep(1)
        mission_finished = await drone.mission.is_mission_finished()
        if mission_finished:
            break
        

    await drone.action.land()

    await asyncio.sleep(10)

    # await drone.action.land()

    # await termination_task


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")

async def print_altitude(drone):
    """ Prints the altitude when it changes """

    previous_altitude = 0.0

    async for position in drone.telemetry.position():
        altitude = position.relative_altitude_m
        if abs(previous_altitude - altitude) >= 0.1:
            previous_altitude = altitude
            print(f"Altitude: {altitude}")


async def print_flight_mode(drone):
    """ Prints the flight mode when it changes """

    previous_flight_mode = None

    async for flight_mode in drone.telemetry.flight_mode():
        if flight_mode != previous_flight_mode:
            previous_flight_mode = flight_mode
            print(f"Flight mode: {flight_mode}")



# async def observe_is_in_air(drone, running_tasks):
#     """ Monitors whether the drone is flying or not and
#     returns after landing """

#     was_in_air = False

    # async for is_in_air in drone.telemetry.in_air():
    #     if is_in_air:
    #         was_in_air = is_in_air

    #     if was_in_air and not is_in_air:
    #         for task in running_tasks:
    #             task.cancel()
    #             try:
    #                 await task
    #             except asyncio.CancelledError:
    #                 pass
    #         await asyncio.get_event_loop().shutdown_asyncgens()

    #         return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())