"""
Main window implementation for the File System Explorer.
"""

import os
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QFileSystemModel, QMenu, QMessageBox, QInputDialog,
    QFileDialog, QDockWidget, QToolBar, QStatusBar,
    QSplitter, QStyle, QStyleFactory, QApplication, QDialog, QComboBox, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QDir, QSize
from PySide6.QtGui import QAction, QIcon, QPalette, QColor

from .search_bar import SearchBar
from .customizer import UICustomizer
from .tag_manager_ui import TagManagerUI
from .search_results import SearchResultsView
from .preview_panel import PreviewPanel
from .file_comparison import FileComparisonDialog
from .permissions_dialog import PermissionsDialog
from utils.file_operations import FileOperations
from utils.compression import Compression
from utils.encryption import Encryption

class MainWindow(QMainWindow):
    """Main window of the File System Explorer application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File System Explorer")
        self.setMinimumSize(1000, 700)
        
        # Set modern style
        self.setStyle(QStyleFactory.create("Fusion"))
        
        # Initialize components
        self.file_ops = FileOperations()
        
        # Initialize UI components
        self._init_ui()
        self._setup_file_system()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._setup_search()
        self._setup_customizer()
        self._setup_tag_manager()
        self._setup_search_results()
        
        # Load user preferences
        self._load_preferences()
    
    def _apply_theme_styles(self, is_dark):
        """Apply theme-specific styles to UI components."""
        if is_dark:
            # Dark theme styles
            self.tree_view.setStyleSheet("""
                QTreeView {
                    border: 1px solid #404040;
                    border-radius: 4px;
                    background-color: #353535;
                    color: white;
                }
                QTreeView::item {
                    padding: 4px;
                    color: white;
                }
                QTreeView::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QTreeView::item:hover {
                    background-color: #404040;
                    color: white;
                }
                QTreeView::branch {
                    background-color: #353535;
                }
            """)
            
            self.toolbar.setStyleSheet("""
                QToolBar {
                    spacing: 8px;
                    padding: 4px;
                    background-color: #353535;
                    border-bottom: 1px solid #404040;
                }
                QToolButton {
                    padding: 4px;
                    border-radius: 4px;
                    color: white;
                }
                QToolButton:hover {
                    background-color: #404040;
                }
                QToolButton:pressed {
                    background-color: #505050;
                }
            """)
            
            self.search_bar.setStyleSheet("""
                QLineEdit {
                    padding: 6px;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    background-color: #353535;
                    color: white;
                }
                QLineEdit:focus {
                    border-color: #2a82da;
                }
                QLineEdit::placeholder {
                    color: #808080;
                }
            """)
            
            self.statusBar.setStyleSheet("""
                QStatusBar {
                    background-color: #353535;
                    border-top: 1px solid #404040;
                    padding: 4px;
                    color: white;
                }
            """)
            
            # Menu bar styles
            self.menuBar().setStyleSheet("""
                QMenuBar {
                    background-color: #353535;
                    color: white;
                }
                QMenuBar::item {
                    padding: 4px 8px;
                    color: white;
                }
                QMenuBar::item:selected {
                    background-color: #404040;
                }
                QMenu {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #404040;
                }
                QMenu::item {
                    padding: 4px 20px;
                    color: white;
                }
                QMenu::item:selected {
                    background-color: #404040;
                }
            """)
            
            # Dock widget styles
            dock_style = """
                QDockWidget {
                    border: 1px solid #404040;
                    titlebar-close-icon: url(close.png);
                }
                QDockWidget::title {
                    text-align: center;
                    padding: 4px;
                    background-color: #353535;
                    color: white;
                }
            """
            self.customizer_dock.setStyleSheet(dock_style)
            self.tag_dock.setStyleSheet(dock_style)
            self.search_dock.setStyleSheet(dock_style)
            
        else:
            # Light theme styles
            self.tree_view.setStyleSheet("""
                QTreeView {
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QTreeView::item {
                    padding: 4px;
                    color: black;
                }
                QTreeView::item:selected {
                    background-color: #0078d7;
                    color: white;
                }
                QTreeView::item:hover {
                    background-color: #e5f3ff;
                    color: black;
                }
                QTreeView::branch {
                    background-color: white;
                }
            """)
            
            self.toolbar.setStyleSheet("""
                QToolBar {
                    spacing: 8px;
                    padding: 4px;
                    background-color: #f5f5f5;
                    border-bottom: 1px solid #dcdcdc;
                }
                QToolButton {
                    padding: 4px;
                    border-radius: 4px;
                    color: black;
                }
                QToolButton:hover {
                    background-color: #e0e0e0;
                }
                QToolButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            
            self.search_bar.setStyleSheet("""
                QLineEdit {
                    padding: 6px;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QLineEdit:focus {
                    border-color: #0078d7;
                }
                QLineEdit::placeholder {
                    color: #808080;
                }
            """)
            
            self.statusBar.setStyleSheet("""
                QStatusBar {
                    background-color: #f5f5f5;
                    border-top: 1px solid #dcdcdc;
                    padding: 4px;
                    color: black;
                }
            """)
            
            # Menu bar styles
            self.menuBar().setStyleSheet("""
                QMenuBar {
                    background-color: #f5f5f5;
                    color: black;
                }
                QMenuBar::item {
                    padding: 4px 8px;
                    color: black;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: white;
                    color: black;
                    border: 1px solid #dcdcdc;
                }
                QMenu::item {
                    padding: 4px 20px;
                    color: black;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
            """)
            
            # Dock widget styles
            dock_style = """
                QDockWidget {
                    border: 1px solid #dcdcdc;
                    titlebar-close-icon: url(close.png);
                }
                QDockWidget::title {
                    text-align: center;
                    padding: 4px;
                    background-color: #f5f5f5;
                    color: black;
                }
            """
            self.customizer_dock.setStyleSheet(dock_style)
            self.tag_dock.setStyleSheet(dock_style)
            self.search_dock.setStyleSheet(dock_style)
    
    def _init_ui(self):
        """Initialize the main UI components."""
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create splitter for tree view and preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.main_layout.addWidget(self.splitter)
        
        # Initialize recent locations
        self.recent_locations = []
        self.max_recent_locations = 10
    
    def _setup_file_system(self):
        """Set up the file system model and tree view."""
        # Create file system model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.homePath()))
        self.tree_view.setAnimated(True)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setColumnWidth(0, 300)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setIndentation(20)
        
        # Enable context menu
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect selection changed signal
        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        # Add tree view to splitter
        self.splitter.addWidget(self.tree_view)
        
        # Create and add preview panel
        self.preview_panel = PreviewPanel()
        self.splitter.addWidget(self.preview_panel)
        
        # Set initial splitter sizes
        self.splitter.setSizes([600, 400])
    
    def _create_toolbar(self):
        """Create the main toolbar with a modern look."""
        # Create main toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 8px;
                padding: 4px;
                background-color: #f5f5f5;
                border-bottom: 1px solid #dcdcdc;
            }
            QToolButton {
                padding: 4px;
                border-radius: 4px;
                color: black;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # Add actions to toolbar
        self.toolbar.addAction(self.new_folder_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.copy_action)
        self.toolbar.addAction(self.move_action)
        self.toolbar.addAction(self.delete_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.rename_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.refresh_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.add_tag_action)
        
        self.addToolBar(self.toolbar)
    
    def _setup_search(self):
        """Set up the search functionality with a modern look."""
        # Create search bar
        self.search_bar = SearchBar()
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border-color: #0078d7;
            }
            QLineEdit::placeholder {
                color: #808080;
            }
        """)
        self.search_bar.search_triggered.connect(self._handle_search)
        
        # Add search bar to toolbar
        self.search_toolbar = QToolBar("Search")
        self.search_toolbar.setMovable(False)
        self.search_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 8px;
                padding: 4px;
                background-color: #f5f5f5;
                border-bottom: 1px solid #dcdcdc;
            }
        """)
        self.search_toolbar.addWidget(self.search_bar)
        self.addToolBar(self.search_toolbar)
    
    def _setup_customizer(self):
        """Set up the UI customizer with a modern look."""
        # Create customizer dock widget
        self.customizer_dock = QDockWidget("Preferences", self)
        self.customizer_dock.setStyleSheet("""
            QDockWidget {
                border: 1px solid #dcdcdc;
                titlebar-close-icon: url(close.png);
            }
            QDockWidget::title {
                text-align: center;
                padding: 4px;
                background-color: #f5f5f5;
                color: black;
            }
        """)
        self.customizer = UICustomizer()
        self.customizer_dock.setWidget(self.customizer)
        self.customizer_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                           Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.customizer_dock)
        
        # Connect theme change signal
        self.customizer.theme_changed.connect(self._on_theme_changed)
    
    def _setup_tag_manager(self):
        """Set up the tag manager with a modern look."""
        # Create tag manager dock widget
        self.tag_dock = QDockWidget("Tags", self)
        self.tag_dock.setStyleSheet("""
            QDockWidget {
                border: 1px solid #dcdcdc;
                titlebar-close-icon: url(close.png);
            }
            QDockWidget::title {
                text-align: center;
                padding: 4px;
                background-color: #f5f5f5;
                color: black;
            }
        """)
        self.tag_manager = TagManagerUI()
        self.tag_dock.setWidget(self.tag_manager)
        self.tag_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                    Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.tag_dock)
        
        # Connect tag modification signal
        self.tag_manager.tags_modified.connect(self._on_tags_modified)
    
    def _setup_search_results(self):
        """Set up the search results view with a modern look."""
        # Create search results dock widget
        self.search_dock = QDockWidget("Search Results", self)
        self.search_dock.setStyleSheet("""
            QDockWidget {
                border: 1px solid #dcdcdc;
                titlebar-close-icon: url(close.png);
            }
            QDockWidget::title {
                text-align: center;
                padding: 4px;
                background-color: #f5f5f5;
                color: black;
            }
        """)
        self.search_results = SearchResultsView()
        self.search_dock.setWidget(self.search_results)
        self.search_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                       Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.search_dock)
        
        # Connect file selection signal
        self.search_results.file_selected.connect(self._on_search_result_selected)
    
    def _create_statusbar(self):
        """Create the status bar with a modern look."""
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #dcdcdc;
                padding: 4px;
                color: black;
            }
        """)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def _create_actions(self):
        """Create the main actions for the application."""
        # File operations
        self.new_folder_action = QAction("New Folder", self)
        self.new_folder_action.setStatusTip("Create a new folder")
        self.new_folder_action.triggered.connect(self._new_folder)
        
        self.copy_action = QAction("Copy", self)
        self.copy_action.setStatusTip("Copy selected items")
        self.copy_action.triggered.connect(self._copy_items)
        
        self.move_action = QAction("Move", self)
        self.move_action.setStatusTip("Move selected items")
        self.move_action.triggered.connect(self._move_items)
        
        self.delete_action = QAction("Delete", self)
        self.delete_action.setStatusTip("Delete selected items")
        self.delete_action.triggered.connect(self._delete_items)
        
        self.rename_action = QAction("Rename", self)
        self.rename_action.setStatusTip("Rename selected item")
        self.rename_action.triggered.connect(self._rename_item)
        
        self.batch_rename_action = QAction("Batch Rename", self)
        self.batch_rename_action.setStatusTip("Rename multiple files")
        self.batch_rename_action.triggered.connect(self._batch_rename)
        
        self.compress_action = QAction("Compress", self)
        self.compress_action.setStatusTip("Compress selected items")
        self.compress_action.triggered.connect(self._compress_items)
        
        self.decompress_action = QAction("Decompress", self)
        self.decompress_action.setStatusTip("Decompress selected archive")
        self.decompress_action.triggered.connect(self._decompress_archive)
        
        self.encrypt_action = QAction("Encrypt", self)
        self.encrypt_action.setStatusTip("Encrypt selected file")
        self.encrypt_action.triggered.connect(self._encrypt_file)
        
        self.decrypt_action = QAction("Decrypt", self)
        self.decrypt_action.setStatusTip("Decrypt selected file")
        self.decrypt_action.triggered.connect(self._decrypt_file)
        
        self.compare_action = QAction("Compare Files", self)
        self.compare_action.setStatusTip("Compare two files")
        self.compare_action.triggered.connect(self._compare_files)
        
        self.permissions_action = QAction("Permissions", self)
        self.permissions_action.setStatusTip("Manage file permissions")
        self.permissions_action.triggered.connect(self._manage_permissions)
        
        # View operations
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setStatusTip("Refresh the current view")
        self.refresh_action.triggered.connect(self._refresh_view)
        
        # Customizer action
        self.customizer_action = QAction("Preferences", self)
        self.customizer_action.setStatusTip("Open preferences")
        self.customizer_action.triggered.connect(self._toggle_customizer)
        
        # Tag actions
        self.add_tag_action = QAction("Add Tag", self)
        self.add_tag_action.setStatusTip("Add tag to selected item")
        self.add_tag_action.triggered.connect(self._add_tag_to_selected)
        
        # Recent locations actions
        self.recent_menu = QMenu("Recent Locations", self)
        self.update_recent_locations_menu()
    
    def _create_menus(self):
        """Create the application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.new_folder_action)
        file_menu.addAction(self.copy_action)
        file_menu.addAction(self.move_action)
        file_menu.addAction(self.delete_action)
        file_menu.addAction(self.rename_action)
        file_menu.addAction(self.batch_rename_action)
        file_menu.addSeparator()
        file_menu.addAction(self.compress_action)
        file_menu.addAction(self.decompress_action)
        file_menu.addSeparator()
        file_menu.addAction(self.encrypt_action)
        file_menu.addAction(self.decrypt_action)
        file_menu.addSeparator()
        file_menu.addAction(self.compare_action)
        file_menu.addAction(self.permissions_action)
        file_menu.addSeparator()
        file_menu.addMenu(self.recent_menu)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.refresh_action)
        view_menu.addAction(self.customizer_action)
        
        # Tags menu
        tags_menu = self.menuBar().addMenu("&Tags")
        tags_menu.addAction(self.add_tag_action)
    
    def _show_context_menu(self, position):
        """Show context menu for file operations."""
        menu = QMenu()
        
        # Add file operations
        menu.addAction(self.new_folder_action)
        menu.addAction(self.copy_action)
        menu.addAction(self.move_action)
        menu.addAction(self.delete_action)
        menu.addAction(self.rename_action)
        menu.addSeparator()
        
        # Add advanced operations
        menu.addAction(self.encrypt_action)
        menu.addAction(self.decrypt_action)
        menu.addAction(self.compare_action)
        menu.addAction(self.permissions_action)
        menu.addSeparator()
        
        # Add tag operations
        menu.addAction(self.add_tag_action)
        
        menu.exec(self.tree_view.mapToGlobal(position))
    
    def _handle_search(self, search_text, options):
        """Handle search requests."""
        if not search_text:
            self.tree_view.setRootIndex(self.model.index(QDir.homePath()))
            self.search_results.clear_results()
            return
        
        if options['type'] == 'tags':
            # Search by tags
            files = self.tag_manager.tag_manager.search_by_tags([search_text])
            if files:
                # Convert to list of (file_path, tags) tuples
                results = [(f, list(self.tag_manager.get_file_tags(f))) for f in files]
                self.search_results.display_results(results, search_type="tags")
            else:
                self.search_results.display_results([])
        else:
            # Search by name/content
            current_dir = self.model.filePath(self.tree_view.currentIndex())
            files = self.file_ops.search_files(
                current_dir,
                search_text,
                options['case_sensitive']
            )
            if files:
                self.search_results.display_results(files)
            else:
                self.search_results.display_results([])
    
    def _on_theme_changed(self, theme):
        """Handle theme changes."""
        is_dark = theme == "dark" or (theme == "system" and self.customizer._is_system_dark_mode())
        self._apply_theme_styles(is_dark)
        self.search_results._apply_theme_styles(is_dark)
        self.preview_panel._apply_theme_styles(is_dark)
        self.statusBar.showMessage(f"Theme changed to: {theme}")
    
    def _on_tags_modified(self):
        """Handle tag modifications."""
        self.statusBar.showMessage("Tags updated")
    
    def _toggle_customizer(self):
        """Toggle the customizer dock widget visibility."""
        self.customizer_dock.setVisible(not self.customizer_dock.isVisible())
    
    def _new_folder(self):
        """Create a new folder in the current directory."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        current_path = self.model.filePath(current_index)
        # Prompt for folder name
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:", text="New Folder")
        if not ok or not folder_name.strip():
            return
        new_folder_path = os.path.join(current_path, folder_name.strip())
        if os.path.exists(new_folder_path):
            QMessageBox.warning(self, "Error", f"A folder named '{folder_name}' already exists.")
            return
        if self.file_ops.create_directory(new_folder_path):
            self._refresh_view()
        else:
            QMessageBox.critical(self, "Error", "Failed to create folder")
    
    def _copy_items(self):
        """Copy selected items."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        
        source_paths = [self.model.filePath(index) for index in indexes]
        destination = QFileDialog.getExistingDirectory(
            self, "Select Destination Directory"
        )
        
        if destination:
            success, failed = self.file_ops.copy_files(source_paths, destination)
            if failed:
                QMessageBox.warning(
                    self, "Warning",
                    f"Failed to copy {len(failed)} items"
                )
            self._refresh_view()
    
    def _move_items(self):
        """Move selected items."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        
        source_paths = [self.model.filePath(index) for index in indexes]
        destination = QFileDialog.getExistingDirectory(
            self, "Select Destination Directory"
        )
        
        if destination:
            success, failed = self.file_ops.move_files(source_paths, destination)
            if failed:
                QMessageBox.warning(
                    self, "Warning",
                    f"Failed to move {len(failed)} items"
                )
            self._refresh_view()
    
    def _delete_items(self):
        """Delete selected items."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        
        paths = [self.model.filePath(index) for index in indexes]
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete the selected items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, failed = self.file_ops.delete_files(paths, recursive=True)
            if failed:
                QMessageBox.warning(
                    self, "Warning",
                    f"Failed to delete {len(failed)} items"
                )
            self._refresh_view()
    
    def _rename_item(self):
        """Rename the selected item."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            print("No valid item selected for rename")  # Debug log
            return
        
        old_path = self.model.filePath(current_index)
        old_name = os.path.basename(old_path)
        print(f"Selected item for rename: {old_path}")  # Debug log
        
        # Get new name from user
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            f"Enter new name for '{old_name}':",
            text=old_name
        )
        
        if not ok or not new_name.strip() or new_name == old_name:
            print("Rename cancelled or invalid new name")  # Debug log
            return
        
        # Construct new path
        new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
        print(f"Attempting to rename to: {new_path}")  # Debug log
        
        # Attempt to rename
        success, error_message = self.file_ops.rename_file(old_path, new_path)
        if success:
            print("Rename successful, updating view")  # Debug log
            # Update the model to reflect the change
            self.model.setRootPath(self.model.rootPath())
            self._refresh_view()
            self.statusBar.showMessage(f"Renamed '{old_name}' to '{new_name}'")
        else:
            print(f"Rename failed: {error_message}")  # Debug log
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to rename '{old_name}':\n{error_message}"
            )
    
    def _add_tag_to_selected(self):
        """Add a tag to the selected item."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        
        file_path = self.model.filePath(current_index)
        tag, ok = QInputDialog.getText(
            self, "Add Tag",
            "Enter tag name:"
        )
        
        if ok and tag:
            if self.tag_manager.add_tag_to_file(file_path, tag):
                self.statusBar.showMessage(f"Added tag '{tag}' to {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to add tag")
    
    def _refresh_view(self):
        """Refresh the current view."""
        self.tree_view.viewport().update()
    
    def _on_search_result_selected(self, file_path):
        """Handle selection of a search result."""
        # Find the file in the tree view
        index = self.model.index(file_path)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
            self.statusBar.showMessage(f"Selected: {file_path}")
    
    def _load_preferences(self):
        """Load user preferences from settings."""
        try:
            if os.path.exists(self.customizer.preferences_file):
                with open(self.customizer.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    
                # Apply theme
                theme = prefs.get('theme', 'light')
                self.customizer.theme_selector.setCurrentText(theme.capitalize())
                self._on_theme_changed(theme)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load preferences: {str(e)}")
    
    def _on_selection_changed(self, selected, deselected):
        """Handle selection changes in the tree view."""
        indexes = selected.indexes()
        if indexes:
            file_path = self.model.filePath(indexes[0])
            self.preview_panel.update_preview(file_path)
        else:
            self.preview_panel.clear_preview()
    
    def _add_to_recent_locations(self, path):
        """Add a path to recent locations."""
        if path in self.recent_locations:
            self.recent_locations.remove(path)
        self.recent_locations.insert(0, path)
        if len(self.recent_locations) > self.max_recent_locations:
            self.recent_locations.pop()
        self.update_recent_locations_menu()
    
    def update_recent_locations_menu(self):
        """Update the recent locations menu."""
        self.recent_menu.clear()
        for path in self.recent_locations:
            action = QAction(path, self)
            action.triggered.connect(lambda checked, p=path: self._navigate_to_path(p))
            self.recent_menu.addAction(action)
    
    def _navigate_to_path(self, path):
        """Navigate to a specific path."""
        if os.path.exists(path):
            index = self.model.index(path)
            self.tree_view.setCurrentIndex(index)
            self.tree_view.setRootIndex(index)
            self._add_to_recent_locations(path)
            self._refresh_view()
    
    def _batch_rename(self):
        """Rename multiple files using patterns."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        
        # Get selected files
        file_paths = [self.model.filePath(index) for index in indexes]
        if not file_paths:
            return
        
        # Show batch rename dialog
        dialog = BatchRenameDialog(self)
        if dialog.exec():
            options = dialog.get_rename_options()
            
            # Apply rename pattern to each file
            for i, file_path in enumerate(file_paths):
                name, ext = os.path.splitext(os.path.basename(file_path))
                dir_path = os.path.dirname(file_path)
                
                if options['pattern_type'] == "Number Sequence":
                    number = options['start_number'] + (i * options['step_number'])
                    new_name = f"{name}_{number:0{options['digits']}d}"
                else:
                    new_name = dialog._apply_rename_pattern(os.path.basename(file_path))
                
                new_path = os.path.join(dir_path, new_name)
                
                # Rename the file
                success, error = self.file_ops.rename_file(file_path, new_path)
                if not success:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        f"Failed to rename {os.path.basename(file_path)}: {error}"
                    )
            
            self._refresh_view()
    
    def _compress_items(self):
        """Compress selected items."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        
        # Get selected files
        file_paths = [self.model.filePath(index) for index in indexes]
        if not file_paths:
            return
        
        # Get compression format
        format_dialog = QDialog(self)
        format_dialog.setWindowTitle("Select Compression Format")
        layout = QVBoxLayout(format_dialog)
        
        format_combo = QComboBox()
        format_combo.addItems(Compression.get_supported_formats())
        layout.addWidget(QLabel("Format:"))
        layout.addWidget(format_combo)
        
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(format_dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(format_dialog.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        if not format_dialog.exec():
            return
        
        format = format_combo.currentText()
        extension = Compression.get_format_extensions()[format]
        
        # Get output path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Archive",
            os.path.join(os.path.dirname(file_paths[0]), "archive" + extension),
            f"Archive Files (*{extension})"
        )
        
        if output_path:
            # Compress files
            success, error = Compression.compress_files(file_paths, output_path, format)
            if success:
                self.statusBar.showMessage(f"Compressed {len(file_paths)} items to {output_path}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to compress files: {error}")
    
    def _decompress_archive(self):
        """Decompress selected archive."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        
        archive_path = self.model.filePath(current_index)
        if not any(archive_path.endswith(ext) for ext in ['.zip', '.tar.gz', '.tgz', '.tar']):
            QMessageBox.warning(self, "Error", "Please select a supported archive file")
            return
        
        # Get extract path
        extract_path = QFileDialog.getExistingDirectory(
            self,
            "Select Extract Location",
            os.path.dirname(archive_path)
        )
        
        if extract_path:
            # Decompress archive
            success, error = Compression.decompress_archive(archive_path, extract_path)
            if success:
                self.statusBar.showMessage(f"Extracted archive to {extract_path}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to extract archive: {error}")
    
    def _encrypt_file(self):
        """Encrypt the selected file."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        
        file_path = self.model.filePath(current_index)
        if not os.path.isfile(file_path):
            return
        
        # Get password
        password, ok = QInputDialog.getText(
            self,
            "Encrypt File",
            "Enter encryption password:",
            QInputDialog.EchoMode.Password
        )
        
        if ok and password:
            success, error = Encryption.encrypt_file(file_path, password)
            if success:
                self.statusBar.showMessage(f"File encrypted: {file_path}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to encrypt file: {error}")
    
    def _decrypt_file(self):
        """Decrypt the selected file."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        
        file_path = self.model.filePath(current_index)
        if not os.path.isfile(file_path) or not Encryption.is_encrypted_file(file_path):
            return
        
        # Get password
        password, ok = QInputDialog.getText(
            self,
            "Decrypt File",
            "Enter decryption password:",
            QInputDialog.EchoMode.Password
        )
        
        if ok and password:
            success, error = Encryption.decrypt_file(file_path, password)
            if success:
                self.statusBar.showMessage(f"File decrypted: {file_path}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to decrypt file: {error}")
    
    def _compare_files(self):
        """Open the file comparison dialog."""
        dialog = FileComparisonDialog(self)
        dialog._apply_theme_styles(self.customizer._is_system_dark_mode())
        dialog.exec()
    
    def _manage_permissions(self):
        """Open the permissions dialog for the selected file."""
        current_index = self.tree_view.currentIndex()
        if not current_index.isValid():
            return
        
        file_path = self.model.filePath(current_index)
        dialog = PermissionsDialog(file_path, self)
        dialog._apply_theme_styles(self.customizer._is_system_dark_mode())
        dialog.exec() 