import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtCore import QTimer, QVariant
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QColor
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, qos_profile_sensor_data
from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix, BatteryState
from armap_ros2 import ROS2PubSub
from circular_gauge import CircularGauge
from table_widget import TableWidget
import pdb


def get_topic_list():
	node_dummy = Node("_ros2cli_dummy_to_show_topic_list")
	topic_list = node_dummy.get_topic_names_and_types()
	node_dummy.destroy_node()
	return topic_list

class PrintClickedPoint(QgsMapToolEmitPoint):
	def __init__(self, canvas):
		self.canvas = canvas
		QgsMapToolEmitPoint.__init__(self, self.canvas)

		def canvasPressEvent( self, e ):
			point = self.toMapCoordinates(self.canvas.mouseLastXY())
			point = list(point)
			feature = QgsFeature()
			#x = event.mapPoint().x()
			#y = event.mapPoint().y()
			#point = QgsGeometry.fromPointXY(QGSPintXY(x,y))
			#feature.setGeometry(point)
			#self.conelayer.dataProvider().addFetures([feature])
			print(point)

class ROS2Receiver(QObject):
	signal_from_bms = pyqtSignal(BatteryState)
	signal_from_gps = pyqtSignal(NavSatFix)

	def __init__(self):
		super().__init__()

	def handle_signal(self, message):
		i = 1
		#print(type(message))
		#if 'BatteryState' in str(type(message)) :
		#	print(f"BMS voltage: {message.voltage}")
		#elif 'NavSatFix' in str(type(message)) :
		#	print(f"GPS lon: {message.longitude}")


class MainWindow(QMainWindow):
	def __init__(self, ros_node, canvas):
		super().__init__()
		self.ros_node = ros_node
		ros2receiver = ros_node.ros2receiver
		ros2receiver.signal_from_bms.connect(self.handle_signal)
		ros2receiver.signal_from_gps.connect(self.handle_signal)

		self.canvas = canvas
		self.coneFID = 0
		self.robot_lastposition_trace = False
		self.initUI()

	def handle_signal(self, message):
		#print(type(message))
		if 'BatteryState' in str(type(message)) :
			#print(f"2BMS voltage: {message.voltage}")
			self.gauge1.setValue(float(message.voltage))
			self.bms_V.setText(f'BMS U: {str(round(message.voltage,1))} V')
			self.bms_I.setText(f'BMS I: {str(round(message.current,1))} mA')
			self.bms_progressbar.setValue(int(round(message.percentage*100,1)))
		#elif 'BatteryState' in str(type(message)) :
			# ha a rakománnyal kapcsolatos üzenetet vesszük
			self.load_info_total.setText(f'Összes bója: {str(5)}')
			self.load_info_done.setText(f'Lerakva: {str(3)}')
		elif 'NavSatFix' in str(type(message)) :
			i = 1
			#print(f"2GPS lon: {message.longitude}")

	def initUI(self):
		# Fő widget beállítása
		main_widget = QWidget()
		main_layout = QVBoxLayout(main_widget)

