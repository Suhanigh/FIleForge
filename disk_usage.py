from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from collections import defaultdict

class DiskUsageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Disk Usage Visualization')
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Show Usage button
        self.usage_btn = QPushButton('Show Usage', clicked=self.show_usage)
        layout.addWidget(self.usage_btn)
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

    def show_usage(self):
        if not self.folder:
            return
        usage = defaultdict(int)
        for root, dirs, files in os.walk(self.folder):
            for f in files:
                ext = os.path.splitext(f)[1].lower() or 'Other'
                path = os.path.join(root, f)
                try:
                    size = os.path.getsize(path)
                    usage[ext] += size
                except Exception:
                    continue
        # Prepare data for pie chart
        labels = []
        sizes = []
        for ext, sz in usage.items():
            labels.append(ext if ext else 'Other')
            sizes.append(sz / (1024*1024))  # MB
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if sizes:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            ax.set_title('Disk Usage by File Type (MB)')
        else:
            ax.text(0.5, 0.5, 'No files found', ha='center', va='center')
        self.canvas.draw() 