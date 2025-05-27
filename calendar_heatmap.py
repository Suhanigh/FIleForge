from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
import os, datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import calendar

class CalendarHeatmapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('File Activity Heatmap')
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Show Heatmap button
        self.show_heatmap_btn = QPushButton('Show Heatmap', clicked=self.show_heatmap)
        layout.addWidget(self.show_heatmap_btn)
        # Chart area
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)

    def show_heatmap(self):
        if not self.folder:
            return
        # Collect file modification dates
        dates = []
        for root, dirs, files in os.walk(self.folder):
            for f in files:
                path = os.path.join(root, f)
                try:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    dates.append(mtime.date())
                except Exception:
                    continue
        # Aggregate activity by day
        activity = {}
        for date in dates:
            activity[date] = activity.get(date, 0) + 1
        # Prepare data for heatmap (last year)
        today = datetime.date.today()
        one_year_ago = today - datetime.timedelta(days=365)
        dates_in_year = [one_year_ago + datetime.timedelta(days=i) for i in range(366)] # +1 for inclusive range
        heatmap_data = np.zeros((7, 53)) # 7 days a week, ~53 weeks a year
        for d in dates_in_year:
            if d < one_year_ago or d > today: # Ensure dates are within range (handles leap year)
                 continue
            week_of_year = d.isocalendar()[1]
            day_of_week = d.weekday() # Monday is 0, Sunday is 6
            col = week_of_year - 1
            row = day_of_week
            if d in activity:
                 heatmap_data[row, col] = activity[d]
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='Blues', aspect='auto')
        # Configure axes
        ax.set_yticks(np.arange(7))
        ax.set_yticklabels([calendar.day_abbr[i] for i in range(7)])
        ax.set_xticks(np.arange(0, 53, 4)) # Show weeks every 4 weeks
        ax.set_xticklabels([f'Week {i+1}' for i in np.arange(0, 53, 4)])
        ax.set_title('File Activity Heatmap (Last Year)')
        self.figure.colorbar(cax, label='File Activity Count')
        self.canvas.draw() 