#		window = QtWidgets.QMainWindow()
		self.canvas = QgsMapCanvas()
		self.canvas.setMinimumSize(600, 600)  # Minimum méret beállítása

		self.initLayers()

		# Alsó Panel (Debug és gombok)
		debug_layout = QHBoxLayout()
		self.debug_text = QTextEdit()
		self.debug_text.setReadOnly(True)
		self.debug_text.setMaximumHeight(250)
		self.debug_text.setMinimumHeight(200)
		
		self.conesTable = TableWidget()
		# Táblázat törlés Jel kezelése
		self.conesTable.row_deleted.connect(self.removeConeFromLayer)
		self.conesTable.coords_sent.connect(self.sendConeCoords)
		self.conesTable.setMaximumHeight(250)
		debug_layout.addWidget(self.debug_text)
		debug_layout.addWidget(self.conesTable)
		#debug_layout.setMinimumSize([,200])

		# Gombok (QPushButton)
		self.pan_button = QPushButton("Térkép mozgatása")
		self.pan_button.setCheckable(True)
		self.pan_button.setChecked(True)
		
		self.zoom_button = QPushButton("Zoom")
		self.zoom_button.setCheckable(True)

		self.cone_button = QPushButton("Bója lerakás")
		self.cone_button.setCheckable(True)

		self.center_button = QPushButton("Követés")
		self.center_button.setCheckable(True)

		self.pan_button.clicked.connect(self.set_pan_tool)
		self.zoom_button.clicked.connect(self.set_zoom_tool)
		self.cone_button.clicked.connect(self.set_cone_tool)
		self.center_button.clicked.connect(lambda: self.set_center_tool(self.robotlayer.extent()))

		# out click tool will emit a QgsPoint on every click
		self.clickTool = QgsMapToolEmitPoint(self.canvas)

		# Gombok elrendezése
		self.button_widget = QWidget()
		button_layout = QVBoxLayout(self.button_widget)
		button_layout.addWidget(self.pan_button)
		button_layout.addWidget(self.zoom_button)
		button_layout.addWidget(self.center_button)
		button_layout.addWidget(self.cone_button)
		button_layout.addStretch()
		self.button_widget.setMaximumHeight(200)
		#debug_layout.addWidget(button_widget)

		self.initGauges()

		# Fő elrendezés összeállítása
		#main_layout.addWidget(self.canvas)  # Térkép widget
		monitor_layout = QHBoxLayout()
		monitor_layout.addWidget(self.canvas)
		monitor_layout.addWidget(self.gauge_widget)

		main_layout.addLayout(monitor_layout)
		main_layout.addLayout(debug_layout)  # Debug panel és gombok
		#main_layout.addWidget(self.gauge_widget)	

		# Fő widget beállítása
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)
		
		# Ablak paraméterek beállítása
		self.setWindowTitle("ARMap GUI")
		self.resize(1300, 500)

	def initGauges(self):
		# mérőórák beállítása
		# Create customized gauge
		self.gauge1 = CircularGauge(
			min_value=0,
			max_value=50,
			value=0,
			steps=10,
			start_angle=-210.0,
			end_angle=30.0,
			outer_circle_pen_color=QColor(50, 50, 50),
			outer_circle_brush_color=QColor(30, 30, 30),
			outer_circle_thickness=10,
			inner_ring_pen_color=QColor(70, 70, 70),
			inner_ring_brush_color=QColor(40, 40, 40),
			inner_circle_brush_color=QColor(20, 20, 20),
			number_font_size=10,
			number_font_family='Arial'
		)

		self.gauge2 = CircularGauge(
			min_value=0,
			max_value=300,
			value=0,
			steps=10,
			start_angle=-210.0,
			end_angle=30.0,
			outer_circle_pen_color=QColor(50, 50, 50),
			outer_circle_brush_color=QColor(30, 30, 30),
			outer_circle_thickness=10,
			inner_ring_pen_color=QColor(70, 70, 70),
			inner_ring_brush_color=QColor(40, 40, 40),
			inner_circle_brush_color=QColor(20, 20, 20),
			number_font_size=6,
			number_font_family='Arial'
		)

		self.gauge3 = CircularGauge(
			min_value=0,
			max_value=300,
			value=0,
			steps=10,
			start_angle=-210.0,
			end_angle=30.0,
			outer_circle_pen_color=QColor(50, 50, 50),
			outer_circle_brush_color=QColor(30, 30, 30),
			outer_circle_thickness=10,
			inner_ring_pen_color=QColor(70, 70, 70),
			inner_ring_brush_color=QColor(40, 40, 40),
			inner_circle_brush_color=QColor(20, 20, 20),
			number_font_size=6,
			number_font_family='Arial'
		)

		self.gauge4 = CircularGauge(
			min_value=0,
			max_value=300,
			value=0,
			steps=10,
			start_angle=-210.0,
			end_angle=30.0,
			outer_circle_pen_color=QColor(50, 50, 50),
			outer_circle_brush_color=QColor(30, 30, 30),
			outer_circle_thickness=10,
			inner_ring_pen_color=QColor(70, 70, 70),
			inner_ring_brush_color=QColor(40, 40, 40),
			inner_circle_brush_color=QColor(20, 20, 20),
			number_font_size=6,
			number_font_family='Arial'
		)

		self.gauge_widget = QWidget()
		self.gauge_widget.setMinimumWidth(250)
		self.gauge_widget.setMaximumWidth(250)
		gauge_layout = QVBoxLayout(self.gauge_widget)
		gauge_front = QHBoxLayout()
		gauge_rear = QHBoxLayout()
		gauge1_labeled = QVBoxLayout()
		gauge2_labeled = QVBoxLayout()
		gauge3_labeled = QVBoxLayout()
		gauge4_labeled = QVBoxLayout()

		gauge_layout.addLayout(gauge_front)
		gauge_layout.addLayout(gauge_rear)
		#gauge_layout.addWidget(self.gauge1)
		#gauge_layout.addWidget(self.gauge2)
		#gauge_layout.addWidget(self.gauge3)
		#gauge_layout.addWidget(self.gauge4)
		label1 = QLabel("Sebesség (km/h)")
		label1.setAlignment(Qt.AlignCenter)
		gauge1_labeled.addWidget(label1)
		gauge1_labeled.addWidget(self.gauge1)
		gauge_front.addLayout(gauge1_labeled)
		# label2 = QLabel("Motor FR (rpm)")
		# label2.setAlignment(Qt.AlignCenter)
		# gauge2_labeled.addWidget(label2)
		# gauge2_labeled.addWidget(self.gauge2)
		# gauge_front.addLayout(gauge2_labeled)
		# label3 = QLabel("Motor RL (rpm)")
		# label3.setAlignment(Qt.AlignCenter)
		# gauge3_labeled.addWidget(label3)
		# gauge3_labeled.addWidget(self.gauge3)
		# gauge_rear.addLayout(gauge3_labeled)
		# label4 = QLabel("Motor RR (rpm)")
		# label4.setAlignment(Qt.AlignCenter)
		# gauge4_labeled.addWidget(label4)
		# gauge4_labeled.addWidget(self.gauge4)
		# gauge_rear.addLayout(gauge4_labeled)

		bms_layout = QVBoxLayout()
		self.bms_label = QLabel()
		self.bms_label.setText("Akku állapot:")
		label1.setAlignment(Qt.AlignLeft)

		self.bms_progressbar = QProgressBar(self)
		self.bms_progressbar.setAlignment(Qt.AlignCenter)
		
		#self.bms_progressbar.setFixedSize(300, 30)

		self.bms_I = QLabel()
		self.bms_I.setAlignment(Qt.AlignCenter)
		self.bms_V = QLabel()
		self.bms_V.setAlignment(Qt.AlignCenter)
		gauge_layout.addWidget(self.bms_label)
		gauge_layout.addWidget(self.bms_progressbar)
		gauge_layout.addWidget(self.bms_I)
		gauge_layout.addWidget(self.bms_V)

		self.load_info_label = QLabel()
		self.load_info_label.setText("Rakomány")
		self.load_info_label.setAlignment(Qt.AlignLeft)
		self.load_info_total = QLabel()
		self.load_info_total.setAlignment(Qt.AlignCenter)
		self.load_info_done = QLabel()
		self.load_info_done.setAlignment(Qt.AlignCenter)
		gauge_layout.addWidget(self.load_info_label)
		gauge_layout.addWidget(self.load_info_total)
		gauge_layout.addWidget(self.load_info_done)


		self.emergency_button = QPushButton("STOP")
		self.emergency_button.setStyleSheet("background-color: red")
		self.emergency_button.setMinimumHeight(50)
		self.emergency_button.clicked.connect(self.set_emergency_stop)
		gauge_layout.addWidget(self.emergency_button)

		gauge_layout.addWidget(self.button_widget)

		gauge_layout.addStretch()
		self.gauge_widget.setMaximumWidth(350)

		# Sebesség
		# Motor paraméterek (áramfelvétel, stb.)
		# Akku % (progress bar)
		# Akku feszültség
		# Akku áram

		#Rakomány adatai
		# Lerakott bólyák száma
		# A fedélzeten lévő bólyák száma

		# Célállomás?
		# Indulási hely?
		# Navigáció állapot %?


		
	def initLayers(self):
		filename = "imagedata/zalazone_ortofoto_20220825.tif"
		filename = "imagedata/zalazone_Egyetemi-palya_orthophoto.tif"
		filename = "imagedata/smartcity_ortofoto_20220825.tif"
		filename2 = "imagedata/73-341_o_2008.tif"
		
		#qgis.utils.iface.mapCanvas().mapRenderer().setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
		#crs = QgsCoordinateReferenceSystem('EPSG:32633')
		crs = QgsCoordinateReferenceSystem('EPSG:32633')
		self.project = QgsProject.instance()
		self.canvas.setDestinationCrs(crs)
		#QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:32633'))

		self.conelayer = QgsVectorLayer("Point?crs=EPSG:32633", "Bója réteg", "memory")
		self.project.addMapLayer(self.conelayer)
		
		#így lehet változtatni a pont színét
		symbols = self.conelayer.renderer().symbol().setColor(QtGui.QColor.fromRgb(50,50,50))
		provider = self.conelayer.dataProvider()
		self.conelayer.startEditing()
		provider.addAttributes([QgsField("FID", QVariant.Int)])
		self.conelayer.updateFields()

		#így lehet svg-re cserélni a markert
		symbol = QgsSvgMarkerSymbolLayer('buoy_icon.svg')
		symbol.setSize(6)
		symbol.setFillColor(QtGui.QColor('#0000ff'))
		symbol.setStrokeColor(QtGui.QColor('#ff0000'))
		symbol.setStrokeWidth(1)
		self.conelayer.renderer().symbol().changeSymbolLayer(0, symbol )


		#self.canvas.setLayers([layer,self.conelayer])
		#self.canvas.setLayers([self.conelayer])

		self.robotlayer = QgsVectorLayer("Point?crs=EPSG:32633", "Robot réteg", "memory")
		self.project.addMapLayer(self.robotlayer)
		rsymbol = self.robotlayer.renderer().symbol()
		rsymbol.setColor(QtGui.QColor.fromRgb(0,250,0))
		rsymbol.setSize(5)
		#self.canvas.setLayers([self.robotlayer])

		layer = QgsRasterLayer(filename, "raster")
		layer.setCrs(QgsCoordinateReferenceSystem('EPSG:32633'))
		self.project.addMapLayer(layer)
		#canvas_layer = QgsMapCanvasLayer(layer)
		#self.canvas.setLayers([layer])
		self.canvas.zoomToFullExtent()

		layer2 = QgsRasterLayer(filename2, "raster")
		#layer.setCrs(QgsCoordinateReferenceSystem('EPSG:23700'))
		self.project.addMapLayer(layer2)
		#canvas_layer = QgsMapCanvasLayer(layer)
		#self.canvas.setLayers([layer,layer2])
