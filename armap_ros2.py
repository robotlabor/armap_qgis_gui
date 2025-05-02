import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_default, qos_profile_sensor_data
from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix, BatteryState

# ROS2 Node osztály
class ROS2PubSub(Node):
	def __init__(self, topic_name, ros2receiver):
		super().__init__('armapgui')
		self.ros2receiver = ros2receiver
		self.topic_name = '/j100_0000/sensors/gps_0/fix' # default topic_name ezen jön a robot pozíciója
		self.subscription = self.create_subscription(
			NavSatFix,
			self.topic_name,
			self.listener_callback,
			10
			)

		self.latest_message = ""
		self.latest_bms_message = ""
		self.latest_conecoords = ""

		#print(self.topic_name)

		bms_topic_name = '/j100_0000/platform/bms/state' # default topic_name ezen jön a robot pozíciója
		self.subscription = self.create_subscription(
			BatteryState,
			bms_topic_name,
			self.listener_bms_callback,
			qos_profile=qos_profile_sensor_data
			)

		robot_topic_name = '/j100_0000/robot_description' # default topic_name ezen jön a robot pozíciója
		self.subscription = self.create_subscription(
			BatteryState,
			robot_topic_name,
			self.listener_robot_callback,
			qos_profile=qos_profile_sensor_data
			)

	def listener_callback(self, msg):
		#self.get_logger().info(f"Üzenet érkezett: lat={msg.latitude}, lon={msg.longitude}, alt={msg.altitude}")
		self.latest_message = f"Latitude: {msg.latitude}, Longitude: {msg.longitude}, Altitude: {msg.altitude}"
		self.latitude = msg.latitude
		self.longitude = msg.longitude
		self.ros2receiver.signal_from_gps.emit(msg)
		#self.latest_message = msg.latitude  # Üzenet tárolása	

	def listener_bms_callback(self, msg):
		#self.get_logger().info(f"Üzenet érkezett: Voltage={msg.voltage}, current={msg.current}, percentage={msg.percentage}, temperature={msg.temperature}")
		self.latest_bms_message = f"Üzenet érkezett: Voltage={msg.voltage}, current={msg.current}, percentage={msg.percentage}, temperature={msg.temperature}"
		# Jelet küldünk a törölt sorok azonosítóival
		#print(type(msg))
		self.ros2receiver.signal_from_bms.emit(msg)

		#self.bmsMsgChanged.emit([])

		#print(f"Üzenet érkezett: lat={msg}")
		#voltage=26.826602935791016, temperature=nan, current=1.5771169662475586, charge=8.875486373901367, 
		#capacity=12.800000190734863, design_capacity=12.800000190734863, percentage=0.6933974027633667, 
		#power_supply_status=2, power_supply_health=1, power_supply_technology=2, present=True, 
		#cell_voltage=[26.826602935791016], cell_temperature=[nan], location='', serial_number=''

		#self.latest_message = msg.latitude  # Üzenet tárolása	

	def listener_robot_callback(self, msg):
		self.get_logger().info(f"Üzenet érkezett: Voltage={msg.voltage}, current={msg.current}, percentage={msg.percentage}, temperature={msg.temperature}")
		
	def set_publisher_conecoords(self, pub_topic_name, message_type):
		# Publisher inicializálása
		self.publisher_conecoords = self.create_publisher(message_type, pub_topic_name, 10)
		self.timer = self.create_timer(1.0, self.publish_conecoords_message)  # 1 másodperc időzítő
		self.message_type = message_type
		self.counter = 0

	def publish_conecoords_message(self):
		# Példa üzenet generálása
		msg = self.message_type()
		if hasattr(msg, 'data'):
			msg.data = f"Küldött üzenet: {self.latest_conecoords}"
		self.publisher_conecoords.publish(msg)
		self.get_logger().info(f"Küldött üzenet: {msg.data}")
		self.counter += 1
		
	def set_publisher_emergencystop(self, pub_topic_name, message_type):
		# Publisher inicializálása
		self.publisher_emergencystop = self.create_publisher(message_type, pub_topic_name, 10)
		self.em_timer = self.create_timer(1.0, self.publish_emergencystop_message)  # 1 másodperc időzítő
		self.message_type = message_type
		self.counter = 0

	def publish_emergencystop_message(self):
		# Példa üzenet generálása
		msg = self.message_type()
		if hasattr(msg, 'data'):
			msg.data = f"ACTIVE"
		self.publisher_emergencystop.publish(msg)
		self.get_logger().info(f"Küldött üzenet: {msg.data}")
		self.counter += 1
		if self.counter >= 10:
			self.em_timer.cancel()
