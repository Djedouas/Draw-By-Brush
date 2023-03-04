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
from qgis.core import QgsWkbTypes, QgsPointXY, QgsGeometry

from qgis.PyQt.QtCore import Qt, QCoreApplication, pyqtSignal, QPoint
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, \
    QGridLayout, QLabel, QGroupBox, QVBoxLayout, QComboBox, QPushButton, \
    QInputDialog
from qgis.PyQt.QtGui import QDoubleValidator, QIntValidator, QKeySequence

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

        # Save references to QGIS interface
        self.canvas = iface.mapCanvas()
        #QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.iface = iface
        
        # Configure Rubber Band
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb.setColor(color)
        self.rb.setWidth(20)

        self.mouse_state = 'free'
        
        self.reset()
        return None

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rb.reset(True)	 # true, its a polygon

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
            self.rb.reset(QgsWkbTypes.LineGeometry)
            self.rb.addPoint(point)
        
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
            self.rb.addPoint(point)

        # if self.rb.numberOfVertices() > 0 and self.status == 1:
        #     self.rb.removeLastPoint(0)
        #     self.rb.addPoint(self.toMapCoordinates(e.pos()))
        # self.move.emit()

    def canvasReleaseEvent(self, event):
        """
        The following needs to happen:
          - check to see if rubber band intersects with any of the active feature
          - if so, add...
        """
        layer=self.canvas.currentLayer()

        # if self.mouse_state != 'free':
        #     self.drawBrushStrokeToPolygon()
        #     self.mouse_state = 'free'

        # BeePen
        if not self.rb:
            return
        
        if self.rb.numberOfVertices() > 2:
            print('number of vertices is greater than 2')
            geom = self.rb.asGeometry()
        else:
            geom = None

        # try:
        self.rbFinished.emit(geom)
        #self.selectionDone.emit()
        print('emitted line of length '+str(len(geom.asPolyline())))
        # except:
        #     pass

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
        QgsMapTool.deactivate(self)    def __init__(self, mapCanvas, geometryType):
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
    