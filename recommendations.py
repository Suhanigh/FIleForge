from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox
from PySide6.QtCore import Qt
import os, datetime, subprocess, sys, shutil

class RecommendationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('File Recommendations')
        self.setMinimumSize(800, 450)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Scan button
        self.scan_btn = QPushButton('Show Recommendations', clicked=self.show_recommendations)
        layout.addWidget(self.scan_btn)
        # Results table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Select', 'File', 'Last Accessed', 'Last Modified', 'Size (KB)', 'Suggested Action'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        # Action buttons
        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton('Open Selected', clicked=self.open_selected)
        self.archive_btn = QPushButton('Archive Selected', clicked=self.archive_selected)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.archive_btn)
        layout.addLayout(btn_layout)
        self.folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)

    def show_recommendations(self):
        if not self.folder:
            QMessageBox.warning(self, 'Recommendations', 'Please select a folder.')
            return
        files = []
        now = datetime.datetime.now().timestamp()
        for root, dirs, filenames in os.walk(self.folder):
            for f in filenames:
                path = os.path.join(root, f)
                try:
                    stat = os.stat(path)
                    files.append({
                        'path': path,
                        'atime': stat.st_atime,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    })
                except Exception:
                    continue
        # Sort by most recently accessed/modified
        files.sort(key=lambda x: max(x['atime'], x['mtime']), reverse=True)
        top_files = files[:30]
        self.table.setRowCount(0)
        for file in top_files:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # Checkbox for selection
            select = QCheckBox()
            self.table.setCellWidget(row, 0, select)
            self.table.setItem(row, 1, QTableWidgetItem(file['path']))
            self.table.setItem(row, 2, QTableWidgetItem(datetime.datetime.fromtimestamp(file['atime']).strftime('%Y-%m-%d %H:%M')))
            self.table.setItem(row, 3, QTableWidgetItem(datetime.datetime.fromtimestamp(file['mtime']).strftime('%Y-%m-%d %H:%M')))
            self.table.setItem(row, 4, QTableWidgetItem(f"{file['size']//1024}"))
            # Suggested Action
            days_since_access = (now - file['atime']) / (60*60*24)
            if days_since_access > 60:
                self.table.setItem(row, 5, QTableWidgetItem('Archive?'))
            else:
                self.table.setItem(row, 5, QTableWidgetItem(''))

    def open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Open', 'No file selected.')
            return
        path = self.table.item(row, 1).text()
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
        except Exception as e:
            QMessageBox.critical(self, 'Open', str(e))

    def archive_selected(self):
        to_archive = []
        for row in range(self.table.rowCount()):
            select = self.table.cellWidget(row, 0)
            if select.isChecked():
                path = self.table.item(row, 1).text()
                to_archive.append(path)
        if not to_archive:
            QMessageBox.information(self, 'Archive', 'No files selected for archiving.')
            return
        archive_dir = os.path.join(self.folder, 'Archive')
        os.makedirs(archive_dir, exist_ok=True)
        for path in to_archive:
            try:
                shutil.move(path, os.path.join(archive_dir, os.path.basename(path)))
            except Exception:
                pass
        QMessageBox.information(self, 'Archive', f'Archived {len(to_archive)} files.')
        self.show_recommendations() 