#		self.canvas.zoomToFullExtent()
		self.canvas.setLayers([self.conelayer,self.robotlayer,layer, layer2])
		
		# Timer a GUI frissítéséhez
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_text)
		self.timer.start(200)  # 100 ms-ként frissít

		#self.canvas.setFocusPolicy(Qt.StrongFocus)
		#self.canvas.setFocus()

		self.canvas.setExtent(layer.extent())
		#canvas.zoomToFullExtent()
		#self.canvas.freeze(True)
		#self.canvas.show()
		#self.canvas.refresh()
		#self.canvas.freeze(False)
		#self.canvas.repaint()
		self.canvas.refresh()

		self.canvas.show()
		self.canvas.raise_()

	def update_text(self):
		#self.debug_text.setText(str(self.ros_node.latest_message))
		self.debug_text.append(str(self.ros_node.latest_message))
		self.debug_text.append(str(self.ros_node.latest_bms_message))
		self.updatePointOnLayer(self.robotlayer)

	def updatePointOnLayer(self, maplayer):
		features = maplayer.getFeatures()
		count = sum (1 for _ in features)
		#print(features.isValid(), count)

		# ha csak az aktuális pozíciót akarjuk megjeleníteni a térképen, akkor törölni kell a korábbi adatokat
		maplayer.startEditing()
		maplayer.dataProvider().truncate()
		maplayer.commitChanges()
		self.canvas.refresh()

		#first = list(features)[0]
		#print(first)
		#maplayer.dataProvider().deleteFeatures(first)
		sourceCrs = QgsCoordinateReferenceSystem('EPSG:4326')
		destCrs = QgsCoordinateReferenceSystem('EPSG:32633')
		tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())

		feature = QgsFeature()
		point = QgsPointXY(self.ros_node.longitude, self.ros_node.latitude)
		geompoint = QgsGeometry.fromPointXY(QgsPointXY(self.ros_node.longitude, self.ros_node.latitude))
		geompoint.transform(tr) 
		#print(geompoint.asPoint())
		#print(self.ros_node.latitude,self.ros_node.longitude)
		if self.robot_lastposition_trace:
			self.canvas.setCenter(geompoint.asPoint())
			#print(geompoint.asPoint())
		#self.canvas.refresh()
		feature.setGeometry(geompoint)
		maplayer.dataProvider().addFeatures([feature])

	def addConeOnLayer(self, maplayer, pointX, pointY):
		sourceCrs = QgsCoordinateReferenceSystem('EPSG:32633')
		destCrs = QgsCoordinateReferenceSystem('EPSG:4326')
		tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())

		feature = QgsFeature()
		point = QgsPointXY(pointX,pointY)
		geompoint = QgsGeometry.fromPointXY(point)
		geompointwgs = QgsGeometry.fromPointXY(point)
		geompointwgs.transform(tr) 
		
		#print(geompoint.asPoint())
		feature.setGeometry(geompoint)
		self.coneFID = self.coneFID + 1
		feature.setAttributes([self.coneFID])
		ret = maplayer.dataProvider().addFeatures([feature])
		maplayer.commitChanges()
		if list(ret)[0]:
			self.conesTable.add_new_row([str(self.coneFID),str(pointX),str(pointY),str(geompointwgs.asPoint().x()),str(geompointwgs.asPoint().y())])
		else:
			self.coneFID = self.coneFID - 1
			print('Nem sikerült a korrdináta rögzítése!')

	def removeConeFromLayer(self, rows):
		# töröljük a megadott FID-jű bóját a térképről
		#print(rows)
		self.conelayer.startEditing()
		fid_to_delete = rows  # Példa: FID attribútum értéke, amelyet törölni akarunk
		#request = QgsFeatureRequest().setFilterExpression(f'"FID" = {fid_to_delete}')
		fid_condition = f'"FID" IN ({", ".join(map(str, rows))})'

		request = QgsFeatureRequest().setFilterExpression(fid_condition)
		# found_features = []
		# for feature in self.conelayer.getFeatures(request):
		# 	found_features.append(feature)
		# 	print(f"Talált objektum FID: {feature['FID']}")
		# 	print(f"Geometria: {feature.geometry().asWkt()}")  # Geometria WKT formátumban

		# if found_features:
		# 	print(f"Összes talált objektum száma: {len(found_features)}")
		# else:
		# 	print("Nem található objektum a megadott attribútummal.")

		for feature in self.conelayer.getFeatures(request):
			self.conelayer.deleteFeature(feature.id())
		self.conelayer.commitChanges()
		self.canvas.refresh()
		self.canvas.repaint()
		
		print(f"Törölve az elem, amelynek FID értéke: {fid_to_delete}")
		#print('Bója törölve (FID): ' + str(rows))

	def sendConeCoords(self, rows):
		# kiküldjük a bója koordinátákat
		print(rows)
		# csak akkor kezdjük küldeni, amikor már tettünk le bójákat
		self.ros_node.set_publisher_conecoords('/armapgui/conecoords',String)

		self.ros_node.latest_conecoords = rows
		print(f"Koordináták kiküldve!")

	def set_emergency_stop(self):
		# Vészleállás Gomb kattintásának eseménye
		#self.button.setText("Köszönöm, hogy kattintottál!")
		# csak akkor kezdjük küldeni, amikor már tettünk le bójákat
		self.ros_node.set_publisher_emergencystop('/armapgui/emergencystop',String)
		print("Vészleállás!!")

	def set_pan_tool(self):
		#iface.mapCanvas().unsetMapTool(iface.mapCanvas().mapTool())

		self.zoom_button.setChecked(False)
		self.cone_button.setChecked(False)
		self.pan_button.setChecked(True)

		pan_tool = QgsMapToolPan(self.canvas)
		self.canvas.setMapTool(pan_tool)
		pt = pan_tool.action().trigger()
		#pdb.set_trace()

		self.canvas.refresh()
		#self.debug_text.append("Pan Tool aktiválva.")
		if self.canvas.mapTool() == pan_tool:
			print("Pan Tool sikeresen aktiválva!")
		else:
			print("Hiba: Pan Tool nem aktiválódott!")

	def set_zoom_tool(self):
		self.pan_button.setChecked(False)
		self.cone_button.setChecked(False)
		self.zoom_button.setChecked(True)

		zoom_tool = QgsMapToolZoom(self.canvas, False)
		self.canvas.setMapTool(zoom_tool)
		self.debug_text.append("Zoom Tool aktiválva.")

	def set_cone_tool(self):
		# a cone layerre kell pontokat tenni a kattintások pozíciójára
		self.cone_button.setChecked(True)
		self.pan_button.setChecked(False)
		self.zoom_button.setChecked(False)

		def display_point(pointTool):
			pointX=pointTool[0]
			pointY=pointTool[1]
			print('Kért koordináta ' +str(pointX)+','+str(pointY))
			self.addConeOnLayer(self.conelayer,pointX, pointY)

		 # this QGIS tool emits as QgsPoint after each click on the map canvas
		self.pointTool = QgsMapToolEmitPoint(self.canvas)
		# Checkpoint
		#print("S 1")
		self.pointTool.canvasClicked.connect( display_point )
		self.canvas.setMapTool( self.pointTool )
		# Checkpoint
		#print("S 3")

		#canvas_clicked = PrintClickedPoint( self.canvas )
		#self.canvas.setMapTool( canvas_clicked )
		#self.debug_text.append("Bója Tool aktiválva.")
	
	def set_center_tool(self, layerextent:QgsRectangle):
		#print(self.center_button.isChecked())
		if self.center_button.isChecked():
			self.center_button.setChecked(True)
			self.robot_lastposition_trace = True
			self.debug_text.append("Követés be.")
		else:
			self.center_button.setChecked(False)
			self.robot_lastposition_trace = False
			self.debug_text.append("Követés ki.")
		#canvas_clicked = PrintClickedPoint( self.canvas )
		#self.canvas.setMapTool( canvas_clicked )
		#ex = self.robotlayer.extent()
		#print(layerextent)
		#self.canvas.setExtent(layerextent)


# Program belépési pontja
def main():
	rclpy.init(args=sys.argv)
	ros2receiver = ROS2Receiver()
	ros2receiver.signal_from_bms.connect(ros2receiver.handle_signal)
	ros2receiver.signal_from_gps.connect(ros2receiver.handle_signal)

	ros_node = ROS2PubSub('/j100_0000/sensors/gps_0/fix',ros2receiver)  # Topic neve
	app = QApplication(sys.argv)

	QgsApplication.setPrefixPath("/usr/share/qgis",True)
	#qgs = QgsApplication([],False)
	QgsApplication.initQgis()
	
	canvas = QgsMapCanvas()

	main_window = MainWindow(ros_node,canvas)
	pan_tool = QgsMapToolPan(main_window.canvas)
	main_window.canvas.setMapTool(pan_tool)

	# ROS futtatása külön szálon
	def ros_spin():
		rclpy.spin(ros_node)

	ros_thread = threading.Thread(target=ros_spin, daemon=True)
	ros_thread.start()

	main_window.show()

	try:
		sys.exit(app.exec_())
	finally:
		rclpy.shutdown()
		QgsApplication.exitQgis()

if __name__ == '__main__':
	main()