# Malayalam Games — Letter Tracing Drawing Canvas
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class TracingCanvas(QWidget):
    """Interactive drawing pad with a ghosted Malayalam guide character."""

    def __init__(self, ml_font_family: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(460, 340)
        self.ml_font_family = ml_font_family
        self.guide_char = "അ"
        self.pen_color = QColor("#E65100")
        self.pen_width = 18
        self.last_point = QPoint()
        self.drawing = False
        self.canvas_pixmap = QPixmap(640, 380)
        self.canvas_pixmap.fill(Qt.transparent)

    def set_character(self, char: str):
        self.guide_char = char
        self.clear_drawing()

    def set_pen_color(self, hex_color: str):
        self.pen_color = QColor(hex_color)

    def clear_drawing(self):
        self.canvas_pixmap.fill(Qt.transparent)
        self.update()

    def resizeEvent(self, event):
        if event.size().width() > 0 and event.size().height() > 0:
            new_pix = QPixmap(event.size())
            new_pix.fill(Qt.transparent)
            painter = QPainter(new_pix)
            painter.drawPixmap(0, 0, self.canvas_pixmap)
            painter.end()
            self.canvas_pixmap = new_pix
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.position().toPoint()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            current = event.position().toPoint()
            painter = QPainter(self.canvas_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, current)
            painter.end()
            self.last_point = current
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)
        painter.setBrush(QColor("#FFFDF7"))
        painter.setPen(QPen(QColor("#FFB74D"), 3, Qt.DashLine))
        painter.drawRoundedRect(rect, 20, 20)

        mid_y = self.height() // 2 + 55
        painter.setPen(QPen(QColor("#E0E0E0"), 2, Qt.DotLine))
        painter.drawLine(40, mid_y, self.width() - 40, mid_y)

        guide_font = QFont(self.ml_font_family, 165, QFont.Bold)
        painter.setFont(guide_font)
        painter.setPen(QColor("#DCE6F2"))
        painter.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, self.guide_char)

        painter.drawPixmap(0, 0, self.canvas_pixmap)
        painter.end()