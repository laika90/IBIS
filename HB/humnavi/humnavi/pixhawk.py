import asyncio
from asyncio.log import logger
import datetime
import json
import os
import sys
import time
from geopy import distance

import mavsdk
import numpy as np
from mavsdk import server_utility
from humnavi.logger import logger_info, logger_debug

class Pixhawk:
    """Hummingbird control class for drone
    Variable Naming Rules: [meaning e.g.)velocity]_[unit e.g.) m_s]
    absolute altitude: altitude from the sea level
    relative altitude: altitude from the ground
    """

    def __init__(self):
        logger_info.info("Pixhawk initialized")
        # odometry
        self.x_m = 0.0
        self.y_m = 0.0
        self.z_m = 0.0
        # global position
        self.latitude_deg = 0.0
        self.longitude_deg = 0.0
        self.absolute_altitude_m = 0.0
        self.relative_altitude_m = 0.0
        # home positioin
        self.home_latitude_deg = 0.0
        self.home_longitude_deg = 0.0
        self.home_absolute_altitude_m = 0.0
        self.home_relative_altitude_m = 0.0

        # max velocity
        self.maximum_speed_m_s = 0.0

        # ned velocity
        self.north_m_s = 0.0
        self.east_m_s = 0.0
        self.down_m_s = 0.0
        # odometryvelocity
        self.x_m_s = 0.0
        self.y_m_s = 0.0
        self.z_m_s = 0.0
        # gps
        self.x_m_gps = 0.0
        self.y_m_gps = 0.0

        # angle
        self.pitch_deg = 0.0
        self.roll_deg = 0.0
        self.yaw_deg = 0.0

        # angular velocity
        self.pitch_rad_s = 0.0
        self.roll_rad_s = 0.0
        self.yaw_rad_s = 0.0
        # odometry angular velocity
        self.odometry_roll_rad_s = 0.0
        self.odometry_pitch_rad_s = 0.0
        self.odometry_yaw_rad_s = 0.0

        # lidar
        self.lidar = -1

        # control
        self.control_roll = 0.0
        self.control_pitch = 0.0
        self.control_yaw = 0.0

        # arm
        self.armed = False
        # in_air
        self.in_air = False
        self.is_landed = False
        self.land_detect = False
        # flight mode
        self.flight_mode = 0.0
        # rc
        self.rc_is_available = False
        self.rc_signal_strength_percent = 0.0
        # voltage
        self.voltage_v = 0.0
        self.remaining_percent = 0.0
        # gps
        self.num_satellites = 0.0
        self.fix_type = 0.0
        # check
        self.is_gyrometer_calibration_ok = 0.0
        self.is_accelerometer_calibration_ok = 0.0
        self.is_magnetometer_calibration_ok = 0.0
        self.is_level_calibration_ok = 0.0
        self.is_local_position_ok = 0.0
        self.is_global_position_ok = 0.0
        self.is_home_position_ok = 0.0
        self.is_health_all_ok = 0.0

        # status_text
        self.status_text = ""

        # time
        self.time = 0.0

        # target
        self.lng_target = None
        self.lat_target = None
        self.alt_target = None
        self.yaw_target = 0

        self.drone = mavsdk.System()
        self.is_detect = False
        self.detection_interval = 1

        self.LAT_1deg = 110940.5844  # at lat 35 deg
        self.LNG_1deg = 91287.7885  # at lat 35 deg

    async def connect(self, system_address: str) -> None:
        """connect pixhawk

        Args:
            system_address (str): system address
        """
        self.is_detect = False

        logger_info.info("Waiting for drone to connect...")
        await self.drone.connect(system_address=system_address)

        async for state in self.drone.core.connection_state():
            if state.is_connected:
                logger_info.info("Drone discovered!")
                break

    def gps_distance(self, lat1, lng1, lat2, lng2):
        lat_diff = (lat1 - lat2) * self.LAT_1deg
        lng_diff = (lng1 - lng2) * self.LNG_1deg
        dist = np.sqrt(lat_diff**2 + lng_diff**2)
        return dist
    
    def geopy_distance(self):
        target = (self.lat_target, self.lng_target)
        cur_pos = (self.latitude_deg, self.longitude_deg)
        return distance.distance(target, cur_pos).meters

    def is_dist_deg_ok(
        self, dest_lat, dest_lng, dist_thh=0.5, dest_yaw=None, deg_thh=10
    ):
        dist = self.gps_distance(
            self.latitude_deg, self.longitude_deg, dest_lat, dest_lng
        )
        if dest_yaw is None:
            logger_info.info("remaining dist: " + str(dist) + "m")
            return dist < dist_thh
        else:
            deg = abs(self.yaw_deg - dest_yaw)
            logger_info.info("remaining dist: " + str(dist) + "m yaw: " + str(deg) + "deg")
            return dist < dist_thh and deg < deg_thh

    def is_alt_ok(self, alt_land):
        if self.lidar > 8:
            logger_info.info("lidar is too high")
            return False
        else:
            logger_info.info("current alt: " + str(self.lidar))
            return self.lidar < alt_land

    # log
    async def get_lidar(self) -> None:
        async for current_distance_m in self.drone.telemetry.distance_sensor():
            self.lidar = (
                current_distance_m.current_distance_m
                / 100
                * np.cos(np.deg2rad(self.pitch_deg))
                * np.cos(np.deg2rad(self.roll_deg))
            )
            if self.lidar < 0:
                self.lidar = 0

    async def get_fake_lidar(self) -> None:
        self.lidar = self.relative_altitude_m

    async def get_attitude_angle(self) -> None:
        """get angle from sensors"""
        async for angle in self.drone.telemetry.attitude_euler():
            self.pitch_deg = angle.pitch_deg
            self.roll_deg = angle.roll_deg
            self.yaw_deg = angle.yaw_deg

    async def get_velocity_ned(self) -> None:
        """get velocity in north east coordinate from sensors"""
        async for velocity_ned in self.drone.telemetry.velocity_ned():
            self.north_m_s = velocity_ned.north_m_s
            self.east_m_s = velocity_ned.east_m_s
            self.down_m_s = velocity_ned.down_m_s

    async def get_attitude_angular_vel(self) -> None:
        """get angular velocity in deg/s from sensors"""
        async for angular_vel in self.drone.telemetry.attitude_angular_velocity_body():
            self.pitch_rad_s = angular_vel.pitch_rad_s
            self.roll_rad_s = angular_vel.roll_rad_s
            self.yaw_rad_s = angular_vel.yaw_rad_s

    async def get_position(self) -> None:
        """get gps position in (lat, lng, abusolute altitude, relative altitude)"""
        async for position in self.drone.telemetry.position():
            self.latitude_deg = position.latitude_deg
            self.longitude_deg = position.longitude_deg
            self.absolute_altitude_m = position.absolute_altitude_m
            self.relative_altitude_m = position.relative_altitude_m

    async def get_position_mean(self, i, position_dict) -> None:
        """get gps position in (lat, lng, abusolute altitude, relative altitude)"""
        async for position in self.drone.telemetry.position():
            if i == 0:
                position_dict["lat"] = [position.latitude_deg for _ in range(5)]
                position_dict["lng"] = [position.longitude_deg for _ in range(5)]
                position_dict["abs_alt"] = [
                    position.absolute_altitude_m for _ in range(5)
                ]
                position_dict["rel_alt"] = [
                    position.relative_altitude_m for _ in range(5)
                ]
            else:
                position_dict["lat"][i % 5] = position.latitude_deg
                position_dict["lng"][i % 5] = position.longitude_deg
                position_dict["abs_alt"][i % 5] = position.absolute_altitude_m
                position_dict["rel_alt"][i % 5] = position.relative_altitude_m

            self.latitude_deg = np.average(position_dict["lat"])
            self.longitude_deg = np.average(position_dict["lng"])
            self.absolute_altitude_m = np.average(position_dict["abs_alt"])
            self.relative_altitude_m = np.average(position_dict["rel_alt"])

    async def get_battery(self) -> None:
        """get battery voltage in V and remaining battery in percent"""
        async for battery in self.drone.telemetry.battery():
            self.voltage_v = battery.voltage_v
            self.remaining_percent = battery.remaining_percent

    async def get_gps_info(self) -> None:
        """get number of satellites and fix type"""
        async for gps_info in self.drone.telemetry.gps_info():
            self.num_satellites = gps_info.num_satellites
            self.fix_type = gps_info.fix_type

    async def get_flight_mode(self) -> None:
        """get flight mode"""
        async for flight_mode in self.drone.telemetry.flight_mode():
            self.flight_mode = flight_mode

    async def get_status_text(self) -> None:
        """get telemetry status"""
        async for status_text in self.drone.telemetry.status_text():
            self.status_text = status_text

    async def get_health(self) -> None:
        """get health of the vehicle"""
        async for health in self.drone.telemetry.health():
            # self.is_gyrometer_calibration_ok = health.is_gyrometer_calibration_ok
            # self.is_accelerometer_calibration_ok = (
            #     health.is_accelerometer_calibration_ok
            # )
            # self.is_magnetometer_calibration_ok = health.is_magnetometer_calibration_ok
            # self.is_level_calibration_ok = health.is_level_calibration_ok
            # self.is_local_position_ok = health.is_local_position_ok
            # self.is_global_position_ok = health.is_global_position_ok
            self.is_home_position_ok = health.is_home_position_ok

    async def get_actuator_control_target(self) -> None:
        """get actuator control target"""
        # TODO learn what is the example of actuator_control_target.controls
        async for actuator_control_target in self.drone.telemetry.actuator_control_target():
            self.control_roll = actuator_control_target.controls[0]
            self.control_pitch = actuator_control_target.controls[1]
            self.control_yaw = actuator_control_target.controls[2]

    async def get_home(self) -> None:
        """get home position in (lat, lng, absolute altitude, relative altitude)"""
        async for home in self.drone.telemetry.home():
            self.home_latitude_deg = home.latitude_deg
            self.home_longitude_deg = home.longitude_deg
            self.home_absolute_altitude_m = home.absolute_altitude_m
            self.home_relative_altitude_m = home.relative_altitude_m

    async def get_armed(self) -> None:
        """get armed"""
        async for armed in self.drone.telemetry.armed():
            self.armed = armed

    async def get_rc_status(self) -> None:
        """get rc status"""
        async for rc_status in self.drone.telemetry.rc_status():
            self.rc_is_available = rc_status.is_available
            self.rc_signal_strength_percent = rc_status.signal_strength_percent

    async def get_odometry(self) -> None:
        """get odometery"""
        async for odometry in self.drone.telemetry.odometry():
            self.x_m = odometry.position_body.x_m
            self.y_m = odometry.position_body.y_m
            self.z_m = odometry.position_body.z_m
            self.x_m_s = odometry.velocity_body.x_m_s
            self.y_m_s = odometry.velocity_body.y_m_s
            self.z_m_s = odometry.velocity_body.z_m_s
            self.odometry_roll_rad_s = odometry.angular_velocity_body.roll_rad_s
            self.odometry_pitch_rad_s = odometry.angular_velocity_body.pitch_rad_s
            self.odometry_yaw_rad_s = odometry.angular_velocity_body.yaw_rad_s

    async def get_health_all_ok(self) -> None:
        """get if health is all ok"""
        async for health_all_ok in self.drone.telemetry.health_all_ok():
            self.is_health_all_ok = health_all_ok

    async def get_unix_epoch_time(self) -> None:
        """get unix epoch time"""
        async for unix_epoch_time in self.drone.telemetry.unix_epoch_time():
            self.time = unix_epoch_time

    async def get_in_air(self) -> None:
        """get if the vehicle is in air"""
        async for in_air in self.drone.telemetry.in_air():
            self.in_air = in_air

    async def get_return_to_launch_after_mission(self) -> None:
        """get return to launch after mission"""
        async for return_to_launch_after_mission in self.drone.mission.get_return_to_launch_after_mission():
            self.return_to_launch_after_mission = return_to_launch_after_mission

    async def get_takeoff_altitude(self) -> None:
        """get takeoff altitude currenty set"""
        self.takeoff_altitude = await self.drone.action.get_takeoff_altitude()

    async def get_maximum_speed(self) -> None:
        """get maximum speed allowed in control"""
        self.maximum_speed_m_s = await self.drone.action.get_maximum_speed()

    async def send_status_text(self, msg: int) -> None:
        """
        msg: messageの種類
          * 1はINFO
          * 他にもALERTとかERRORとかある
        """
        msg_type = server_utility.StatusTextType(5)
        await self.drone.server_utility.send_status_text(msg_type, msg)

    async def upload_geofence(self, polygons) -> None:
        """
        Upload a geofence.

        Polygons are uploaded to a drone. Once uploaded, the geofence will remain
        on the drone even if a connection is lost.

        Parameters
        ----------
        polygons : [Polygon]
             Polygon(s) representing the geofence(s)

        Raises
        ------
        GeofenceError
            If the request fails. The error contains the reason for the failure.
        """
        # TODO learn how to set polygons (what coordinate is used? what unit is used?)
        logger_info.info("Uploading geofence...")
        await self.drone.geofence.upload_geofence(polygons)
        logger_info.info("Geofence uploaded!")

    async def download_logfile(self) -> None:
        """download logfile from pixhawk to raspberry pi"""
        logger_info.info("-- Entry logs")
        entries = await self.drone.log_files.get_entries()
        logger_info.info("-- Entried logs")
        entry = entries[-1]
        logger_info.info(str(entry))
        date_without_colon = entry.date.replace(":", "-")
        path = f"/home/hum-bird/log/flight_log/log-{date_without_colon}.ulg"
        logger_info.info(str(path))
        previous_progress = -1
        async for progress in self.drone.log_files.download_log_file(entry, path):
            new_progress = round(progress.progress * 100)
            if new_progress != previous_progress:
                sys.stdout.write(f"\r{new_progress} %")
                sys.stdout.flush()
                previous_progress = new_progress
        logger_info.info("-- Downloaded logfile")

    # tasks
    async def arm(self) -> None:
        """arm"""
        if str(self.flight_mode) == "TAKEOFF":
            logger_info.info("Flight mode is TAKEOFF.")
            return
        logger_info.info("--Arming")
        await self.drone.action.arm()

    async def disarm(self) -> None:
        """disarm"""
        logger_info.info("--Disarming")
        await self.drone.action.disarm()

    async def hold(self) -> None:
        """hold"""
        logger_info.info("--Holding")
        await self.drone.action.hold()

    async def takeoff(self) -> None:
        """takeoff"""
        logger_info.info("--Taking off")
        await self.drone.action.takeoff()

    async def land(self) -> None:
        """land"""
        logger_info.info("--Landing")
        await self.drone.action.land()

    async def reboot(self) -> None:
        """reboot"""
        logger_info.info("--Reboot")
        await self.drone.action.reboot()

    async def shutdown(self) -> None:
        """shutdown"""
        logger_info.info("--Shutdown")
        await self.drone.action.shutdown()

    async def kill(self) -> None:
        """kill"""
        logger_info.info("--Kill")
        await self.drone.action.kill()

    async def kill_async(self) -> None:
        """non_blocking kill"""
        logger_info.info("--kill_async")
        await self.drone.action.kill_async()

    async def return_to_launch(self) -> None:
        """return to launch site"""
        await self.drone.action.return_to_launch()

    async def offboard_start(self) -> None:
        """start offboard mode"""
        logger_info.info("-- Starting offboard")
        try:
            await self.drone.offboard.start()
        except mavsdk.offboard.OffboardError as error:
            print(
                f"Starting offboard mode failed with error code: {error._result.result}"
            )
            await self.drone.action.disarm()
            return

    async def offboard_stop(self) -> None:
        """stop offboard mode"""
        try:
            await self.drone.offboard.stop()
        except mavsdk.offboard.OffboardError as error:
            print(
                f"Stopping offboard mode failed with error code: \
                {error._result.result}"
            )

    async def offboard_set_attitude(
        self, thrust=0.6, roll=0.0, pitch=0.0, yaw=0.0
    ) -> None:
        """set attitude for offboard

        Args:
            thrust (float, optional): thurst (0~1). Defaults to 0.6.
            roll (float, optional): roll in deg. Defaults to 0.
            pitch (float, optional): pitch in deg. Defaults to 0.
            yaw (float, optional): yaw in deg. Defaults to 0.
        """
        await self.drone.offboard.set_attitude(
            mavsdk.offboard.Attitude(roll, pitch, yaw, thrust)
        )

    async def offboard_set_position_ned(
        self, north_m=0.0, east_m=0.0, down_m=0.0, yaw_deg=0.0
    ) -> None:
        """set position in north east coordinate

        Args:
            north_m (float, optional): north in meter. Defaults to 0.
            east_m (float, optional): east in meter. Defaults to 0.
            down_m (float, optional): down in meter. Defaults to 0.
            yaw_deg (float, optional): yaw in deg. Defaults to 0.
        """
        await self.drone.offboard.set_position_ned(
            mavsdk.offboard.PositionNedYaw(north_m, east_m, down_m, yaw_deg)
        )

    async def offboard_set_velocity_body(
        self, forward_m_s=0.0, right_m_s=0.0, down_m_s=0.0, yawspeed_deg_s=0.0
    ) -> None:
        """set velocity for the vehicle for offboard mode

        Args:
            forward_m_s (float, optional): forward speed in m/s. Defaults to 0..
            right_m_s (float, optional): right speed in m/s. Defaults to 0..
            down_m_s (float, optional): down speed in m/s. Defaults to 0..
            yawspeed_deg_s (float, optional): yaw speed in deg/s. Defaults to 0..
        """
        await self.drone.offboard.set_velocity_body(
            mavsdk.offboard.VelocityBodyYawspeed(
                forward_m_s, right_m_s, down_m_s, yawspeed_deg_s
            )
        )

    async def offboard_set_velocity_ned(
        self, north_m_s=0.0, east_m_s=0.0, down_m_s=0.0, yaw_deg=0.0
    ) -> None:
        """set velocity in north east coordinate

        Args:
            north_m_s (float, optional): velocity to north in m/s. Defaults to 0..
            east_m_s (float, optional): velocity to east in m/s. Defaults to 0..
            down_m_s (float, optional): velocity to down in m/s. Defaults to 0..
            yaw_deg (float, optional): velocity yaw in deg/s. Defaults to 0..
        """
        await self.drone.offboard.set_velocity_ned(
            mavsdk.offboard.VelocityNedYaw(north_m_s, east_m_s, down_m_s, yaw_deg)
        )

    async def goto_location(
        self,
        latitude_deg: float,
        longitude_deg: float,
        absolute_altitude_m: float,
        yaw_deg: float,
    ) -> None:
        """go to the input location

        Args:
            latitude_deg (float): latitude in deg
            longitude_deg (float): longitude in deg
            absolute_altitude_m (float): absolute altitude in meter
            yaw_deg (float): yaw in deg
        """
        logger_info.info(
            "--Go to location to lat: "
            + str(latitude_deg)
            + " lng:"
            + str(longitude_deg)
            + " alt:"
            + str(absolute_altitude_m)
            + " yaw:"
            + str(yaw_deg)
        )
        await self.drone.action.goto_location(
            latitude_deg, longitude_deg, absolute_altitude_m, yaw_deg
        )

    async def task_transition_from_arm_to_goto(self, conf):
        logger_info.info("arms opened!")
        await asyncio.sleep(conf.deploy_arm_s)
        try:
            await self.arm()
        except mavsdk.action.ActionError:
            logger_info.info("arm ActionError")
            await asyncio.sleep(0.01)
        await asyncio.sleep(conf.arm_takeoff_s)
        while not str(self.flight_mode) == "TAKEOFF":
            try:
                await self.takeoff()
            except mavsdk.action.ActionError:
                logger_info.info("takeoff ActionError")
                await asyncio.sleep(0.01)
        await asyncio.sleep(conf.takeoff_goto_s)
        start_goto_time = time.time()
        while True:
            target = (self.lat_target, self.lng_target)
            cur_pos = (self.latitude_deg, self.longitude_deg)
            remaining_dist = distance.distance(target, cur_pos).meters
            recovery_target_abs_alt_m = max(10, self.absolute_altitude_m + conf.recovery_tan * remaining_dist)
            logger_info.info("recovery_target_abs_alt: " + str(recovery_target_abs_alt_m) + "m")
            try:
                await self.goto_location(self.lat_target, self.lng_target, recovery_target_abs_alt_m, 0)
            except mavsdk.action.ActionError:
                logger_info.info("goto Action Error")
                await asyncio.sleep(0.01)
            if time.time() - start_goto_time > conf.recovery_time_s:
                start_hold_time = time.time()
                while time.time() - start_hold_time < conf.hold_time_s:
                    try:
                        await self.goto_location(self.lat_target, self.lng_target, self.absolute_altitude_m, 0)
                    except mavsdk.action.ActionError:
                        logger_info.info("goto ActionError")
                    await asyncio.sleep(0.1)
                logger_info.info("recovery end")
                return
            else:
                logger_info.info("recovering from freefall...")
                await asyncio.sleep(0.1)

    # separated goto_location
    async def task_goto_location_without_set_target(self, conf):
        """goto location without setting target.

        Args:
            time_limit (float): time limit for goto
        """
        start_time = time.time()
        try:
            await self.set_current_speed(conf.max_cruise_speed_m_s)
        except mavsdk.action.ActionError:
            logger_info.info("set current speed Action Error")
            await asyncio.sleep(0.01)
        while True:
            if time.time() - start_time > conf.time_limit_goto_s:
                logger_info.info("time's up")
                self.abort_goto_land = True
                return
            if self.lidar < 8 and self.lidar > 0:
                logger_info.info("lidar_on")
                self.abs_alt_target = self.absolute_altitude_m - self.lidar + self.alt_target
            try:
                await self.goto_location(
                    self.lat_target,
                    self.lng_target,
                    self.abs_alt_target,
                    0,
                )
            except mavsdk.action.ActionError:
                logger_info.info("goto Action Error")
            target = (self.lat_target, self.lng_target)
            cur_pos = (self.latitude_deg, self.longitude_deg)
            remaining_dist = distance.distance(target, cur_pos).meters
            if remaining_dist < conf.goto_end_threshold_m:
                logger_info.info("reached the target!")
                return
            else:
                logger_info.info("heading for target...")
            await asyncio.sleep(0.1)

    def set_target_from_dict(self, location_dict, target_name):
        target_pos = location_dict[target_name]
        self.lat_target = target_pos[0]
        self.lng_target = target_pos[1]
        self.abs_alt_target = target_pos[2]
        self.alt_target = target_pos[4]
    
    async def task_goto_location(
        self,
        location_dict: dict,
        target_name: str,
        time_limit: float,
    ):
        """run goto location until mission name


        Args:
            location_dict (dict): location dict
            target_name (str): target name
            time_limit (float): time limit for goto
        """
        target_pos = location_dict[target_name]
        self.lat_target = target_pos[0]
        self.lng_target = target_pos[1]
        self.abs_alt_target = target_pos[2]
        self.alt_target = target_pos[4]
        start_time = time.time()

        while self.geopy_distance() > 0.5:
            if time.time() - start_time > time_limit:
                self.abort_goto_land = True
                logger_info.info("time's up")
                return
            else:
                try:
                    if self.lidar < 8 and self.lidar > 0:
                        await self.goto_location(
                            self.lat_target,
                            self.lng_target,
                            self.absolute_altitude_m - self.lidar + self.alt_target,
                            0,
                        )
                        logger_info.info("lidar: on")
                        logger_info.info("target_abs_alt:" + str(self.absolute_altitude_m - self.lidar + self.alt_target))
                    else:
                        await self.goto_location(
                            self.lat_target,
                            self.lng_target,
                            self.abs_alt_target,
                            0,
                        )
                        logger_info.info("target_abs_alt:" + str(self.abs_alt_target))
                except mavsdk.action.ActionError:
                    logger_info.info("Action Error")
            await asyncio.sleep(0.1)
        logger_info.info("reached the target!")
        return

    async def task_kill_forever(self):
        self.land_detect = False
        while True:
            await self.kill()
            await asyncio.sleep(0.1)

    async def task_goto_land(self, land_time_limit: float, alt_land=0.1) -> None:
        """goto land

        Args:
            land_time_limit (float): time limit for landing sequence
            alt_land (float, optional): altitude to move on to land mode. Defaults to 0.1.
            0.55 = 25cm / tan(24.4 deg) altitude where target sheet covers most of view field
        """
        logger_info.info("goto land start")

        if self.lat_target is None:
            self.lat_target = self.latitude_deg
            self.lng_target = self.longitude_deg
        start_time = time.time()

        check_interval = 0.1
        set_interval = 1
        is_time_up = False

        self.is_detect = True
        self.land_detect = True

        if self.alt_target == None or self.alt_target > 8:
            self.alt_target = 8

        timeout_time = land_time_limit
        pixhawk_goto_land_start_time = time.time()

        while self.lidar > 8:
            logger_info.info("alt_target:" + str(self.alt_target))
            if self.is_detect == False:
                return
            await self.goto_location(
                self.lat_target,
                self.lng_target,
                self.absolute_altitude_m - 0.5,
                self.yaw_target,
            )
            await asyncio.sleep(0.7)
        try:
            await self.set_current_speed(3)
        except mavsdk.action.ActionError:
            logger_info.info("set current speed ActionError")
            await asyncio.sleep(0.01)
        while not (
            self.is_alt_ok(1.5)
            and self.geopy_distance() < 0.5
        ):
            if self.is_detect == False:
                return
            if self.is_landed:
                return
            logger_info.info("alt_target:" + str(self.alt_target))
            if time.time() - start_time > set_interval and self.lidar < 8:
                start_time = time.time()
                if self.alt_target > 1.4:
                    self.alt_target -= 0.4
                if self.lidar > 1.5:
                    await self.goto_location(
                        self.lat_target,
                        self.lng_target,
                        self.absolute_altitude_m - self.lidar + self.alt_target,
                        self.yaw_target,
                    )
                    self.alt_target -= 0.4
            if time.time() - pixhawk_goto_land_start_time > timeout_time:
                logger_info.info("time's up")
                is_time_up = True
                break
            await asyncio.sleep(check_interval)
        try:
            await self.set_current_speed(1)
        except mavsdk.action.ActionError:
            logger_info.info("set current speed ActionError")
            await asyncio.sleep(0.01)
        while not (
            self.is_alt_ok(alt_land)
            and self.geopy_distance < 0.05
        ):
            if self.is_detect == False:
                return
            if self.is_landed:
                return
            logger_info.info("alt_target:" + str(self.alt_target))
            if time.time() - start_time > set_interval and self.lidar < 8:
                start_time = time.time()
                if self.lidar > alt_land + 0.2:
                    self.alt_target -= 0.1
                elif self.lidar <= alt_land:
                    self.alt_target += 0.1
                elif self.lidar <= alt_land + 0.2:
                    self.alt_target -= 0.05
                await self.goto_location(
                    self.lat_target,
                    self.lng_target,
                    self.absolute_altitude_m - self.lidar + self.alt_target,
                    self.yaw_target,
                )
            if time.time() - pixhawk_goto_land_start_time > timeout_time:
                logger_info.info("time's up")
                is_time_up = True
                break
            await asyncio.sleep(check_interval)

        if not is_time_up:
            logger_info.info("reached the target!")
        logger_info.info("detection finish")
        self.is_detect = False
        logger_info.info("goto land finish")
        return

    async def task_do_orbit(self, conf):
        self.land_detect = True
        self.abs_alt_target = self.absolute_altitude_m - self.lidar + conf.orbit_altitude
        while abs(conf.orbit_altitude - self.lidar) > 0.5:
            await self.goto_location(self.lat_target, self.lng_target, self.abs_alt_target, 0)
        radius_list = [5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5]
        for radius_m in radius_list:
            if self.land_detect == False:
                break
            print("start orbit in", radius_m)
            for _ in range(50):
                try:
                    await self.drone.action.do_orbit(radius_m, conf.orbit_velocity_m_s, mavsdk.action.OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER, self.lat_target, self.lng_target, self.abs_alt_target)
                    await asyncio.sleep(0.1)
                except mavsdk.action.ActionError:
                    logger_info.info("do_orbit ActionError moving onto the next radius...")
                    await asyncio.sleep(0.01)
        if self.land_detect:
            await self.goto_location(self.lat_target, self.lng_target, self.abs_alt_target, 0)
            await asyncio.sleep(5)
            return
    
    async def task_land(self):
        self.land_detect = True
        while True:
            if str(self.flight_mode) != "LAND":
                try:
                    await self.land()
                except mavsdk.action.ActionError:
                    logger_info.info("land ActionError")
                    await asyncio.sleep(0.1)
            else:
                break
    
    async def task_goto_land_without_detection(self, conf):
        logger_info.info("task goto land without detection has started.")
        if self.lidar < 8 and self.lidar > 0:
            self.abs_alt_target = self.absolute_altitude_m - self.lidar + conf.land_alt_m
        try:
            await self.goto_location(self.lat_target, self.lng_target, self.abs_alt_target, 0)
            await asyncio.sleep(conf.final_goto_duration_s)
        except mavsdk.action.ActionError:
            await asyncio.sleep(0.01)
        return

    async def task_hold_wait(self):
        while str(self.flight_mode) != "HOLD":
            try:
                await self.hold()
            except mavsdk.action.ActionError:
                logger_info.info("hold ActionError")
                await asyncio.sleep(0.01)

    async def cycle_hold_wait(self, light):
        while True:
            if light.is_armopen == False:
                while str(self.flight_mode) != "HOLD":
                    try:
                        await self.hold()
                    except mavsdk.action.ActionError:
                        logger_info.info("hold ActionError")
                        await asyncio.sleep(0.01)
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

    async def wait_arm_open(self, light):
        while light.is_armopen == False:
            await asyncio.sleep(0.01)

    # cycle
    async def cycle_gps_info(self) -> None:
        while True:
            await self.get_gps_info()
            await asyncio.sleep(0.1)

    async def cycle_odometry(self) -> None:
        while True:
            await self.get_odometry()
            await asyncio.sleep(0.01)

    async def cycle_is_landed(self) -> None:
        while True:
            if self.land_detect:
                if float(self.lidar) < 0.10 and float(self.lidar) > 0 and self.is_detect == False:
                    await self.land()
                    await asyncio.sleep(3)
                    await self.task_kill_forever()
                elif abs(float(self.roll_deg)) > 60 or abs(float(self.pitch_deg)) > 60:
                    if self.armed:
                        logger_info.info("hit the target!")
                        await self.task_kill_forever()
                await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.01)
    
    async def cycle_is_landed_deg_only(self) -> None:
        while True:
            if self.land_detect:
                if abs(float(self.roll_deg)) > 60 or abs(float(self.pitch_deg)) > 60:
                    if self.armed:
                        logger_info.info("hit the target!")
                        await self.task_kill_forever()
                else:
                    await asyncio.sleep(0.01)
            else:
                await asyncio.sleep(0.01)
    
    async def cycle_health(self) -> None:
        while True:
            await self.get_health()
            await asyncio.sleep(0.1)

    async def cycle_in_air(self) -> None:
        while True:
            await self.get_in_air()
            await asyncio.sleep(0.1)

    async def cycle_position_mean(self) -> None:
        i = 0
        position_dict = {}
        position_dict["lat"] = []
        position_dict["lng"] = []
        position_dict["abs_alt"] = []
        position_dict["rel_alt"] = []
        while True:
            await self.get_position_mean(i, position_dict)
            await asyncio.sleep(0.01)

    async def cycle_gps_position(self) -> None:
        while True:
            await self.get_position()
            await asyncio.sleep(0.01)

    async def cycle_relative_position(self) -> None:
        """
        LAT_1deg (float): length of 1 deg of latitude in m
        LAT_1deg = PI() * R / 180  R: radius of Earth
        LNG_1deg (float): length of 1 deg of longitude in m = LAT_1deg * cos(latitude)
        """
        while True:
            LAT_1deg = 110360
            LNG_1deg = 90187
            self.x_m_gps, self.y_m_gps = (
                self.longitude_deg - self.home_longitude_deg
            ) * LNG_1deg, (self.latitude_deg - self.home_latitude_deg) * LAT_1deg
            await asyncio.sleep(0.1)

    async def cycle_attitude(self):
        while True:
            await self.get_attitude_angle()
            await asyncio.sleep(0.01)

    async def cycle_lidar(self):
        """get lidar once a five cycles
        pre_lider (float): previous lidar value in m
        count (int): keep the number of iterations in five cycles
        """
        while True:
            await self.get_lidar()
            await asyncio.sleep(0.01)


    async def cycle_fake_lidar(self):
        while True:
            await self.get_fake_lidar()
            await asyncio.sleep(0.01)

    async def cycle_flight_mode(self):
        while True:
            await self.get_flight_mode()
            await asyncio.sleep(0.01)

    async def cycle_armed(self):
        while True:
            await self.get_armed()
            await asyncio.sleep(0.01)

    async def cycle_status_text(self):
        while True:
            await self.get_status_text()
            logger_info.info(str(self.status_text))
            await asyncio.sleep(0.1)

    async def cycle_time(self):
        while True:
            await self.get_unix_epoch_time()
            await asyncio.sleep(0.1)
    
    async def cycle_maximum_speed(self):
        while True:
            await self.get_maximum_speed()
            await asyncio.sleep(0.1)

    async def cycle_show(self):
        while True:
            log_txt = (
                "armed:"
                + str(self.armed)
                + " mode:"
                + str(self.flight_mode)
                + " satellite: "
                + str(self.num_satellites)
                + " abs_alt:"
                + str(self.absolute_altitude_m)
                + " lidar: "
                + str(self.lidar)
                + "m"
                + " x:"
                + str(self.x_m)
                + " y:"
                + str(self.y_m)
                + " roll:"
                + str(self.roll_deg)
                + " pitch:"
                + str(self.pitch_deg)
                + " yaw:"
                + str(self.yaw_deg)
                + " is_landed:"
                + str(self.is_landed)
                + " is home position ok:"
                + str(self.is_home_position_ok)
                + " maximum_speed:"
                + str(self.maximum_speed_m_s)
            )
            logger_info.info(str(log_txt))
            await asyncio.sleep(0.3)

    async def cycle_record_log(self) -> None:
        """record log to a json file"""
        log_file = self.create_log_file()
        log_dict = {}
        log_dict["mode"] = []
        log_dict["lat_deg"] = []
        log_dict["lng_deg"] = []
        log_dict["abs_alt_m"] = []
        log_dict["rel_alt_m"] = []
        log_dict["x_m"] = []
        log_dict["y_m"] = []
        log_dict["pitch_deg"] = []
        log_dict["roll_deg"] = []
        log_dict["yaw_deg"] = []
        log_dict["lidar"] = []
        log_dict["target point"] = []
        log_dict["unix time"] = []
        while True:
            log_dict["mode"].append(str(self.flight_mode))
            log_dict["lat_deg"].append(self.latitude_deg)
            log_dict["lng_deg"].append(self.longitude_deg)
            log_dict["abs_alt_m"].append(self.absolute_altitude_m)
            log_dict["rel_alt_m"].append(self.relative_altitude_m)
            log_dict["x_m"].append(self.x_m)
            log_dict["y_m"].append(self.y_m)
            log_dict["pitch_deg"].append(self.pitch_deg)
            log_dict["roll_deg"].append(self.roll_deg)
            log_dict["yaw_deg"].append(self.yaw_deg)
            log_dict["lidar"].append(self.lidar)
            log_dict["target point"].append(
                [self.lat_target, self.lng_target, self.alt_target]
            )
            log_dict["unix time"].append(self.time)
            with open(log_file, mode="w") as f:
                json.dump(log_dict, f)
            await asyncio.sleep(0.5)

    async def cycle_arliss_log(self) -> None:
        """record log to a json file"""
        log_file = self.create_log_file()
        log_dict = {}
        log_dict["lat_deg"] = []
        log_dict["lng_deg"] = []
        log_dict["rel_alt_m"] = []
        log_dict["lidar"] = []
        log_dict["target point"] = []
        log_dict["unix time"] = []
        while True:
            log_dict["lat_deg"].append(self.latitude_deg)
            log_dict["lng_deg"].append(self.longitude_deg)
            log_dict["rel_alt_m"].append(self.relative_altitude_m)
            log_dict["lidar"].append(self.lidar)
            log_dict["target point"].append(
                [self.lat_target, self.lng_target, self.alt_target]
            )
            log_dict["unix time"].append(self.time)
            with open(log_file, mode="w") as f:
                json.dump(log_dict, f)
            await asyncio.sleep(0.5)

    # configs
    async def set_maximum_speed(self, maximum_speed_m_s: float) -> None:
        """set maximum velocity in m/s

        Args:
            maximum_speed_m_s (float): max velocity [m/s]
        """
        self.maximum_speed_m_s = maximum_speed_m_s
        logger_info.info("set maximum speed to:" + str(maximum_speed_m_s))
        await self.drone.action.set_maximum_speed(maximum_speed_m_s)

    async def set_current_speed(self, current_speed_m_s: float) -> None:
        logger_info.info("set current speed to:" + str(current_speed_m_s))
        await self.drone.action.set_current_speed(current_speed_m_s)

    async def set_takeoff_altitude(self, takeoff_altitude: float) -> None:
        """set takeoff altitude in m

        Args:
            takeoff_altitude (float): takeoff altitude [m]
        """
        self.takeoff_altitude = takeoff_altitude
        await self.drone.action.set_takeoff_altitude(takeoff_altitude)

    async def set_target(self, lat: float, lng: float, alt: float, yaw: float) -> None:
        """set the target location

        Args:
            lat (float): latitude in deg
            lng (float): longitude in deg
            alt (float): altitude in m
            yaw (float): yaw angle in deg
        """
        self.lat_target = lat
        self.lng_target = lng
        self.alt_target = alt
        self.yaw_target = yaw
        logger_info.info(
            "set target lat: "
            + str(lat)
            + ", lng: "
            + str(lng)
            + ", alt: "
            + str(alt)
            + ", yaw: "
            + str(yaw)
        )

    def create_log_file(self):
        LOG_DIR = os.path.abspath("log")
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        log_path = LOG_DIR + "/" + str(datetime.date.today())
        i = 0
        while True:
            log_file = log_path + "/" + str(i).zfill(3) + ".json"
            if os.path.exists(log_file):
                logger_info.info(str(log_file) + " already exists")
                i += 1
                continue
            else:
                try:
                    with open(log_file, mode="w"):
                        pass
                except FileNotFoundError:
                    os.mkdir(log_path)
                    with open(log_file, mode="w"):
                        pass
                return str(log_file)
