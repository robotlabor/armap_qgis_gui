from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QSlider, QVBoxLayout
from PyQt5.QtGui import QPainter, QPen, QColor, QPolygonF, QPainterPath, QBrush, QFont
from PyQt5.QtCore import Qt, QPointF, QRectF
from typing import Optional, Union
import sys
import math


class CircularGauge(QWidget):
    """
    A Circular Gauge Widget that mimics an analog voltage meter.
    https://github.com/god233012yamil/Creating-a-Custom-Gauge-with-PyQt5
    Attributes:
        min_value (float): The minimum value of the gauge.
        max_value (float): The maximum value of the gauge.
        value (float): The current value of the gauge.
        steps (int): Number of major ticks on the gauge.
        start_angle (float): Starting angle of the gauge in degrees.
        end_angle (float): Ending angle of the gauge in degrees.
        outer_circle_pen_color (QColor): Pen color for the outer arc.
        outer_circle_brush_color (Optional[QColor]): Brush color for the outer arc.
        outer_circle_thickness (int): Thickness for the outer arc.
        inner_ring_pen_color (QColor): Pen color for the inner ring.
        inner_ring_brush_color (Optional[QColor]): Brush color for the inner ring.
        inner_circle_brush_color (Optional[QColor]): Brush color for the inner circle (hole).
        number_font_size (int): Font size for the numbers on the gauge.
        number_font_family (str): Font family for the numbers on the gauge.
    """

    def __init__(self,
                 min_value: float = 0.0,
                 max_value: float = 100.0,
                 value: float = 50.0,
                 steps: int = 10,
                 start_angle: float = -210.0,
                 end_angle: float = 30.0,
                 outer_circle_pen_color: Union[QColor, Qt.GlobalColor, str] = Qt.black,
                 outer_circle_brush_color: Optional[Union[QColor, Qt.GlobalColor, str]] = None,
                 outer_circle_thickness: int = 12,
                 inner_ring_pen_color: Union[QColor, Qt.GlobalColor, str] = Qt.black,
                 inner_ring_brush_color: Optional[Union[QColor, Qt.GlobalColor, str]] = Qt.white,
                 inner_circle_brush_color: Optional[Union[QColor, Qt.GlobalColor, str]] = None,
                 number_font_size: int = 10,
                 number_font_family: str = 'Arial',
                 parent=None):
        """
        Initialize the CircularGauge widget.

        Args:
            min_value (float): The minimum value of the gauge.
            max_value (float): The maximum value of the gauge.
            value (float): The current value of the gauge.
            steps (int): Number of major ticks on the gauge.
            start_angle (float): Starting angle of the gauge in degrees.
            end_angle (float): Ending angle of the gauge in degrees.
            outer_circle_pen_color (QColor or str): Pen color for the outer arc.
            outer_circle_brush_color (QColor or str or None): Brush color for the outer arc.
            outer_circle_thickness (int): Thickness for the outer arc.
            inner_ring_pen_color (QColor or str): Pen color for the inner ring.
            inner_ring_brush_color (QColor or str or None): Brush color for the inner ring.
            inner_circle_brush_color (QColor or str or None): Brush color for the inner circle (hole).
            number_font_size (int): Font size for the numbers on the gauge.
            number_font_family (str): Font family for the numbers on the gauge.
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        self.min_value: float = min_value
        self.max_value: float = max_value
        self.value: float = value
        self.steps: int = steps
        self.start_angle: float = start_angle  # Starting angle in degrees (min_value position)
        self.end_angle: float = end_angle  # Ending angle in degrees (max_value position)
        self.angle_range: float = self.end_angle - self.start_angle  # Total angle span
        self.outer_circle_thickness = outer_circle_thickness
        self.setMinimumSize(200, 200)

        # Set the colors, converting them to QColor if necessary
        self.outer_circle_pen_color = self._get_color(outer_circle_pen_color)
        self.outer_circle_brush_color = self._get_color(outer_circle_brush_color) if outer_circle_brush_color else None
        self.inner_ring_pen_color = self._get_color(inner_ring_pen_color)
        self.inner_ring_brush_color = self._get_color(inner_ring_brush_color) if inner_ring_brush_color else None
        self.inner_circle_brush_color = self._get_color(inner_circle_brush_color) if inner_circle_brush_color else None

        # Font settings
        self.number_font_size = number_font_size
        self.number_font_family = number_font_family

    def _get_color(self, color: Union[QColor, str, Qt.GlobalColor]) -> QColor:
        """Convert a color input to a QColor object."""
        if isinstance(color, QColor):
            return color
        else:
            return QColor(color)

    def setValue(self, value: float):
        """Set the current value of the gauge.

        Args:
            value (float): The new value to set.
        """
        if value < self.min_value:
            self.value = self.min_value
        elif value > self.max_value:
            self.value = self.max_value
        else:
            self.value = value
        self.update()

    def paintEvent(self, event):
        """Override the paintEvent to draw the gauge."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            center = rect.center()
            # radius = min(rect.width(), rect.height()) / 2 - 10
            radius = min(rect.width(), rect.height()) / 2 - self.outer_circle_thickness

            painter.translate(center)

            # Draw the outer arc using QPainterPath
            self.drawOuterArc(painter, radius)

            # Draw ticks
            self.drawTicks(painter, radius)

            # Draw numbers
            self.drawNumbers(painter, radius)

            # Draw another arc on top of the outer arc, the ticks, and the numbers
            self.drawOuterArc2(painter, radius)

            # Draw the needle
            self.drawNeedle(painter, radius)

        except Exception as e:
            print(f"Error in paintEvent: {e}")

    def normalize_angle(self, angle: float) -> float:
        """Normalize an angle to the range [0, 360)."""
        return angle % 360

    def drawTicks_ok(self, painter: QPainter, radius: float):
        """Draw the ticks and numbers on the gauge."""
        painter.save()
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)
        angle_step = self.angle_range / self.steps  # Degrees between ticks

        # Set the font for the numbers
        font = QFont(self.number_font_family, self.number_font_size)
        painter.setFont(font)

        for i in range(self.steps + 1):
            # Draw the ticks
            pen = QPen(Qt.black, 2)  # to set the ticks color
            painter.setPen(pen)
            angle = self.start_angle + i * angle_step
            rad = math.radians(angle)
            x1 = (radius - 10) * math.cos(rad)
            y1 = (radius - 10) * math.sin(rad)
            x2 = radius * math.cos(rad)
            y2 = radius * math.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Draw the numbers
            # pen = QPen(Qt.darkGray, 2)  # to set the numbers color
            pen = QPen(QColor(137, 148, 153), 2)  # to set the numbers color
            painter.setPen(pen)
            val = self.min_value + i * (self.max_value - self.min_value) / self.steps
            text = f"{val:.0f}"
            text_rect = QRectF(-15, -15, 30, 30)
            text_x = (radius - 18) * math.cos(rad)
            text_y = (radius - 18) * math.sin(rad)
            painter.save()
            painter.translate(text_x, text_y)
            painter.rotate(angle + 90)
            painter.drawText(text_rect, Qt.AlignCenter, text)

            painter.restore()

        painter.restore()

    def drawOuterArc(self, painter: QPainter, radius: float):
        """
        Draw the outer arc using QPainterPath
        :param painter:
        :param radius:
        :return:
        """
        painter.save() ##
        path = QPainterPath()
        arc_rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)

        # Normalize angles to [0, 360)
        start_angle_normalized = self.normalize_angle(self.start_angle)

        # Calculate startAngle and spanAngle for arc
        # Angles in degrees, starting from 0 at 3 o'clock position, increasing counterclockwise
        startAngle = -start_angle_normalized
        spanAngle = -(self.angle_range)

        path.arcMoveTo(arc_rect, startAngle)
        path.arcTo(arc_rect, startAngle, spanAngle)

        painter.setPen(QPen(self.outer_circle_pen_color, self.outer_circle_thickness))  # outer circle thickness
        if self.outer_circle_brush_color:
            painter.setBrush(QBrush(self.outer_circle_brush_color))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.restore()

    def drawOuterArc2(self, painter: QPainter, radius: float):
        """
        Draw the outer arc using QPainterPath
        :param painter:
        :param radius:
        :return:
        """
        painter.save() ##
        path = QPainterPath()
        arc_rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)

        # Normalize angles to [0, 360)
        start_angle_normalized = self.normalize_angle(self.start_angle)

        # Calculate startAngle and spanAngle for arc
        # Angles in degrees, starting from 0 at 3 o'clock position, increasing counterclockwise
        startAngle = -start_angle_normalized
        spanAngle = -(self.angle_range)

        path.arcMoveTo(arc_rect, startAngle)
        path.arcTo(arc_rect, startAngle, spanAngle)

        # painter.setPen(QPen(self.outer_circle_pen_color, self.outer_circle_thickness))  # outer circle thickness
        painter.setPen(QPen(QColor(200, 200, 200, 200), self.outer_circle_thickness / 2))  # outer circle thickness
        # painter.setPen(QPen(QColor(0, 150, 255, 200), self.outer_circle_thickness / 2))  # outer circle thickness
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.restore()

    def drawTicks(self, painter: QPainter, radius: float):
        """Draw the ticks on the gauge."""
        painter.save()
        angle_step = self.angle_range / self.steps  # Degrees between ticks

        for i in range(self.steps + 1):
            painter.save() ##
            pen = QPen(Qt.white, 2)  # to set the ticks color and thickness
            # pen = QPen(QColor(0, 150, 255), 6)  # to set the ticks color and thickness
            painter.setPen(pen)
            angle = self.start_angle + i * angle_step
            rad = math.radians(angle)
            x1 = (radius - 10) * math.cos(rad)
            y1 = (radius - 10) * math.sin(rad)
            x2 = radius * math.cos(rad)
            y2 = radius * math.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            painter.restore()

        painter.restore()

    def drawNumbers(self, painter: QPainter, radius: float):
        """Draw the numbers on the gauge."""
        painter.save()
        # pen = QPen(Qt.darkGray, 2)  # to set the numbers color
        # pen = QPen(QColor(137, 148, 153), 2)  # to set the numbers color
        pen = QPen(QColor(0, 150, 255), 1)  # to set the numbers color
        painter.setPen(pen)
        angle_step = self.angle_range / self.steps  # Degrees between ticks

        # Set the font for the numbers
        font = QFont(self.number_font_family, self.number_font_size)
        painter.setFont(font)

        for i in range(self.steps + 1):
            angle = self.start_angle + i * angle_step
            rad = math.radians(angle)
            val = self.min_value + i * (self.max_value - self.min_value) / self.steps
            text = f"{val:.0f}"
            # text_rect = QRectF(-15, -15, 30, 30)
            text_rect = QRectF(-15, -15, 34, 34)
            text_x = (radius - 18) * math.cos(rad)
            text_y = (radius - 18) * math.sin(rad)
            painter.save()
            painter.translate(text_x, text_y)
            painter.rotate(angle + 90)
            painter.drawText(text_rect, Qt.AlignCenter, text)
            painter.restore()

        painter.restore()

    def drawNeedle(self, painter: QPainter, radius: float):
        """Draw the needle with shadows, base ring, and inner circle."""
        painter.save()
        value_range = self.max_value - self.min_value
        if value_range == 0:
            value_ratio = 0.0
        else:
            value_ratio = (self.value - self.min_value) / value_range

        # Calculate the angle for the current value
        angle = self.start_angle + value_ratio * self.angle_range

        # Define the needle shape
        needle = QPolygonF([
            QPointF(0, -5),                   # Left base point
            QPointF(radius - 20, 0),          # Tip point
            QPointF(0, 5)                     # Right base point
        ])

        # Draw the shadow of the needle
        painter.save()
        painter.rotate(angle)
        painter.translate(2, 2)  # Offset for shadow effect
        shadow_color = QColor(0, 0, 0, 80)  # Semi-transparent black
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawPolygon(needle)
        painter.restore()

        # Draw the needle
        painter.save()
        painter.rotate(angle)
        # pen = QPen(Qt.red, 1)
        pen = QPen(QColor(0, 150, 255), 1)  # needle color
        painter.setPen(pen)
        # painter.setBrush(Qt.red)
        painter.setBrush(QColor(0, 150, 255))
        painter.drawPolygon(needle)
        painter.restore()

        # Draw the shadow of the ring
        painter.save()
        painter.rotate(angle)  # new
        painter.translate(2, 2)  # Offset for shadow effect
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)

        center_circle_radius_outer = 12
        center_circle_radius_inner = 5

        # Create a path for the outer circle
        ring_path = QPainterPath()
        ring_path.addEllipse(QPointF(0, 0), center_circle_radius_outer, center_circle_radius_outer)

        # Create a path for the inner circle (hole)
        ring_inner_path = QPainterPath()
        ring_inner_path.addEllipse(QPointF(0, 0), center_circle_radius_inner, center_circle_radius_inner)

        # Subtract the inner circle from the outer circle to create the ring
        ring_shadow_path = ring_path.subtracted(ring_inner_path)

        painter.drawPath(ring_shadow_path)
        painter.restore()

        # Draw the ring
        painter.setPen(QPen(self.inner_ring_pen_color, 1))
        if self.inner_ring_brush_color:
            painter.setBrush(QBrush(self.inner_ring_brush_color))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.drawPath(ring_path)

        # Draw the inner circle (hole) with specified color
        if self.inner_circle_brush_color:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.inner_circle_brush_color))
            painter.drawEllipse(QPointF(0, 0), center_circle_radius_inner, center_circle_radius_inner)

        painter.restore()


