#!/usr/bin/env python3

from math import copysign
from time import time
from threading import Lock
from typing import Tuple

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from std_srvs.srv import SetBool, SetBoolRequest, SetBoolResponse

from xbox_controller import XboxController

### helpers ##################################################################

deadzone = 0.01

def clamp(value: float, lower: float, upper: float) -> float:
	return min(upper, max(value, lower))

### main #####################################################################

def main():
	GamepadInput().loop()

class GamepadInput:
	def __init__(self):

		rospy.init_node("gamepad_input")

		### local variables ##################################################

		self.timeout = rospy.get_param("~timeout")
		self.turbo_multiplier = rospy.get_param("~turbo_multiplier")
		self.base_multiplier = rospy.get_param("~base_multiplier")

		self.min_linear_speed = rospy.get_param("~min_linear_speed")
		self.max_linear_speed = rospy.get_param("~max_linear_speed")
		self.min_angular_speed = rospy.get_param("~min_angular_speed")
		self.max_angular_speed = rospy.get_param("~max_angular_speed")

		self.enabled = rospy.get_param("~enabled_on_start")  # whether or not to publish cmd_vel
		self.enabled_lock = Lock()

		self.last_tick = 0.0  # remember last time joy message was received
		self.tick_lock = Lock()

		self.drive_direction_correction = 1
		self.drive_direction_correction_lock = Lock()

		self.car_style_turning = False
		self.car_style_turning_lock = Lock()

		### connect to ROS ###################################################

		joy_topic = rospy.get_param("~joy_topic")
		cmd_vel_topic = rospy.get_param("~cmd_vel_topic")
		selected_mode_topic = rospy.get_param("~selected_mode_topic")
		enabled_service = rospy.get_param("~enabled_service")
		drive_forward_service = rospy.get_param("~drive_forward_service")
		car_style_turning_service = rospy.get_param("~car_style_turning_service")

		self.joy_sub = rospy.Subscriber(joy_topic, Joy, self.joy_sub_callback)
		self.cmd_vel_pub = rospy.Publisher(cmd_vel_topic, Twist, queue_size=1)
		self.selected_mode_pub = rospy.Publisher(selected_mode_topic, String, queue_size=1)
		self.enabled_srv = rospy.Service(enabled_service, SetBool, self.enabled_callback)
		self.drive_forward_srv = rospy.Service(drive_forward_service, SetBool, self.drive_direction_callback)
		self.turning_style_srv = rospy.Service(car_style_turning_service, SetBool, self.turning_style_callback)

		### end init #########################################################

	### local functions ######################################################

	def normal_drive(self, xbox: XboxController) -> Tuple[float]:
		x, y, z = -xbox.left_stick_x, xbox.left_stick_y, xbox.right_stick_y

		# get rid of -0 problem
		if (abs(x) < deadzone): x = 0
		if (abs(y) < deadzone): y = 0
		if (abs(z) < deadzone): z = 0

		linear_x = y
		linear_z = z
		angular = -x
		with self.car_style_turning_lock:
			if self.car_style_turning:
				angular = angular * copysign(1, y)
		return linear_x, linear_z, angular

	def tank_drive(self, xbox: XboxController) -> Twist:
		l, r = xbox.left_stick_y, xbox.right_stick_y
		linear_x = (l + r) / 2
		linear_z = 0  # TODO: could use triggers maybe
		angular = (-l + r) / 2
		return linear_x, linear_z, angular

	### callbacks ############################################################

	def enabled_callback(self, bool: SetBoolRequest) -> SetBoolResponse:
		with self.enabled_lock:
			self.enabled = bool.data
		response = SetBoolResponse()
		response.success = True
		response.message = "Updated gamepad_input enable status"
		return response

	def drive_direction_callback(self, drive_forward_request: SetBoolRequest) -> SetBoolResponse:
		if drive_forward_request.data:
			drive_direction_correction = 1
			drive_desc = 'forward'
		else:
			drive_direction_correction = -1
			drive_desc = 'backward'

		with self.drive_direction_correction_lock:
			self.drive_direction_correction = drive_direction_correction

		response = SetBoolResponse()
		response.success = True
		response.message = f"Driving {drive_desc}"
		return response

	def turning_style_callback(self, turning_style_request: SetBoolRequest) -> SetBoolResponse:
		with self.car_style_turning_lock:
			self.car_style_turning = turning_style_request.data

		response = SetBoolResponse()
		response.success = True
		response.message = f"Car style turning set to {turning_style_request.data}"
		return response

	def joy_sub_callback(self, joy: Joy):
		with self.tick_lock:
			self.last_tick = time()  # record most recent input

		xbox = XboxController(joy)  # translate joy array to xbox

		# key switches
		deadman_switch = xbox.x
		teleop_switch = deadman_switch and xbox.y
		autonomy_switch = deadman_switch and xbox.a
		return_home_switch = deadman_switch and xbox.b
		takeoff_switch = deadman_switch and xbox.dpad_y
		land_switch = deadman_switch and -xbox.dpad_y
		emergency_stop_switch = xbox.left_stick_button and xbox.right_stick_button
		turbo_switch = xbox.right_bumper
		tank_drive_switch = xbox.left_bumper

		### update user mode selection
		if teleop_switch:
			self.selected_mode_pub.publish(String("teleop"))
		elif autonomy_switch:
			self.selected_mode_pub.publish(String("autonomy"))
		elif return_home_switch:
			self.selected_mode_pub.publish(String("return_home"))
		elif takeoff_switch:
			self.selected_mode_pub.publish(String("takeoff"))
		elif land_switch:
			self.selected_mode_pub.publish(String("land"))
		elif emergency_stop_switch:
			self.selected_mode_pub.publish(String("emergency_stop"))

		### translate xbox to cmd_vel ###
		if not self.enabled:
			return

		if deadman_switch:
			linear_x, linear_z, angular = self.normal_drive(xbox)
		elif tank_drive_switch:
			linear_x, linear_z, angular = self.tank_drive(xbox)
		else:
			linear_x, linear_z, angular = 0, 0, 0

		# drive direction correction
		linear_x = linear_x * self.drive_direction_correction

		# scaling
		multiplier = self.turbo_multiplier if turbo_switch else self.base_multiplier
		linear_x_scale = abs(self.max_linear_speed if linear_x >= 0 else self.min_linear_speed) * multiplier
		linear_z_scale = abs(self.max_linear_speed if linear_z >= 0 else self.min_linear_speed) * multiplier
		angular_scale = abs(self.max_angular_speed if angular >= 0 else self.min_angular_speed) * multiplier

		# scale cmd_vel and publish
		cmd_vel = Twist()
		cmd_vel.linear.x = clamp(linear_x * linear_x_scale, self.min_linear_speed, self.max_linear_speed)
		cmd_vel.linear.z = clamp(linear_z * linear_z_scale, self.min_linear_speed, self.max_linear_speed)
		cmd_vel.angular.z = clamp(angular * angular_scale, self.min_angular_speed, self.max_angular_speed)
		self.cmd_vel_pub.publish(cmd_vel)

	### loop #################################################################

	def loop(self):
		rate = rospy.Rate(5 // self.timeout)

		while not rospy.is_shutdown():

			# tell robot to stay still if connection lost
			with self.enabled_lock:
				enabled = self.enabled
			with self.tick_lock:
				timed_out = (time() - self.last_tick) > self.timeout
			if timed_out and enabled:
				self.cmd_vel_pub.publish(Twist())

			rate.sleep()

if __name__ == "__main__":
	main()
