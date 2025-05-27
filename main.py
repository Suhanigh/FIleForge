import sys
import os
import shutil
import psutil
import zipfile
import tempfile
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLineEdit, QCheckBox, QComboBox, QPushButton, QTreeView, QListView, QFileSystemModel, QTabWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QGroupBox, QFormLayout, QMessageBox, QTextEdit, QStatusBar, QProgressDialog, QMenu
from PySide6.QtCore import Qt, QDir, QTimer, QThread, Signal, QDateTime
from PySide6.QtGui import QIcon, QPixmap, QAction
from preferences import PreferencesDialog
from duplicate_finder import DuplicateFinderDialog
from smart_organizer import SmartOrganizerDialog
from tagging import TaggingDialog
from search import SearchDialog
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
import base64
import getpass
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
from recommendations import RecommendationsDialog
from classifier import ClassifierDialog
from disk_usage import DiskUsageDialog
from timeline import TimelineDialog
from calendar_heatmap import CalendarHeatmapDialog
from reminder_dialog import ReminderDialog, load_reminders, save_reminders
import datetime
import subprocess
from google_drive_auth import authenticate_google_drive # Import authentication function
from cloud_config import save_google_credentials, load_google_credentials, clear_google_credentials # Import config functions
from google_drive_model import GoogleDriveModel # Import the Google Drive model

# --- Threading Example for Background Tasks ---
class WorkerThread(QThread):
    result = Signal(object)
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def run(self):
        res = self.func(*self.args, **self.kwargs)
        self.result.emit(res)

class FileOperationThread(QThread):
    finished = Signal(object, object)  # result, error
    progress = Signal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result, None)
        except Exception as e:
            self.finished.emit(None, e)

    def update_progress(self, message):
        """Emit a progress update signal"""
        self.progress.emit(message)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

class FileForgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileForge")
        self.setGeometry(100, 100, 1400, 850)
        self.tags = {}  # {filepath: [tags]}
        self.dark_mode = False
        self.file_cache = {}  # Cache for frequently accessed files
        self.cache_size_limit = 100 * 1024 * 1024  # 100MB cache limit
        self.current_cache_size = 0
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks for large file operations

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        self.google_drive_credentials = None

        self._init_ui()
        self._init_performance_monitor()
        self._init_notification_timer()
        self._init_cache_cleanup_timer()

    def _init_cache_cleanup_timer(self):
        self.cache_cleanup_timer = QTimer(self)
        self.cache_cleanup_timer.timeout.connect(self._cleanup_cache)
        self.cache_cleanup_timer.start(300000)  # Clean cache every 5 minutes

    def _cleanup_cache(self):
        if self.current_cache_size > self.cache_size_limit:
            # Remove oldest entries until we're under the limit
            while self.current_cache_size > self.cache_size_limit and self.file_cache:
                oldest_key = next(iter(self.file_cache))
                self.current_cache_size -= len(self.file_cache[oldest_key])
                del self.file_cache[oldest_key]

    def _chunked_file_copy(self, src, dst):
        """Copy a file in chunks to manage memory usage"""
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                while True:
                    chunk = fsrc.read(self.chunk_size)
                    if not chunk:
                        break
                    fdst.write(chunk)

    def _chunked_file_read(self, filepath):
        """Read a file in chunks and cache it"""
        if filepath in self.file_cache:
            return self.file_cache[filepath]

        data = bytearray()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                data.extend(chunk)

        # Update cache
        self.current_cache_size += len(data)
        self.file_cache[filepath] = data
        self._cleanup_cache()
        return data

    def _init_ui(self):
        # --- Toolbar ---
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.actions = {}
        for name, handler in [
            ("New Folder", self.create_new_folder),
            ("Copy", self.copy_selected),
            ("Move", self.move_selected),
            ("Delete", self.delete_selected),
            ("Rename", self.rename_selected),
            ("Refresh", self.refresh_view),
            ("Search", self.search_files),
            ("Preview", self.preview_selected),
            ("Encrypt", self.encrypt_selected),
            ("Decrypt", self.decrypt_selected),
            ("Compress", self.compress_selected),
            ("Decompress", self.decompress_selected),
            ("Hide File", self.hide_selected),
            ("Unhide File", self.unhide_selected),
            ("Preferences", self.open_preferences),
            ("Duplicate Finder", self.find_duplicates),
            ("Smart Organize", self.smart_organize),
            ("Recommendations", self.open_recommendations),
            ("Classifier", self.open_classifier),
            ("Disk Usage", self.open_disk_usage),
            ("Timeline", self.open_timeline),
            ("Heatmap Calendar", self.open_heatmap_calendar),
        ]:
            action = QAction(name, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
            self.actions[name] = action
        toolbar.addSeparator()
        self.search_name = QLineEdit(); self.search_name.setPlaceholderText("Name")
        toolbar.addWidget(self.search_name)
        self.case_sensitive = QCheckBox("Case Sensitive")
        toolbar.addWidget(self.case_sensitive)
        self.search_type = QComboBox(); self.search_type.addItems(["All", "File", "Folder"])
        toolbar.addWidget(self.search_type)
        toolbar.addWidget(QPushButton("Search", clicked=self.search_files))
        toolbar.addWidget(QPushButton("Clear", clicked=self.clear_search))

        # --- Main Layout ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # --- Left: File Tree ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(QDir.homePath()))
        self.tree_view.clicked.connect(self.on_tree_clicked)
        left_layout.addWidget(self.tree_view)
        left_panel.setMaximumWidth(250)

        # --- Center: Tabbed File View ---
        center_tabs = QTabWidget()
        self.center_tabs = center_tabs
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        self.list_view = QListView()
        self.list_view.setModel(self.file_model)
        self.list_view.setRootIndex(self.file_model.index(QDir.homePath()))
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.file_context_menu)
        self.list_view.clicked.connect(self.on_list_clicked)
        files_layout.addWidget(self.list_view)
        center_tabs.addTab(files_tab, "Files")
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_label = QLabel("[Preview panel here]")
        preview_layout.addWidget(self.preview_label)
        center_tabs.addTab(preview_tab, "Preview")
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        self.search_results_table = QTableWidget(0, 4)
        self.search_results_table.setHorizontalHeaderLabels(["Name", "Path", "Type", "Tags"])
        search_layout.addWidget(self.search_results_table)
        center_tabs.addTab(search_tab, "Search Results")
        hidden_tab = QWidget()
        hidden_layout = QVBoxLayout(hidden_tab)
        self.hidden_files_list = QListWidget()
        hidden_layout.addWidget(self.hidden_files_list)
        center_tabs.addTab(hidden_tab, "Hidden Files")
        center_tabs.currentChanged.connect(self.on_tab_changed)

        # Add Google Drive tab
        google_drive_tab = QWidget()
        google_drive_layout = QVBoxLayout(google_drive_tab)

        # Google Drive Tree View
        self.google_drive_tree_view = QTreeView()
        self.google_drive_tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.google_drive_tree_view.customContextMenuRequested.connect(self.google_drive_context_menu)
        # TODO: Set custom model for Google Drive
        google_drive_layout.addWidget(self.google_drive_tree_view)
        
        # Google Drive List View
        self.google_drive_list_view = QListView()
        self.google_drive_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.google_drive_list_view.customContextMenuRequested.connect(self.google_drive_context_menu)
        # TODO: Set custom model for Google Drive
        google_drive_layout.addWidget(self.google_drive_list_view)

        center_tabs.addTab(google_drive_tab, "Google Drive")

        # --- Right: Preferences/Tags/Search ---
        right_panel = QTabWidget()
        pref_tab = QWidget()
        pref_layout = QVBoxLayout(pref_tab)
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        self.theme_combo = QComboBox(); self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(self.toggle_theme)
        theme_layout.addRow("Theme:", self.theme_combo)
        pref_layout.addWidget(theme_group)
        view_group = QGroupBox("View Options")
        view_layout = QVBoxLayout(view_group)
        self.show_tree = QCheckBox("Show Tree View"); self.show_tree.setChecked(True)
        self.show_details = QCheckBox("Show Details View"); self.show_details.setChecked(True)
        self.show_hidden = QCheckBox("Show Hidden Files"); self.show_hidden.stateChanged.connect(self.toggle_hidden_files)
        view_layout.addWidget(self.show_tree)
        view_layout.addWidget(self.show_details)
        view_layout.addWidget(self.show_hidden)
        pref_layout.addWidget(view_group)
        export_group = QGroupBox("Export/Save Directory")
        export_layout = QHBoxLayout(export_group)
        export_layout.addWidget(QLabel("Not set"))
        export_layout.addWidget(QPushButton("Choose..."))
        pref_layout.addWidget(export_group)
        right_panel.addTab(pref_tab, "Preferences")
        tags_tab = QWidget()
        tags_layout = QVBoxLayout(tags_tab)
        tags_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QTextEdit()
        tags_layout.addWidget(self.tags_edit)
        tags_layout.addWidget(QPushButton("Add", clicked=self.add_tag))
        self.tag_stats = QLabel("Tag Statistics: ")
        tags_layout.addWidget(self.tag_stats)
        right_panel.addTab(tags_tab, "Tags")
        right_search_tab = QWidget()
        right_search_layout = QVBoxLayout(right_search_tab)
        right_search_layout.addWidget(QLabel("No search results"))
        right_search_layout.addWidget(QLineEdit("Filter results..."))
        right_search_layout.addWidget(QCheckBox("Case Sensitive"))
        right_search_layout.addWidget(QPushButton("Clear Filters"))
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Name", "at", "Type", "Tags"])
        right_search_layout.addWidget(table)
        right_search_layout.addWidget(QPushButton("Export Results"))
        right_search_layout.addWidget(QPushButton("Clear Results"))
        right_panel.addTab(right_search_tab, "Search Results")
        right_panel.setMinimumWidth(320)
        right_panel.setMaximumWidth(400)

        # Add Reminders tab
        reminders_tab = QWidget()
        reminders_layout = QVBoxLayout(reminders_tab)
        
        # Add header and controls
        reminders_header = QHBoxLayout()
        reminders_header.addWidget(QLabel("Active Reminders"))
        refresh_btn = QPushButton("Refresh", clicked=self.refresh_reminders)
        reminders_header.addWidget(refresh_btn)
        reminders_layout.addLayout(reminders_header)
        
        # Add reminders list
        self.reminders_list = QTableWidget(0, 4)
        self.reminders_list.setHorizontalHeaderLabels(["File", "Due Date", "Recurrence", "Action"])
        self.reminders_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        reminders_layout.addWidget(self.reminders_list)
        
        # Add reminder controls
        reminder_controls = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected", clicked=self.delete_selected_reminder)
        edit_btn = QPushButton("Edit Selected", clicked=self.edit_selected_reminder)
        add_btn = QPushButton("Add New Reminder", clicked=self.add_new_reminder_from_tab)
        reminder_controls.addWidget(delete_btn)
        reminder_controls.addWidget(edit_btn)
        reminder_controls.addWidget(add_btn)
        reminders_layout.addLayout(reminder_controls)
        
        # Add filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.reminder_filter_edit = QLineEdit()
        self.reminder_filter_edit.textChanged.connect(self.filter_reminders)
        filter_layout.addWidget(self.reminder_filter_edit)
        self.reminder_filter_column = QComboBox()
        self.reminder_filter_column.addItems(["File", "Due Date", "Recurrence", "Action"])
        filter_layout.addWidget(self.reminder_filter_column)
        reminders_layout.addLayout(filter_layout)
        
        right_panel.addTab(reminders_tab, "Reminders")

        # Add Cloud Storage tab
        cloud_tab = QWidget()
        cloud_layout = QVBoxLayout(cloud_tab)
        
        cloud_layout.addWidget(QLabel("Cloud Storage Accounts:"))
        self.cloud_accounts_list = QListWidget()
        cloud_layout.addWidget(self.cloud_accounts_list)
        
        add_account_btn = QPushButton("Add Account", clicked=self.add_cloud_account)
        cloud_layout.addWidget(add_account_btn)
        
        # Add button to remove selected account
        remove_account_btn = QPushButton("Remove Selected Account", clicked=self.remove_cloud_account)
        cloud_layout.addWidget(remove_account_btn)

        right_panel.addTab(cloud_tab, "Cloud Storage")

        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_tabs, stretch=2)
        main_layout.addWidget(right_panel)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("CPU Usage: 0% | Memory Usage: 0%")

        # Enable sorting on the reminders table
        self.reminders_list.setSortingEnabled(True)
        
        # Initialize reminders list
        self.refresh_reminders()

        # Load saved cloud accounts
        self.load_saved_cloud_accounts()

        # Initialize Google Drive model if credentials exist
        self.google_drive_model = None
        if self.google_drive_credentials:
             self.google_drive_model = GoogleDriveModel(self.google_drive_credentials)
             self.google_drive_tree_view.setModel(self.google_drive_model)
             self.google_drive_list_view.setModel(self.google_drive_model)
             # Optionally set the root index for the list view to show children of the selected folder in the tree view
             self.google_drive_tree_view.clicked.connect(self.on_google_drive_tree_clicked)

    def _init_performance_monitor(self):
        self.perf_timer = QTimer(self)
        self.perf_timer.timeout.connect(self.update_performance)
        self.perf_timer.start(2000)
    def update_performance(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.status.showMessage(f"CPU Usage: {cpu}% | Memory Usage: {mem}%")

    def get_selected_path(self):
        index = self.list_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select a file or folder.")
            return None
        return self.file_model.filePath(index)

    def on_tree_clicked(self, index):
        path = self.file_model.filePath(index)
        self.list_view.setRootIndex(self.file_model.index(path))
        self.populate_hidden_files()
    def on_list_clicked(self, index):
        path = self.file_model.filePath(index)
        # Only update preview if Preview tab is active
        if self.center_tabs.tabText(self.center_tabs.currentIndex()) == "Preview":
            self.preview_selected()
        self.preview_label.setText(f"Preview: {path}")
        # TODO: Show preview (image/text/etc.)

    def toggle_hidden_files(self):
        # TODO: Show/hide hidden files in views
        pass

    def file_context_menu(self, pos):
        menu = QMenu()
        menu.addAction("Copy", self.copy_selected)
        menu.addAction("Move", self.move_selected)
        menu.addAction("Delete", self.delete_selected)
        menu.addAction("Rename", self.rename_selected)
        menu.addAction("Compress", self.compress_selected)
        menu.addAction("Decompress", self.decompress_selected)
        menu.addAction("Set Reminder", self.set_file_reminder)
        menu.exec_(self.list_view.viewport().mapToGlobal(pos))

    def create_new_folder(self):
        index = self.list_view.rootIndex()
        dir_path = self.file_model.filePath(index)
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            new_folder_path = os.path.join(dir_path, name)
            try:
                os.makedirs(new_folder_path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def copy_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Copy to...")
        if dest:
            def do_copy(src_path, dest_path):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting copy of {os.path.basename(src_path)}...")
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        self._chunked_file_copy(src_path, dest_path)
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Finished copying {os.path.basename(src_path)}.")
                    return dest_path
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Error copying {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                # on_thread_finished is already connected in run_in_thread
                if not error:
                    QMessageBox.information(self, "Copy Successful", f"Copied to {result}")

            # Call run_in_thread with the worker function and its arguments
            self.run_in_thread(do_copy, src, dest)

    def move_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Move to...")
        if dest:
            def do_move(src_path, dest_path):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting move of {os.path.basename(src_path)} to {os.path.basename(dest_path)}...")
                try:
                    shutil.move(src_path, dest_path)
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Finished moving {os.path.basename(src_path)}.")
                    return dest_path
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Error moving {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                if not error:
                    QMessageBox.information(self, "Move Successful", f"Moved to {result}")

            self.run_in_thread(do_move, src, dest)

    def delete_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        reply = QMessageBox.question(self, "Delete", f"Delete {os.path.basename(src)}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            def do_delete(src_path):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting deletion of {os.path.basename(src_path)}...")
                try:
                    if os.path.isdir(src_path):
                        shutil.rmtree(src_path)
                    else:
                        os.remove(src_path)
                    if isinstance(thread, FileOperationThread):
                         thread.update_progress(f"Finished deleting {os.path.basename(src_path)}.")
                    return f"{os.path.basename(src_path)} deleted."
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Error deleting {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                if not error:
                    QMessageBox.information(self, "Delete Successful", result)

            self.run_in_thread(do_delete, src)

    def rename_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:")
        if ok and new_name:
            dest = os.path.join(os.path.dirname(src), new_name)
            try:
                os.rename(src, dest)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def compress_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Compress to...", filter="Zip Files (*.zip)")
        if dest:
            def do_compress(src_path, dest_path):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting compression of {os.path.basename(src_path)}...")
                try:
                    with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        if os.path.isdir(src_path):
                            for root, dirs, files in os.walk(src_path):
                                for file in files:
                                    abs_path = os.path.join(root, file)
                                    rel_path = os.path.relpath(abs_path, os.path.dirname(src_path))
                                    if isinstance(thread, FileOperationThread):
                                        thread.update_progress(f"Compressing {file}...")
                                    zipf.write(abs_path, rel_path)
                        else:
                            if isinstance(thread, FileOperationThread):
                                thread.update_progress(f"Compressing {os.path.basename(src_path)}...")
                            zipf.write(src_path, os.path.basename(src_path))
                    if isinstance(thread, FileOperationThread):
                         thread.update_progress(f"Finished compressing {os.path.basename(src_path)}.")
                    return dest_path
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Error compressing {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                if not error:
                    QMessageBox.information(self, "Compression Successful", f"Compressed to {result}")

            self.run_in_thread(do_compress, src, dest)

    def decompress_selected(self):
        src = self.get_selected_path()
        if not src or not src.endswith('.zip'):
            QMessageBox.warning(self, "Not a zip file", "Please select a .zip file to decompress.")
            return
        dest = QFileDialog.getExistingDirectory(self, "Extract to...")
        if dest:
            def do_decompress(src_path, dest_path):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting decompression of {os.path.basename(src_path)}...")
                try:
                    with zipfile.ZipFile(src_path, 'r') as zipf:
                        # More advanced implementation would iterate through zipf.infolist() to report progress
                        zipf.extractall(dest_path)
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Finished decompressing {os.path.basename(src_path)}.")
                    return dest_path
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                         thread.update_progress(f"Error decompressing {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                if not error:
                    QMessageBox.information(self, "Decompression Successful", f"Decompressed to {result}")

            self.run_in_thread(do_decompress, src, dest)

    def hide_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        dirname, basename = os.path.split(src)
        if not basename.startswith('.'):
            new_path = os.path.join(dirname, '.' + basename)
            try:
                os.rename(src, new_path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def unhide_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        dirname, basename = os.path.split(src)
        if basename.startswith('.'):
            new_path = os.path.join(dirname, basename.lstrip('.'))
            try:
                os.rename(src, new_path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def encrypt_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        password, ok = QInputDialog.getText(self, "Encrypt", "Enter password:", QLineEdit.Password)
        if ok and password:
            def do_encrypt(src_path, password):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Starting encryption of {os.path.basename(src_path)}...")
                try:
                    salt = os.urandom(16)
                    key = derive_key(password, salt)
                    fernet = Fernet(key)
                    
                    if os.path.isdir(src_path):
                        if isinstance(thread, FileOperationThread):
                            thread.update_progress(f"Creating zip archive of {os.path.basename(src_path)}...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmpzip:
                            zip_path = tmpzip.name
                        shutil.make_archive(zip_path[:-4], 'zip', src_path)
                        data = self._chunked_file_read(zip_path)
                        os.remove(zip_path)
                        out_path = src_path.rstrip(os.sep) + ".zip.encrypted"
                    else:
                        data = self._chunked_file_read(src_path)
                        out_path = src_path + ".encrypted"
                    
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Encrypting data...")
                    
                    # Encrypt in chunks
                    encrypted = bytearray()
                    for i in range(0, len(data), self.chunk_size):
                        chunk = data[i:i + self.chunk_size]
                        encrypted.extend(fernet.encrypt(chunk))
                    
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Writing encrypted file {os.path.basename(out_path)}...")
                    
                    with open(out_path, 'wb') as f:
                        f.write(salt + encrypted)
                    
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Finished encrypting {os.path.basename(src_path)}.")
                    return out_path
                except Exception as e:
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Error encrypting {os.path.basename(src_path)}: {e}")
                    raise e

            def on_done(result, error):
                if not error:
                    QMessageBox.information(self, "Encrypt Successful", f"Encrypted as {result}")

            self.run_in_thread(do_encrypt, src, password)

    def decrypt_selected(self):
        src = self.get_selected_path()
        if not src or not src.endswith('.encrypted'):
            QMessageBox.warning(self, "Decrypt", "Please select a .encrypted file to decrypt.")
            return
        password, ok = QInputDialog.getText(self, "Decrypt File/Folder", "Enter password:", QLineEdit.Password)
        if not ok or not password:
            return
        def do_decrypt(src_path, password):
            thread = QThread.currentThread()
            if isinstance(thread, FileOperationThread):
                thread.update_progress(f"Starting decryption of {os.path.basename(src_path)}...")
            try:
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Reading encrypted data from {os.path.basename(src_path)}...")
                with open(src_path, 'rb') as f:
                    salt = f.read(16)
                    encrypted = f.read()
                
                key = derive_key(password, salt)
                fernet = Fernet(key)
                
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Decrypting data...")
                decrypted = fernet.decrypt(encrypted)
                
                if src_path.endswith('.zip.encrypted'):
                    if isinstance(thread, FileOperationThread):
                         thread.update_progress(f"Decompressing zip archive...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmpzip:
                        tmpzip.write(decrypted)
                        zip_path = tmpzip.name
                    extract_dir = src_path[:-15]
                    os.makedirs(extract_dir, exist_ok=True)
                    shutil.unpack_archive(zip_path, extract_dir)
                    os.remove(zip_path)
                    out_path = extract_dir
                    msg = f"Decrypted and extracted to {out_path}"
                else:
                    out_path = src_path[:-10]
                    if isinstance(thread, FileOperationThread):
                        thread.update_progress(f"Writing decrypted file {os.path.basename(out_path)}...")
                    with open(out_path, 'wb') as f:
                        f.write(decrypted)
                    msg = f"Decrypted as {os.path.basename(out_path)}"
                
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Finished decrypting {os.path.basename(src_path)}.")
                return msg
            except InvalidToken:
                 if isinstance(thread, FileOperationThread):
                     thread.update_progress("Error: Invalid password.")
                 QMessageBox.critical(self, "Decrypt Error", "Invalid password.")
                 raise ValueError("Invalid password.") # Re-raise to stop the thread
            except Exception as e:
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Error decrypting {os.path.basename(src_path)}: {e}")
                raise e

        def on_done(result, error):
            if not error and result:
                # Message box already shown in do_decrypt for InvalidToken
                pass # QMessageBox.information(self, "Decrypt Successful", result)

        self.run_in_thread(do_decrypt, src, password)

    def run_in_thread(self, func, *args, **kwargs):
        self.progress = QProgressDialog("Working...", None, 0, 0, self)
        self.progress.setWindowTitle("Please Wait")
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setCancelButton(None)
        self.progress.show()
        self.setEnabled(False)
        thread = FileOperationThread(func, *args, **kwargs)
        thread.finished.connect(lambda result, error: self.on_thread_finished(result, error, thread))
        thread.progress.connect(self.progress.setLabelText)
        thread.start()

    def on_thread_finished(self, result, error, thread):
        self.setEnabled(True)
        self.progress.close()
        thread.deleteLater()
        self.refresh_view()
        if error:
            QMessageBox.critical(self, "Error", str(error))

    def refresh_view(self):
        self.file_model.refresh()

    def search_files(self):
        dlg = SearchDialog(self)
        dlg.exec_()

    def clear_search(self):
        # TODO: Clear search filters/results
        self.search_name.clear()
        self.case_sensitive.setChecked(False)
        self.search_type.setCurrentIndex(0)
        self.search_results_table.setRowCount(0)

    def add_tag(self):
        dlg = TaggingDialog(self)
        dlg.exec_()

    def update_tag_stats(self):
        # TODO: Update tag statistics
        pass

    def preview_selected(self):
        src = self.get_selected_path()
        if not src:
            return
        ext = os.path.splitext(src)[1].lower()
        if os.path.isdir(src):
            self.preview_label.setText(f"Folder: {src}")
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            pixmap = QPixmap(src)
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(600, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.preview_label.setText(f"Could not load image: {src}")
        elif ext in ['.txt', '.md', '.py', '.log', '.json', '.csv']:
            try:
                with open(src, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)
                self.preview_label.setText(f"Text Preview:\n{content}")
            except Exception as e:
                self.preview_label.setText(f"Error reading file: {e}")
        elif ext == '.pdf':
            if HAS_PYMUPDF:
                try:
                    doc = fitz.open(src)
                    page = doc.load_page(0)
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("ppm")
                    from PySide6.QtCore import QByteArray
                    from PySide6.QtGui import QImage
                    image = QImage()
                    image.loadFromData(QByteArray(img_data))
                    self.preview_label.setPixmap(QPixmap.fromImage(image).scaled(600, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception as e:
                    self.preview_label.setText(f"Error previewing PDF: {e}")
            else:
                self.preview_label.setText("PDF preview requires PyMuPDF. Install with: pip install pymupdf")
        else:
            self.preview_label.setText(f"File: {src}\n(No preview available)")

    def find_duplicates(self):
        dlg = DuplicateFinderDialog(self)
        dlg.exec_()

    def smart_organize(self):
        dlg = SmartOrganizerDialog(self)
        dlg.exec_()

    def toggle_theme(self, theme):
        if theme == "Dark" or (isinstance(theme, bool) and theme):
            self.setStyleSheet("""
                QMainWindow { background: #232629; color: #f0f0f0; }
                QTreeView, QListView, QTableWidget { background: #2b2b2b; color: #f0f0f0; }
                QLabel, QCheckBox, QComboBox, QLineEdit { color: #f0f0f0; }
                QToolBar { background: #232629; }
            """)
            self.dark_mode = True
        else:
            self.setStyleSheet("")
            self.dark_mode = False

    def open_preferences(self):
        dlg = PreferencesDialog(self)
        dlg.exec_()

    def on_tab_changed(self, idx):
        tab_text = self.center_tabs.tabText(idx)
        if tab_text == "Hidden Files":
            self.populate_hidden_files()
        elif tab_text == "Preview":
            self.preview_selected()

    def populate_hidden_files(self):
        self.hidden_files_list.clear()
        # Get current directory from list_view root
        index = self.list_view.rootIndex()
        dir_path = self.file_model.filePath(index)
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)
        try:
            for name in os.listdir(dir_path):
                if name.startswith('.'):
                    self.hidden_files_list.addItem(name)
        except Exception as e:
            self.hidden_files_list.addItem(f"Error: {e}")

    def open_recommendations(self):
        dlg = RecommendationsDialog(self)
        dlg.exec_()

    def open_classifier(self):
        dlg = ClassifierDialog(self)
        dlg.exec_()

    def open_disk_usage(self):
        dlg = DiskUsageDialog(self)
        dlg.exec_()

    def open_timeline(self):
        dlg = TimelineDialog(self)
        dlg.exec_()

    def open_heatmap_calendar(self):
        dlg = CalendarHeatmapDialog(self)
        dlg.exec_()

    def set_file_reminder(self):
        selected_path = self.get_selected_path()
        if selected_path:
            dlg = ReminderDialog(selected_path, self)
            dlg.exec_()

    def add_new_reminder_from_tab(self):
        """Adds a new reminder for the currently selected file from the Reminders tab"""
        self.set_file_reminder()

    # --- Smart Notifications (Checking Reminders) ---
    def _init_notification_timer(self):
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_reminders)
        self.notification_timer.start(60000) # Check every 60 seconds

    def check_reminders(self):
        reminders = load_reminders()
        now = QDateTime.currentDateTime()
        reminders_to_show = []
        reminders_to_keep = []
        for reminder in reminders:
            due_datetime = QDateTime.fromString(reminder['datetime'], Qt.ISODate)
            if due_datetime <= now:
                reminders_to_show.append(reminder)
                # Handle recurrence
                if reminder['recurrence'] == 'Daily':
                    reminder['datetime'] = due_datetime.addDays(1).toString(Qt.ISODate)
                    reminders_to_keep.append(reminder)
                elif reminder['recurrence'] == 'Weekly':
                    reminder['datetime'] = due_datetime.addDays(7).toString(Qt.ISODate)
                    reminders_to_keep.append(reminder)
                elif reminder['recurrence'] == 'Monthly':
                    reminder['datetime'] = due_datetime.addMonths(1).toString(Qt.ISODate)
                    reminders_to_keep.append(reminder)
                elif reminder['recurrence'] == 'Yearly':
                    reminder['datetime'] = due_datetime.addYears(1).toString(Qt.ISODate)
                    reminders_to_keep.append(reminder)
                # else: single reminder, not kept
            else:
                reminders_to_keep.append(reminder)
        save_reminders(reminders_to_keep)
        for reminder in reminders_to_show:
            self.trigger_notification(reminder)

    def trigger_notification(self, reminder):
        message = f"Reminder for {os.path.basename(reminder['file_path'])}"
        if reminder['message']:
            message += f": {reminder['message']}"
        action = reminder['action']
        
        if action == 'Notify Only':
            # Attempt to send a system notification
            try:
                if sys.platform.startswith('darwin'): # macOS
                    subprocess.run(['osascript', '-e', f'display notification "{message}" with title "FileForge Reminder" sound name "Hero"'])
                elif sys.platform.startswith('linux'): # Linux
                    # Requires notify-send utility
                    subprocess.run(['notify-send', 'FileForge Reminder', message])
                else:
                    # Fallback to QMessageBox for other platforms (e.g., Windows) or if commands fail
                    QMessageBox.information(self, "File Reminder", message)
            except Exception as e:
                print(f"Error sending system notification: {e}") # Print error for debugging
                # Fallback to QMessageBox if system notification fails
                QMessageBox.information(self, "File Reminder", message)
                
        elif action == 'Open File':
            reply = QMessageBox.information(self, "File Reminder", message + "\nOpen file?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    if sys.platform.startswith('darwin'):
                        subprocess.call(('open', reminder['file_path']))
                    elif os.name == 'nt':
                        os.startfile(reminder['file_path'])
                    elif os.name == 'posix':
                        subprocess.call(('xdg-open', reminder['file_path']))
                except Exception as e:
                    QMessageBox.critical(self, "Open File Error", str(e))
        elif action == 'Open Folder':
            reply = QMessageBox.information(self, "File Reminder", message + "\nOpen folder?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    folder_path = os.path.dirname(reminder['file_path'])
                    if sys.platform.startswith('darwin'):
                        subprocess.call(('open', folder_path))
                    elif os.name == 'nt':
                        os.startfile(folder_path)
                    elif os.name == 'posix':
                        subprocess.call(('xdg-open', folder_path))
                except Exception as e:
                    QMessageBox.critical(self, "Open Folder Error", str(e))

    # --- Add inactivity nudges (basic check) ---
    def check_inactivity_nudges(self):
        # This is a basic check; a more robust implementation would track usage patterns over time
        now = datetime.datetime.now().timestamp()
        cutoff_30_days = now - datetime.timedelta(days=30).total_seconds()
        cutoff_6_months = now - datetime.timedelta(days=180).total_seconds()
        inactive_30_days = []
        inactive_6_months = []
        # Iterate through some files (e.g., visible files or indexed files)
        # For simplicity, let's just check the current directory's files
        index = self.list_view.rootIndex()
        dir_path = self.file_model.filePath(index)
        if os.path.isdir(dir_path):
            for entry in os.listdir(dir_path):
                path = os.path.join(dir_path, entry)
                if os.path.isfile(path):
                    try:
                        atime = os.path.getatime(path)
                        if atime < cutoff_6_months:
                            inactive_6_months.append(path)
                        elif atime < cutoff_30_days:
                            inactive_30_days.append(path)
                    except Exception:
                        continue
        if inactive_30_days:
            QMessageBox.information(self, "Inactivity Nudge", f"You haven't opened {len(inactive_30_days)} file(s) in the current directory in 30 days.")
        if inactive_6_months:
            QMessageBox.information(self, "Inactivity Nudge", f"You haven't opened {len(inactive_6_months)} file(s) in the current directory in 6 months. Consider cleaning up.")

    def refresh_reminders(self):
        """Refresh the reminders list in the UI"""
        reminders = load_reminders()
        self.reminders_list.setRowCount(0)
        
        for reminder in reminders:
            row = self.reminders_list.rowCount()
            self.reminders_list.insertRow(row)
            
            # File name
            file_name = os.path.basename(reminder['file_path'])
            self.reminders_list.setItem(row, 0, QTableWidgetItem(file_name))
            
            # Due date
            due_date = QDateTime.fromString(reminder['datetime'], Qt.ISODate)
            self.reminders_list.setItem(row, 1, QTableWidgetItem(due_date.toString('yyyy-MM-dd hh:mm')))
            
            # Recurrence
            self.reminders_list.setItem(row, 2, QTableWidgetItem(reminder['recurrence']))
            
            # Action
            self.reminders_list.setItem(row, 3, QTableWidgetItem(reminder['action']))
            
            # Store the full reminder data in the first column
            self.reminders_list.item(row, 0).setData(Qt.UserRole, reminder)

    def delete_selected_reminder(self):
        """Delete the selected reminder"""
        current_row = self.reminders_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a reminder to delete.")
            return
            
        reminder = self.reminders_list.item(current_row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete Reminder", 
                                   f"Are you sure you want to delete the reminder for {os.path.basename(reminder['file_path'])}?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            reminders = load_reminders()
            reminders = [r for r in reminders if r != reminder]
            save_reminders(reminders)
            self.refresh_reminders()

    def edit_selected_reminder(self):
        """Edit the selected reminder"""
        current_row = self.reminders_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a reminder to edit.")
            return
            
        reminder_data = self.reminders_list.item(current_row, 0).data(Qt.UserRole)
        
        # Open ReminderDialog with existing data
        dlg = ReminderDialog(reminder_data['file_path'], self, existing_reminder=reminder_data)
        if dlg.exec_():
            # Dialog handles saving the updated reminder, just refresh the list
            self.refresh_reminders()

    def filter_reminders(self):
        """Filter the reminders list based on user input"""
        filter_text = self.reminder_filter_edit.text().lower()
        filter_column_index = self.reminder_filter_column.currentIndex()
        
        for row in range(self.reminders_list.rowCount()):
            item = self.reminders_list.item(row, filter_column_index)
            if item:
                item_text = item.text().lower()
                self.reminders_list.setRowHidden(row, filter_text not in item_text)

    def add_cloud_account(self):
        """Initiate the process to add a cloud storage account (Google Drive)"""
        # Run authentication in a separate thread to keep the UI responsive
        self.progress = QProgressDialog("Waiting for Google Authentication...", None, 0, 0, self)
        self.progress.setWindowTitle("Google Drive Authentication")
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setCancelButton(None)
        self.progress.show()
        self.setEnabled(False) # Disable UI while authentication is in progress

        def do_auth():
            # This function runs in the new thread
            try:
                creds = authenticate_google_drive()
                return creds
            except Exception as e:
                return e # Return the error to the main thread

        # Create a dedicated thread for authentication
        self.auth_thread = QThread()
        self.auth_worker = WorkerThread(do_auth) # Reusing WorkerThread as it emits result
        self.auth_worker.moveToThread(self.auth_thread)

        self.auth_thread.started.connect(self.auth_worker.run)
        self.auth_worker.result.connect(self.on_auth_completed)
        self.auth_thread.start()

    def on_auth_completed(self, result):
        """Handle the result of the Google Drive authentication."""
        self.setEnabled(True) # Re-enable UI
        self.progress.close() # Close progress dialog
        self.auth_thread.quit() # Quit the thread
        self.auth_thread.wait() # Wait for the thread to finish
        self.auth_thread.deleteLater()
        self.auth_worker.deleteLater()

        if isinstance(result, Exception):
            # Authentication failed with an exception
             QMessageBox.critical(self, "Google Drive Authentication Error", str(result))
        elif result:
            # Authentication successful, result is the credentials object
            user_info = "Google Drive Account" # Placeholder - can fetch user info later
            if user_info not in [self.cloud_accounts_list.item(i).text() for i in range(self.cloud_accounts_list.count())]:
                self.cloud_accounts_list.addItem(user_info)
                QMessageBox.information(self, "Google Drive", f"Successfully connected {user_info}!")
                # Store these credentials securely
                save_google_credentials(result)
                self.google_drive_credentials = result # Store credentials in memory as well
                # Populate Google Drive view after successful connection
                if not self.google_drive_model:
                     self.google_drive_model = GoogleDriveModel(self.google_drive_credentials)
                     self.google_drive_tree_view.setModel(self.google_drive_model)
                     self.google_drive_list_view.setModel(self.google_drive_model)
                     self.google_drive_tree_view.clicked.connect(self.on_google_drive_tree_clicked)
                else:
                     # If model already exists (shouldn't happen with current logic, but for completeness)
                     self.google_drive_model = GoogleDriveModel(self.google_drive_credentials) # Re-initialize with new credentials
                     self.google_drive_tree_view.setModel(self.google_drive_model)
                     self.google_drive_list_view.setModel(self.google_drive_model)
            
        else:
            # Authentication failed without an exception (e.g., user closed browser)
             QMessageBox.warning(self, "Google Drive Authentication Failed", "Authentication process did not complete.")

    def load_saved_cloud_accounts(self):
        """Loads saved cloud account credentials and updates the UI."""
        creds = load_google_credentials()
        if creds:
            # Assuming only one Google account for now
            user_info = "Google Drive Account" # Placeholder
            self.cloud_accounts_list.addItem(user_info)
            self.google_drive_credentials = creds # Store credentials in memory
            print("Loaded saved Google Drive credentials.")

    def remove_cloud_account(self):
        """Removes the selected cloud account credentials."""
        current_item = self.cloud_accounts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a cloud account to remove.")
            return
        
        account_text = current_item.text()
        if account_text == "Google Drive Account":
            reply = QMessageBox.question(self, "Remove Account", 
                                       "Are you sure you want to remove the Google Drive account?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                clear_google_credentials()
                self.cloud_accounts_list.takeItem(self.cloud_accounts_list.currentRow())
                self.google_drive_credentials = None # Clear credentials from memory
                # Clear the Google Drive model and views
                self.google_drive_tree_view.setModel(None)
                self.google_drive_list_view.setModel(None)
                self.google_drive_model = None
                QMessageBox.information(self, "Account Removed", "Google Drive account removed.")
        # Add logic for other cloud services here if implemented

    def on_google_drive_tree_clicked(self, index):
        """Updates the Google Drive list view when a folder is selected in the tree view."""
        if index.isValid() and self.google_drive_model:
            item = index.internalPointer()
            if item and item.is_folder():
                self.google_drive_list_view.setRootIndex(index)

    def google_drive_context_menu(self, pos):
        """Creates and shows the context menu for Google Drive items."""
        menu = QMenu()
        download_action = menu.addAction("Download", self.download_google_drive_item_action)
        upload_action = menu.addAction("Upload File Here", self.upload_file_to_google_drive)
        delete_action = menu.addAction("Delete", self.delete_google_drive_item_action)
        # TODO: Add more actions (Create Folder, etc.)

        # Determine which view requested the context menu and get the selected index
        sender_view = self.sender()
        if sender_view == self.google_drive_tree_view:
            index = self.google_drive_tree_view.indexAt(pos)
        elif sender_view == self.google_drive_list_view:
            index = self.google_drive_list_view.indexAt(pos)
        else:
            return # Should not happen

        # Disable download action if no item is selected or if it's a folder
        if not index.isValid() or (index.isValid() and index.internalPointer() and index.internalPointer().is_folder()):
            download_action.setEnabled(False)

        # Enable upload action only if a folder is selected
        if not index.isValid() or (index.isValid() and index.internalPointer() and not index.internalPointer().is_folder()):
             upload_action.setEnabled(False)

        # Disable delete action if no item is selected
        if not index.isValid():
            delete_action.setEnabled(False)

        menu.exec_(pos)

    def download_google_drive_item_action(self):
        """Handles the download action for a selected Google Drive item."""
        # Determine which view is currently active to get the selected index
        current_tab_widget = self.center_tabs.currentWidget()
        if current_tab_widget == self.google_drive_tree_view.parent(): # Check if Google Drive tab is active
             index = self.google_drive_tree_view.currentIndex()
             if not index.isValid(): # If nothing selected in tree view, check list view
                 index = self.google_drive_list_view.currentIndex()

        if not index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select a Google Drive file to download.")
            return

        item = index.internalPointer()
        if not item or item.is_folder():
            QMessageBox.warning(self, "Invalid Selection", "Please select a Google Drive file to download (folders cannot be downloaded directly yet).")
            return

        # Prompt user for save location
        file_name = item.item_data().get('name', 'downloaded_file')
        save_path, _ = QFileDialog.getSaveFileName(self, "Download File", file_name)

        if save_path:
            file_id = item.item_id()
            if not file_id:
                 QMessageBox.critical(self, "Download Error", "Could not get file ID for download.")
                 return
            
            # Run download in a separate thread with progress
            from google_drive_api import download_google_drive_file # Import here to avoid circular dependency

            def do_download(file_id, save_path, credentials):
                 thread = QThread.currentThread()
                 if isinstance(thread, FileOperationThread):
                     # The download_google_drive_file function has basic print statements for progress.
                     # A more advanced implementation would require modifying download_google_drive_file
                     # to accept and use a progress callback function from the thread.
                     thread.update_progress(f"Downloading {os.path.basename(save_path)}...")
                 
                 # The download_google_drive_file function itself doesn't report incremental progress back to the thread currently.
                 # For now, we'll just show start/end/error messages in the progress dialog.
                 success = download_google_drive_file(credentials, file_id, save_path)
                 
                 if isinstance(thread, FileOperationThread):
                     if success:
                          thread.update_progress(f"Finished downloading {os.path.basename(save_path)}.")
                     else:
                          thread.update_progress(f"Error downloading {os.path.basename(save_path)}.")
                 
                 if not success:
                     # If download_google_drive_file returns False, raise an exception to trigger error handling
                     raise Exception("Download failed.")
                 
                 return save_path # Return the save path on success

            def on_download_done(result, error):
                 # on_thread_finished handles closing the progress dialog and showing critical errors
                 if not error:
                     QMessageBox.information(self, "Download Complete", f"File downloaded to {result}")

            # Pass credentials to the thread function
            self.run_in_thread(do_download, file_id, save_path, self.google_drive_credentials)

    def upload_file_to_google_drive(self):
        """Handles the upload action to Google Drive."""
        # Determine the target folder ID
        current_tab_widget = self.center_tabs.currentWidget()
        if current_tab_widget == self.google_drive_tree_view.parent(): # Check if Google Drive tab is active
             index = self.google_drive_tree_view.currentIndex()
             if not index.isValid(): # If nothing selected in tree view, check list view
                 index = self.google_drive_list_view.currentIndex()

        if not index.isValid():
            QMessageBox.warning(self, "No Target Folder", "Please select a Google Drive folder to upload to.")
            return

        item = index.internalPointer()
        if not item or not item.is_folder():
            QMessageBox.warning(self, "Invalid Target", "Please select a Google Drive folder to upload to.")
            return

        target_folder_id = item.item_id()
        if not target_folder_id:
             QMessageBox.critical(self, "Upload Error", "Could not get target folder ID.")
             return

        # Prompt user to select a local file to upload
        local_file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")

        if local_file_path:
            from google_drive_api import upload_google_drive_file # Import here to avoid circular dependency

            def do_upload(file_path, folder_id, credentials):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Uploading {os.path.basename(file_path)}...")
                
                # The upload_google_drive_file function doesn't report incremental progress back to the thread currently.
                # For now, we'll just show start/end/error messages in the progress dialog.
                uploaded_file_id = upload_google_drive_file(credentials, file_path, folder_id)

                if isinstance(thread, FileOperationThread):
                    if uploaded_file_id:
                         thread.update_progress(f"Finished uploading {os.path.basename(file_path)}.")
                    else:
                         thread.update_progress(f"Error uploading {os.path.basename(file_path)}.")
                         
                if not uploaded_file_id:
                    raise Exception("Upload failed.")

                return uploaded_file_id # Return the uploaded file ID on success

            def on_upload_done(result, error):
                # on_thread_finished handles closing the progress dialog and showing critical errors
                if not error:
                    QMessageBox.information(self, "Upload Complete", f"File uploaded successfully!")
                    # Refresh the view to show the new file
                    # The easiest way is to re-fetch the children of the parent folder
                    # Need to find the index of the target folder again after the thread finishes
                    # This is a bit tricky. For now, let's just refresh the entire model (less efficient)
                    # A better approach would be to emit a signal from the model when content changes
                    if self.google_drive_model:
                         # Find the parent item and mark it as unfetched to trigger fetchMore on expand
                         # Or, ideally, use beginInsertRows/endInsertRows in the model
                         # For now, a simple refresh might suffice depending on how the model is implemented.
                         # Let's try refreshing the current view's root index.
                         current_google_drive_index = self.google_drive_list_view.rootIndex()
                         if current_google_drive_index.isValid() and self.google_drive_model:
                             item = current_google_drive_index.internalPointer()
                             if item and item.is_folder():
                                 item._is_fetched = False # Mark as unfetched
                                 # This doesn't automatically trigger fetchMore in list view. Need to signal model change.
                                 # A more robust solution involves model signals.
                                 # For a quick visual update, we could just re-set the model or refresh the current index.
                                 # Let's emit a data changed signal for the parent to trigger a view update.
                                 # Need to get the index of the parent item in the tree view.
                                 # Finding the index from the item is also not straightforward with the current model.

                                 # Alternative: just re-populate the current list view.
                                 # This requires fetching children again for the current folder.
                                 # Let's add a method to the model to fetch children of a specific index.
                                 # For now, let's keep it simple and just show a message.
                                 pass # No automatic refresh for now, user can click folder again.
                                 QMessageBox.information(self, "Refresh Required", "Please re-select the folder to see the uploaded file.")

            # Pass credentials and folder ID to the thread function
            self.run_in_thread(do_upload, local_file_path, target_folder_id, self.google_drive_credentials)

    def delete_google_drive_item_action(self):
        """Handles the delete action for a selected Google Drive item."""
        # Determine which view is currently active to get the selected index
        current_tab_widget = self.center_tabs.currentWidget()
        if current_tab_widget == self.google_drive_tree_view.parent(): # Check if Google Drive tab is active
             index = self.google_drive_tree_view.currentIndex()
             if not index.isValid(): # If nothing selected in tree view, check list view
                 index = self.google_drive_list_view.currentIndex()

        if not index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select a Google Drive item to delete.")
            return

        item = index.internalPointer()
        if not item:
             QMessageBox.warning(self, "Invalid Selection", "Could not get selected Google Drive item details.")
             return
             
        item_name = item.item_data().get('name', 'selected item')
        item_id = item.item_id()

        if not item_id:
             QMessageBox.critical(self, "Delete Error", "Could not get item ID for deletion.")
             return

        reply = QMessageBox.question(self, "Delete Item", 
                                   f"Are you sure you want to delete \"{item_name}\"?\nThis action cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            from google_drive_api import delete_google_drive_item # Import here to avoid circular dependency

            def do_delete(item_id, credentials):
                thread = QThread.currentThread()
                if isinstance(thread, FileOperationThread):
                    thread.update_progress(f"Deleting \"{item_name}\"...")

                success = delete_google_drive_item(credentials, item_id)

                if isinstance(thread, FileOperationThread):
                    if success:
                         thread.update_progress(f"Finished deleting \"{item_name}\".")
                    else:
                         thread.update_progress(f"Error deleting \"{item_name}\".")

                if not success:
                    raise Exception("Deletion failed.")

                return item_name # Return the item name on success

            def on_delete_done(result, error):
                 # on_thread_finished handles closing the progress dialog and showing critical errors
                if not error:
                    QMessageBox.information(self, "Delete Complete", f"\"{result}\" deleted successfully!")
                    # Refresh the view after deletion
                    # Similar to upload, a full model refresh or a more targeted signal is needed
                    # For now, prompt user to re-select folder
                    QMessageBox.information(self, "Refresh Required", "Please re-select the folder to see the changes.")

            # Pass credentials and item ID to the thread function
            self.run_in_thread(do_delete, item_id, self.google_drive_credentials)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileForgeWindow()
    window.show()
    sys.exit(app.exec()) 