class Windows(QMainWindow):
    def __init__(self) -> None:
        super(Windows, self).__init__()

        self.gauge = CircularGauge(
            min_value=0,
            max_value=30,
            value=0,
            steps=15,
            start_angle=-210.0,  # -240.0,  # -210.0,
            end_angle=30.0,  # 60.0,  # 30.0,
            outer_circle_pen_color=QColor(0, 150, 255),  # 'black',  # QColor(137, 148, 153),  # 'blue',
            outer_circle_brush_color='white',  # QColor(0, 150, 255, 255),  # 'lightblue',
            outer_circle_thickness=20,
            inner_ring_pen_color=QColor(0, 150, 255),  # 'darkred',
            inner_ring_brush_color=QColor(0, 150, 255),  # 'red',
            inner_circle_brush_color='white',  # QColor(0, 150, 255, 255),  # Color for the inner circle (hole)
            number_font_size=14,  # Font size for the numbers
            number_font_family='Arial'  # 'Times New Roman'  # Font family for the numbers
        )

        # Create a slider to simulate voltage changes
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(30)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(lambda value: self.updateVoltage(value))

        layout = QVBoxLayout()
        layout.addWidget(self.gauge)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        # self.setMinimumSize(800, 600)
        self.setWindowTitle('Custom Gauge')

    def updateVoltage(self, value: int) -> None:
        self.gauge.setValue(value)


def main():
    app = QApplication(sys.argv)
    window = Windows()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()