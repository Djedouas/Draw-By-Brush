# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Brush
                                 A QGIS plugin
 This plugin provides a tool for drawing polygons like with a brush in photoshop and GIMP
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-02-18
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Joseph Burkhart
        email                : josephburkhart.public@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from builtins import str
from builtins import range

from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolEmitPoint, \
    QgsProjectionSelectionDialog
from qgis.core import QgsWkbTypes, QgsPointXY, QgsPoint, QgsGeometry, QgsRenderContext

from qgis.PyQt.QtCore import Qt, QCoreApplication, pyqtSignal, QPoint
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, \
    QGridLayout, QLabel, QGroupBox, QVBoxLayout, QComboBox, QPushButton, \
    QInputDialog
from qgis.PyQt.QtGui import QDoubleValidator, QIntValidator, QKeySequence, \
    QPixmap, QCursor, QPainter

from math import sqrt, pi, cos, sin

from PyQt5.QtGui import QGuiApplication

# Initialize Qt resources from file resources.py
from .resources import *

class BrushTool(QgsMapTool):
    """
    Brush drawing tool.
    Patterned off of `drawtools.py` from the qdraw plugin.
    """
    # Make signals for movement and end of selection and end of drawing
    selectionDone = pyqtSignal()
    move = pyqtSignal()
    rbFinished = pyqtSignal(QgsGeometry)    # from BeePen

    def __init__(self, iface, color):
        QgsMapTool.__init__(self, iface.mapCanvas())

        # Save references to QGIS interface and current active layer
        self.canvas = iface.mapCanvas()
        #QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.iface = iface
        self.active_layer = iface.activeLayer()

        # Save reference to active layer
        
        # Configure Rubber Band
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(color)
        self.rb.setWidth(1)

        # Set default brush parameters
        self.brush_radius = 10
        self.brush_points = 64

        self.mouse_state = 'free'
        
        self.reset()
        return None

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rb.reset(True)	 # true, its a polygon

    def circle_around_point(self, center, radius=0, num_points=0, map_units=False):
        """
        Creates a circular QgsGeometry centered on a point with the given 
        radius and num_points

        :type center: qgis.core.QgsPoint
        :param center: canvas point, in layer crs
        :type radius: float
        :param radius: cicle radius, considered to be in layer units
        :type num_points: int
        :param num_points: number of vertices
        :type map_units: bool
        :param map_units: whether the radius should be considered in map units
        :return: QgsGeometry of type QGis.Polygon

        Adapted from https://gis.stackexchange.com/a/69792
        """
        if not radius:
            radius = self.brush_radius #default brush radius
        
        if not map_units:
            context = QgsRenderContext().fromMapSettings(self.canvas.mapSettings())
            # scale factor is px / mm; as mm (converted to map pixels, then to map units)
            radius *= context.mapToPixel().mapUnitsPerPixel()
            #print(f"radius = {radius}")
            #print(f"context.scaleFactor() = {context.scaleFactor()}")
            #print(f"context.mapToPixel().mapUnitsPerPixel() = {context.mapToPixel().mapUnitsPerPixel()}")
        if not num_points:
            num_points = self.brush_points

        points = []

        for i in range(num_points-1):
            theta = i * (2.0 * pi / (num_points-1))
            p = QgsPointXY(center.x() + radius * cos(theta),
                         center.y() + radius * sin(theta))
            points.append(p)
        
        return QgsGeometry.fromPolygonXY([points])

    def canvasPressEvent(self, event):
        """
        The following needs to happen:
          - apply the current brush to the rubber band
          - start tracking mouse movement

        """
        layer=self.canvas.currentLayer()

        # Left click
        if event.button() == Qt.LeftButton:
            self.mouse_state = 'drawing_with_brush'
            point = self.toMapCoordinates(event.pos())
            #self.rb.reset(QgsWkbTypes.LineGeometry)
            #self.rb.addPoint(point)
            self.rb.reset(QgsWkbTypes.PolygonGeometry)
            self.rb.setToGeometry(self.circle_around_point(point))
        
        # if e.button() == Qt.LeftButton:
        #     if self.status == 0:
        #         self.rb.reset(QgsWkbTypes.LineGeometry)
        #         self.status = 1
        #     self.rb.addPoint(self.toMapCoordinates(e.pos()))
        # else:
        #     if self.rb.numberOfVertices() > 2:
        #         self.status = 0
        #         self.selectionDone.emit()
        #     else:
        #         self.reset()

    def canvasMoveEvent(self, event):
        """
        The following needs to happen:
          - track how far the mouse has moved since canvasPressEvent
          - once a threshold value is reached, apply current brush to rubber
            band and merge with existing rubber band
            - note: the threshold value should simply be 1-99% of the brush's
              current diameter
        """
        layer=self.canvas.currentLayer()

        if self.mouse_state == 'drawing_with_brush':
            point = self.toMapCoordinates(event.pos())
            #self.rb.addPoint(point)
            previous_geom = self.rb.asGeometry()
            current_geom = self.circle_around_point(point)
            self.rb.setToGeometry(previous_geom.combine(current_geom))

    def canvasReleaseEvent(self, event):
        """
        The following needs to happen:
          - check to see if rubber band intersects with any of the active feature
          - if so, add...
        """
        layer=self.canvas.currentLayer()

        # BeePen
        if not self.rb:
            return
        
        if self.rb.numberOfVertices() > 2: #TODO: not necessary
            geom = self.rb.asGeometry()
        else:
            geom = None

        self.rbFinished.emit(self.rb.asGeometry())

        # reset rubberband and refresh the canvas
        self.rb.reset()
        self.canvas.refresh()

        self.mouse_state = 'free'

    def drawBrushStrokeToPolygon(self):
        geom = self.rb.asGeometry()
        scale = self.canvas.scale()


    def reset(self):
        self.status = 0
        self.rb.reset(True)

    def deactivate(self):
        self.rb.reset(True)
        QgsMapTool.deactivate(self)

class BrushRubberBand(QgsRubberBand):
    """Subclass of QgsRubberBand customized to behave more like a brush tool"""
    def __init__(self, mapCanvas, geometryType):
        super().__init__(mapCanvas, geometryType)
    
    def paint(self, event):
        painter = QPainter()
        painter.begin(self)

    # def mousePressEvent(self, e):
    #     pass
    
    # def mouseMoveEvent(self, e):
    #     pass

    # def mouseReleaseEvent(self, e):
    #     pass
    