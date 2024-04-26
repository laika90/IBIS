#!/usr/bin/env python3

import asyncio
from mavsdk import System
from logger import logger_info, logger_debug

altitude = 2.5
land_alt = 0.4
mode = None

async def run():
    """
    This is the "main" function.
    It first creates the drone object and initializes it.

    Then it registers tasks to be run in parallel (one can think of them as
    threads):
        - print_altitude: print the altitude
        - print_flight_mode: print the flight mode
        - observe_is_in_air: this monitors the flight mode and returns when the
                             drone has been in air and is back on the ground.

    Finally, it goes to the actual works: arm the drone, initiate a takeoff
    and finally land.

    Note that "observe_is_in_air" is not necessary, but it ensures that the
    script waits until the drone is actually landed, so that we receive
    feedback during the landing as well.
    """

    # Init the drone
    drone = System()

    # cycle_log_task = asyncio.ensure_future(cycle_log(drone))
    # await cycle_log_task
    print("Waiting for drone to connect...")
    # await drone.connect(system_address="udp://:14540")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    
    logger_info.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            logger_info.info("-- Connected to drone!")
            break

    print("waiting for pixhawk to hold")
    
    # hold_mode = False #MAVSDKではTrueって出るけどFalseが出ない場合もあるから最初からFalseにしてる
    # while True:
    #    if hold_mode==True:
    #        break
    #    async for flight_mode in drone.telemetry.flight_mode():
    #        if str(flight_mode) == "HOLD":
    #            print("hold checked")
    #            hold_mode=True
    #            break
    #        else:
    #            try:
    #                await drone.action.hold() #holdじゃない状態からholdしようてしても無理だからもう一回exceptで繋ぎなおす
    #            except Exception as e:
    #                print(e)
    #                drone = System()
    #                await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    #                print("Waiting for drone to connect...")
    #                async for state in drone.core.connection_state():

    #                     if state.is_connected:
                            
    #                         print(f"-- Connected to drone!")
    #                         break

    # Start parallel tasks
    print_altitude_task = asyncio.create_task(print_altitude(drone))
    print_flight_mode_task = asyncio.create_task(print_flight_mode(drone))
    arm_takeoff_task = asyncio.create_task(arm_takeoff(drone))
    await print_altitude_task
    await print_flight_mode_task
    # termination_task = asyncio.ensure_future(observe_is_in_air(drone, print_altitude_task))

    await arm_takeoff_task
    


    # async for health in drone.telemetry.health():
    #     if health.is_global_position_ok and health.is_home_position_ok:
    #         print("-- Global position state is good enough for flying.")
    #         break


    # Execute the maneuvers

async def arm_takeoff(drone):
    print("-- Arming")
    logger_info.info("-- Arming")
    await drone.action.arm()
    print("-- Armed")
    logger_info.info("-- Armed")
    print("-- Taking off")
    logger_info.info("-- Taking off")
    await drone.action.set_takeoff_altitude(altitude)
    await drone.action.takeoff()

    await asyncio.sleep(20)

    print("-- Landing")
    logger_info.info("-- Landing")
    await drone.action.land()

    # Wait until the drone is landed (instead of exiting after 'land' is sent)
    # await termination_task


async def print_altitude(drone):
    """ Prints the altitude when it changes """

    previous_altitude = 0.0
    
    async for distance in drone.telemetry.distance_sensor():
        # mode = drone.telemetry.flight_mode()
        altitude_now = distance.current_distance_m
        print("difference : {}".format(altitude_now - previous_altitude))
        if abs(previous_altitude - altitude_now) >= 0.1:
            previous_altitude = altitude_now
            print(f"Altitude: {altitude_now}")

            logger_info.info(f"mode:{mode} lidar:{altitude_now}m")
       
        if altitude_now > land_alt:
            print("over {}".format(land_alt))
            await drone.action.land()


async def print_flight_mode(drone):
    """ Prints the flight mode when it changes """

    # previous_flight_mode = None
    

    async for flight_mode in drone.telemetry.flight_mode():
        mode = flight_mode
        # if flight_mode != previous_flight_mode:
        #     previous_flight_mode = flight_mode
        #     print(f"Flight mode: {flight_mode}")
            # break
            

# logがループに入ってなかったら
# async def cycle_log(drone):
#     mode = None
#     height = None
#     while True:   
#         async for flight_mode in drone.telemetry.flight_mode():
#             mode = flight_mode
#         async for distance in drone.telemetry.distance_sensor:
#             height = distance.current_distance_m

#         logger_info.info(f"mode:{mode} lidar:{height}m ")

        # logが一生終わらなくてウザかったら
        # if mode == 6 :
        #     await asyncio.sleep(10)
        #     break


# async def observe_altitude(drone, running_task):
#     """ Monitors whether the drone is flying or not and
#     returns after landing """

#     was_in_air = False

#     async for is_in_air in drone.telemetry.in_air():
#         if is_in_air:
#             was_in_air = is_in_air

#         if was_in_air and not is_in_air:
#             for task in running_tasks:
#                 task.cancel()
#                 try:
#                     await task
#                 except asyncio.CancelledError:
#                     pass
#             await asyncio.get_event_loop().shutdown_asyncgens()
#             return


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
