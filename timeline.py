from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
import os, datetime, subprocess, sys

class TimelineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder = None
        self.files = []
        self.current_page = 0
        self.items_per_page = 100
        self.setWindowTitle('Timeline')
        self.setGeometry(200, 200, 800, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_layout.addWidget(self.folder_label)
        select_button = QPushButton('Select Folder')
        select_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(select_button)
        layout.addLayout(folder_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Path', 'Date', 'Size (KB)'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous')
        self.prev_button.clicked.connect(self.previous_page)
        self.prev_button.setEnabled(False)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_label = QLabel('Page 1')
        pagination_layout.addWidget(self.page_label)
        
        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        pagination_layout.addWidget(self.next_button)
        
        layout.addLayout(pagination_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        open_button = QPushButton('Open Selected')
        open_button.clicked.connect(self.open_selected)
        button_layout.addWidget(open_button)
        
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
            self.current_page = 0
            self.show_timeline()

    def show_timeline(self):
        if not self.folder:
            QMessageBox.warning(self, 'Timeline', 'Please select a folder.')
            return

        # Collect file information in a separate thread
        self.files = []
        for root, dirs, filenames in os.walk(self.folder):
            for f in filenames:
                path = os.path.join(root, f)
                try:
                    stat = os.stat(path)
                    self.files.append({
                        'path': path,
                        'date': stat.st_mtime,
                        'size': stat.st_size
                    })
                except Exception:
                    continue

        # Sort by date
        self.files.sort(key=lambda x: x['date'], reverse=True)
        
        # Update pagination
        total_pages = (len(self.files) + self.items_per_page - 1) // self.items_per_page
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)
        self.page_label.setText(f'Page {self.current_page + 1} of {total_pages}')
        
        # Display current page
        self.display_current_page()

    def display_current_page(self):
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.files))
        
        self.table.setRowCount(0)
        for i in range(start_idx, end_idx):
            file = self.files[i]
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(file['path']))
            self.table.setItem(row, 1, QTableWidgetItem(
                datetime.datetime.fromtimestamp(file['date']).strftime('%Y-%m-%d %H:%M')))
            self.table.setItem(row, 2, QTableWidgetItem(f"{file['size']//1024}"))

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_timeline()

    def next_page(self):
        total_pages = (len(self.files) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.show_timeline()

    def open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Open', 'No file selected.')
            return
        path = self.table.item(row, 0).text()
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
        except Exception as e:
            QMessageBox.critical(self, 'Open', str(e)) 