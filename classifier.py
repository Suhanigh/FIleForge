from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
import os, re

CATEGORIES = {
    'resume': ['resume', 'cv'],
    'invoice': ['invoice', 'bill', 'receipt'],
    'photo': ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
    'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.ipynb'],
    'pdf': ['.pdf'],
    'spreadsheet': ['.xls', '.xlsx', '.csv'],
    'presentation': ['.ppt', '.pptx'],
    'document': ['.doc', '.docx', '.txt', '.md'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'academic': ['thesis', 'paper', 'journal', 'research'],
}

class ClassifierDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI File Classifier')
        self.setMinimumSize(700, 400)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Classify button
        self.classify_btn = QPushButton('Classify', clicked=self.classify_files)
        layout.addWidget(self.classify_btn)
        # Results table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['File', 'Predicted Category'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)

    def classify_files(self):
        if not self.folder:
            QMessageBox.warning(self, 'Classifier', 'Please select a folder.')
            return
        files = []
        for root, dirs, filenames in os.walk(self.folder):
            for f in filenames:
                path = os.path.join(root, f)
                files.append(path)
        self.table.setRowCount(0)
        for path in files:
            category = self.predict_category(path)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path))
            self.table.setItem(row, 1, QTableWidgetItem(category))

    def predict_category(self, path):
        fname = os.path.basename(path).lower()
        ext = os.path.splitext(fname)[1]
        for cat, patterns in CATEGORIES.items():
            for pat in patterns:
                if pat.startswith('.') and fname.endswith(pat):
                    return cat.capitalize()
                elif pat in fname:
                    return cat.capitalize()
        # Optionally, add content-based rules here
        return 'Other' 