from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal
import os, hashlib

class DuplicateScanThread(QThread):
    result = Signal(list, object)  # (duplicates, error)
    
    def __init__(self, folder, by_hash=True, chunk_size=8*1024*1024):  # 8MB chunks
        super().__init__()
        self.folder = folder
        self.by_hash = by_hash
        self.chunk_size = chunk_size
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def _calculate_file_hash(self, filepath):
        """Calculate file hash in chunks to manage memory usage"""
        try:
            h = hashlib.md5()
            with open(filepath, 'rb') as f:
                while True:
                    if self._stop_requested:
                        return None
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def run(self):
        try:
            duplicates = []
            groups = {}
            
            # First pass: group by size
            for root, dirs, files in os.walk(self.folder):
                if self._stop_requested:
                    return
                for f in files:
                    if self._stop_requested:
                        return
                    path = os.path.join(root, f)
                    try:
                        size = os.path.getsize(path)
                        if size > 0:  # Skip empty files
                            groups.setdefault(size, []).append({'path': path, 'size': size})
                    except Exception:
                        continue

            # Second pass: check hashes for files with same size
            for group in groups.values():
                if self._stop_requested:
                    return
                if len(group) < 2:
                    continue
                if self.by_hash:
                    hash_map = {}
                    for file in group:
                        if self._stop_requested:
                            return
                        file['hash'] = self._calculate_file_hash(file['path'])
                        if file['hash'] is not None:
                            hash_map.setdefault(file['hash'], []).append(file)
                    for g in hash_map.values():
                        if len(g) > 1:
                            duplicates.append(g)
                else:
                    if len(group) > 1:
                        duplicates.append(group)

            self.result.emit(duplicates, None)
        except Exception as e:
            self.result.emit([], e)

class DuplicateFinderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Duplicate Finder')
        self.setMinimumSize(700, 400)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Criteria
        crit_layout = QHBoxLayout()
        self.by_name = QCheckBox('Name')
        self.by_size = QCheckBox('Size'); self.by_size.setChecked(True)
        self.by_hash = QCheckBox('Content Hash'); self.by_hash.setChecked(True)
        crit_layout.addWidget(QLabel('Match by:'))
        crit_layout.addWidget(self.by_name)
        crit_layout.addWidget(self.by_size)
        crit_layout.addWidget(self.by_hash)
        layout.addLayout(crit_layout)
        # Scan button
        self.scan_btn = QPushButton('Scan', clicked=self.start_scan)
        layout.addWidget(self.scan_btn)
        # Results table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['Keep', 'File', 'Size'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        # Delete button
        self.delete_btn = QPushButton('Delete Selected', clicked=self.delete_selected)
        self.delete_btn.setEnabled(False)
        layout.addWidget(self.delete_btn)
        self.progress = None
        self.duplicates = []
        self.folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)

    def start_scan(self):
        if not self.folder:
            QMessageBox.warning(self, 'Duplicate Finder', 'Please select a folder.')
            return
        self.table.setRowCount(0)
        self.progress = QProgressDialog('Scanning for duplicates...', None, 0, 0, self)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.show()
        self.scan_btn.setEnabled(False)
        self.thread = DuplicateScanThread(
            self.folder, self.by_name.isChecked(), self.by_size.isChecked(), self.by_hash.isChecked())
        self.thread.result.connect(self.show_results)
        self.thread.start()

    def show_results(self, duplicates, error):
        self.progress.close()
        self.scan_btn.setEnabled(True)
        self.delete_btn.setEnabled(bool(duplicates))
        self.duplicates = duplicates
        self.table.setRowCount(0)
        if error:
            QMessageBox.critical(self, 'Error', str(error))
            return
        for group in duplicates:
            for i, file in enumerate(group):
                row = self.table.rowCount()
                self.table.insertRow(row)
                keep = QCheckBox()
                keep.setChecked(i == 0)  # Suggest keeping the first
                self.table.setCellWidget(row, 0, keep)
                self.table.setItem(row, 1, QTableWidgetItem(file['path']))
                self.table.setItem(row, 2, QTableWidgetItem(str(file['size'])))
        if not duplicates:
            QMessageBox.information(self, 'Duplicate Finder', 'No duplicates found!')

    def delete_selected(self):
        to_delete = []
        for row in range(self.table.rowCount()):
            keep = self.table.cellWidget(row, 0)
            if not keep.isChecked():
                path = self.table.item(row, 1).text()
                to_delete.append(path)
        if not to_delete:
            QMessageBox.information(self, 'Delete', 'No files selected for deletion.')
            return
        reply = QMessageBox.question(self, 'Delete', f'Delete {len(to_delete)} files?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for path in to_delete:
                try:
                    os.remove(path)
                except Exception:
                    pass
            QMessageBox.information(self, 'Delete', f'Deleted {len(to_delete)} files.')
            self.start_scan() 