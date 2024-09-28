# main.py

import sys
import win32api
import win32con
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg



def draw_windows_and_monitors(windows, monitors, plot, virtual_screen_width, virtual_screen_height):
    """Draw monitors and visible windows on the plot."""
    plot.clear()

    # Draw monitors
    for monitor in monitors:
        left, top, right, bottom = monitor['monitor_rect']
        width = right - left
        height = bottom - top
        pen = pg.mkPen(color=(0, 0, 255, 125), width=2)
        brush = pg.mkBrush(color=(0, 0, 255, 50))
        monitor_rect = QtWidgets.QGraphicsRectItem(left, top, width, height)
        monitor_rect.setPen(pen)
        monitor_rect.setBrush(brush)
        plot.addItem(monitor_rect)

        # Draw work area (excluding taskbar)
        work_left, work_top, work_right, work_bottom = monitor['work_area_rect']
        work_width = work_right - work_left
        work_height = work_bottom - work_top
        pen = pg.mkPen(color=(0, 255, 0, 125), width=2)
        brush = pg.mkBrush(color=(0, 255, 0, 50))
        work_area_rect = QtWidgets.QGraphicsRectItem(work_left, work_top, work_width, work_height)
        work_area_rect.setPen(pen)
        work_area_rect.setBrush(brush)
        plot.addItem(work_area_rect)

    # Draw windows
    for window in windows:
        if not window['visible']:
            continue

        visible_region = window['visible_region']
        if not visible_region:
            continue

        left, top, right, bottom = visible_region
        width = right - left
        height = bottom - top
        pen = pg.mkPen(color=(255, 0, 0, 125), width=2)
        brush = pg.mkBrush(color=(255, 0, 0, 50))
        window_rect = QtWidgets.QGraphicsRectItem(left, top, width, height)
        window_rect.setPen(pen)
        window_rect.setBrush(brush)
        plot.addItem(window_rect)

        # Add window title
        title_text = pg.TextItem(window['title'], color=(255, 255, 255, 255))
        title_text.setPos(left + 5, top + 5)
        plot.addItem(title_text)


def main():
    # Initialize the PyQtGraph window
    app = QApplication([])
    win_graph = pg.GraphicsLayoutWidget(show=True)
    win_graph.setWindowTitle('Visible Windows and Overlap')

    # Create the plot and set limits
    plot = win_graph.addPlot()
    virtual_screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    virtual_screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    plot.setXRange(0, virtual_screen_width)
    plot.setYRange(0, virtual_screen_height)
    plot.invertY(True)  # Invert Y-axis to match screen coordinates

    def update_data():
        """Update monitors and windows data and redraw the plot."""
        windows, monitors = WindowInfo.get_window_data()
        draw_windows_and_monitors(windows, monitors, plot, virtual_screen_width, virtual_screen_height)

    # Initial drawing
    update_data()

    # Set the timer to update the plot every second
    timer = QtCore.QTimer()
    timer.timeout.connect(update_data)
    timer.start(1000)  # 1000 milliseconds = 1 second

    # Run the application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
