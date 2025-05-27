from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QCheckBox, QLineEdit, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal
import os, shutil, datetime

class OrganizeThread(QThread):
    result = Signal(str, object)
    
    def __init__(self, folder, archive_old=False, archive_days=365, 
                 archive_large=False, archive_size=100*1024*1024,  # 100MB
                 remove_empty=False, chunk_size=8*1024*1024):  # 8MB chunks
        super().__init__()
        self.folder = folder
        self.archive_old = archive_old
        self.archive_days = archive_days
        self.archive_large = archive_large
        self.archive_size = archive_size
        self.remove_empty = remove_empty
        self.chunk_size = chunk_size
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def _chunked_file_move(self, src_path, dest_path):
        """Move a file in chunks to manage memory usage"""
        try:
            # First try direct move
            shutil.move(src_path, dest_path)
        except OSError:
            # If direct move fails, copy and delete
            with open(src_path, 'rb') as fsrc:
                with open(dest_path, 'wb') as fdst:
                    while True:
                        if self._stop_requested:
                            return False
                        chunk = fsrc.read(self.chunk_size)
                        if not chunk:
                            break
                        fdst.write(chunk)
            os.remove(src_path)
        return True

    def run(self):
        try:
            organized = 0
            archived = 0
            removed = 0
            
            # Create archive directory if needed
            if self.archive_old or self.archive_large:
                archive_dir = os.path.join(self.folder, 'Archive')
                os.makedirs(archive_dir, exist_ok=True)
            
            # Process files
            for root, dirs, files in os.walk(self.folder):
                if self._stop_requested:
                    return
                
                # Skip Archive directory
                if os.path.basename(root) == 'Archive':
                    continue
                
                # Archive old files
                if self.archive_old:
                    cutoff = datetime.datetime.now() - datetime.timedelta(days=self.archive_days)
                    for f in files:
                        if self._stop_requested:
                            return
                        src_path = os.path.join(root, f)
                        try:
                            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(src_path))
                            if mtime < cutoff:
                                dest_path = os.path.join(archive_dir, f)
                                if self._chunked_file_move(src_path, dest_path):
                                    archived += 1
                        except Exception:
                            continue
                
                # Archive large files
                if self.archive_large:
                    for f in files:
                        if self._stop_requested:
                            return
                        src_path = os.path.join(root, f)
                        try:
                            size = os.path.getsize(src_path)
                            if size > self.archive_size:
                                dest_path = os.path.join(archive_dir, f)
                                if self._chunked_file_move(src_path, dest_path):
                                    archived += 1
                        except Exception:
                            continue
                
                # Remove empty folders
                if self.remove_empty:
                    for d in dirs:
                        if self._stop_requested:
                            return
                        dir_path = os.path.join(root, d)
                        try:
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                                removed += 1
                        except Exception:
                            continue
            
            message = f"Organization complete. Archived {archived} files, removed {removed} empty folders."
            self.result.emit(message, None)
        except Exception as e:
            self.result.emit("", e)

class SmartOrganizerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Smart Organizer')
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('No folder selected')
        folder_btn = QPushButton('Choose Folder', clicked=self.choose_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)
        # Organize by
        self.by_type = QCheckBox('Type (Documents, Images, etc.)')
        self.by_date = QCheckBox('Date (Year/Month)')
        self.by_tag = QCheckBox('Keyword/Tag:')
        self.tag_input = QLineEdit(); self.tag_input.setPlaceholderText('e.g. Resume, Invoice')
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(self.by_tag)
        tag_layout.addWidget(self.tag_input)
        layout.addWidget(self.by_type)
        layout.addWidget(self.by_date)
        layout.addLayout(tag_layout)
        # Archive options
        self.archive_old = QCheckBox('Archive files older than (days):')
        self.archive_days = QLineEdit('180'); self.archive_days.setFixedWidth(60)
        self.archive_large = QCheckBox('Archive files larger than (MB):')
        self.archive_size = QLineEdit('100'); self.archive_size.setFixedWidth(60)
        archive_layout = QHBoxLayout()
        archive_layout.addWidget(self.archive_old)
        archive_layout.addWidget(self.archive_days)
        archive_layout.addWidget(self.archive_large)
        archive_layout.addWidget(self.archive_size)
        layout.addLayout(archive_layout)
        # Remove empty folders
        self.remove_empty = QCheckBox('Remove empty folders')
        layout.addWidget(self.remove_empty)
        # Batch rename
        rename_layout = QHBoxLayout()
        self.rename_pattern = QLineEdit(); self.rename_pattern.setPlaceholderText('Batch rename pattern (e.g. photo_{num}.{ext})')
        rename_layout.addWidget(QLabel('Batch Rename:'))
        rename_layout.addWidget(self.rename_pattern)
        layout.addLayout(rename_layout)
        # Organize button
        self.organize_btn = QPushButton('Organize', clicked=self.start_organize)
        layout.addWidget(self.organize_btn)
        self.progress = None
        self.folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)

    def start_organize(self):
        if not self.folder:
            QMessageBox.warning(self, 'Smart Organizer', 'Please select a folder.')
            return
        self.progress = QProgressDialog('Organizing...', None, 0, 0, self)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.show()
        self.organize_btn.setEnabled(False)
        thread = OrganizeThread(
            self.folder,
            self.archive_old.isChecked(),
            int(self.archive_days.text() or '0'),
            self.archive_large.isChecked(),
            int(float(self.archive_size.text() or '0') * 1024 * 1024),
            self.remove_empty.isChecked()
        )
        thread.result.connect(self.show_result)
        thread.start()
        self.thread = thread

    def show_result(self, msg, error):
        self.progress.close()
        self.organize_btn.setEnabled(True)
        if error:
            QMessageBox.critical(self, 'Error', str(error))
        else:
            QMessageBox.information(self, 'Smart Organizer', msg) 