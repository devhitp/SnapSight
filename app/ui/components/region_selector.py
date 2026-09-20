"""
Region selection overlay component.
"""
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class RegionSelector(QWidget):
    # Emits the selected QRect on success, or an empty QRect on cancellation
    region_selected = Signal(QRect)

    def __init__(self):
        super().__init__()
        
        # Make the window frameless, stay on top, and behave as a tool window
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.MaximizeUsingFullscreenGeometryHint
        )
        
        # Transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setCursor(Qt.CrossCursor)
        
        # Set geometry to cover all screens (virtual desktop)
        desktop_rect = QRect()
        for screen in QApplication.screens():
            desktop_rect = desktop_rect.united(screen.geometry())
        
        self.setGeometry(desktop_rect)
        
        self.start_point = QPoint()
        self.current_point = QPoint()
        self.is_selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Dim the entire screen
        overlay_color = QColor(0, 0, 0, 100) # Semi-transparent black
        painter.fillRect(self.rect(), overlay_color)
        
        if self.is_selecting and not self.start_point.isNull() and not self.current_point.isNull():
            # Calculate the selected rectangle
            selection_rect = QRect(self.start_point, self.current_point).normalized()
            
            # Clear the overlay inside the selection (make it fully transparent)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.transparent)
            
            # Draw a border around the selection
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(0, 150, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.globalPosition().toPoint()
            self.current_point = self.start_point
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.current_point = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.current_point = event.globalPosition().toPoint()
            
            selection_rect = QRect(self.start_point, self.current_point).normalized()
            
            # Safely reject invalid/empty selections
            if selection_rect.width() <= 5 or selection_rect.height() <= 5:
                self.cancel_selection()
                return
                
            self.region_selected.emit(selection_rect)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_selection()

    def cancel_selection(self):
        self.region_selected.emit(QRect())
        self.close()
