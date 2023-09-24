#!/usr/bin/env python3

from enum import IntEnum

from sensor_msgs.msg import Joy

class XboxInputs(IntEnum):
	"""Can be used to index Xbox controller inputs in a Joy array"""

	# axes
	LEFT_STICK_X_AXIS = 0
	LEFT_STICK_Y_AXIS = 1
	LEFT_TRIGGER_AXIS = 2
	RIGHT_STICK_X_AXIS = 3
	RIGHT_STICK_Y_AXIS = 4
	RIGHT_TRIGGER_AXIS = 5
	DPAD_X_AXIS = 6
	DPAD_Y_AXIS = 7

	# buttons
	A_INDEX = 0
	B_INDEX = 1
	X_INDEX = 2
	Y_INDEX = 3
	LEFT_BUMPER_INDEX = 4
	RIGHT_BUMPER_INDEX = 5
	SELECT_INDEX = 6
	START_INDEX = 7
	XBOX_BUTTON_INDEX = 8
	LEFT_STICK_BUTTON_INDEX = 9
	RIGHT_STICK_BUTTON_INDEX = 10


class XboxController:
	"""Translates Joy array to descriptive XboxController API"""

	def __init__(self, joy: Joy):

		# axes
		self.left_stick_x = joy.axes[XboxInputs.LEFT_STICK_X_AXIS]
		self.left_stick_y = joy.axes[XboxInputs.LEFT_STICK_Y_AXIS]
		self.left_trigger = joy.axes[XboxInputs.LEFT_TRIGGER_AXIS]
		self.right_stick_x = joy.axes[XboxInputs.RIGHT_STICK_X_AXIS]
		self.right_stick_y = joy.axes[XboxInputs.RIGHT_STICK_Y_AXIS]
		self.right_trigger = joy.axes[XboxInputs.RIGHT_TRIGGER_AXIS]
		self.dpad_x = joy.axes[XboxInputs.DPAD_X_AXIS]
		self.dpad_y = joy.axes[XboxInputs.DPAD_Y_AXIS]

		# buttons
		self.a = joy.buttons[XboxInputs.A_INDEX]
		self.b = joy.buttons[XboxInputs.B_INDEX]
		self.x = joy.buttons[XboxInputs.X_INDEX]
		self.y = joy.buttons[XboxInputs.Y_INDEX]
		self.left_bumper = joy.buttons[XboxInputs.LEFT_BUMPER_INDEX]
		self.right_bumper = joy.buttons[XboxInputs.RIGHT_BUMPER_INDEX]
		self.select = joy.buttons[XboxInputs.SELECT_INDEX]
		self.start = joy.buttons[XboxInputs.START_INDEX]
		self.xbox_button = joy.buttons[XboxInputs.XBOX_BUTTON_INDEX]
		self.left_stick_button = joy.buttons[XboxInputs.LEFT_STICK_BUTTON_INDEX]
		self.right_stick_button = joy.buttons[XboxInputs.RIGHT_STICK_BUTTON_INDEX]
