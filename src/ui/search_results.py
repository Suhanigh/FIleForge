"""
Search results view component for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QHBoxLayout,
    QLineEdit, QComboBox, QCheckBox, QSplitter,
    QFileDialog, QMenu, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal
import os
import csv
import json
from datetime import datetime

from .file_preview import FilePreview

class SortableTableWidgetItem(QTableWidgetItem):
    """Custom table widget item that supports proper sorting."""
    
    def __init__(self, text, sort_key=None):
        super().__init__(text)
        self.sort_key = sort_key or text.lower()
    
    def __lt__(self, other):
        """Override less than operator for sorting."""
        if isinstance(other, SortableTableWidgetItem):
            return self.sort_key < other.sort_key
        return super().__lt__(other)

class SearchResultsView(QWidget):
    """Widget to display search results in a table format."""
    
    # Signal emitted when a file is double-clicked
    file_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._all_results = []  # Store all results for filtering
        self._current_search_type = "name"
    
    def _init_ui(self):
        """Initialize the search results UI components."""
        layout = QVBoxLayout(self)
        
        # Results count label
        self.results_label = QLabel("No search results")
        layout.addWidget(self.results_label)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Filter type
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "Files", "Folders"])
        self.filter_type.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.filter_type)
        
        # Filter text
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("Filter results...")
        self.filter_text.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_text)
        
        # Case sensitive checkbox
        self.case_sensitive = QCheckBox("Case Sensitive")
        self.case_sensitive.stateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.case_sensitive)
        
        # Clear filters button
        self.clear_filters = QPushButton("Clear Filters")
        self.clear_filters.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self.clear_filters)
        
        layout.addLayout(filter_layout)
        
        # Create splitter for results and preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Name", "Path", "Type", "Tags"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting
        self.results_table.setSortingEnabled(True)
        
        # Enable context menu
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect signals
        self.results_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.results_table.itemSelectionChanged.connect(self._on_selection_changed)
        header.sectionClicked.connect(self._on_header_clicked)
        
        self.splitter.addWidget(self.results_table)
        
        # File preview
        self.file_preview = FilePreview()
        self.splitter.addWidget(self.file_preview)
        
        # Set initial splitter sizes
        self.splitter.setSizes([600, 300])
        
        layout.addWidget(self.splitter)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Export button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self._export_results)
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        
        # Clear button
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
    
    def _show_context_menu(self, position):
        """Show context menu for the results table."""
        menu = QMenu()
        
        # Add export actions
        export_menu = menu.addMenu("Export")
        export_csv = export_menu.addAction("Export as CSV")
        export_json = export_menu.addAction("Export as JSON")
        
        # Add copy actions
        copy_menu = menu.addMenu("Copy")
        copy_name = copy_menu.addAction("Copy Name")
        copy_path = copy_menu.addAction("Copy Path")
        copy_all = copy_menu.addAction("Copy All Details")
        
        # Show menu and handle action
        action = menu.exec(self.results_table.mapToGlobal(position))
        
        if action == export_csv:
            self._export_results("csv")
        elif action == export_json:
            self._export_results("json")
        elif action == copy_name:
            self._copy_to_clipboard("name")
        elif action == copy_path:
            self._copy_to_clipboard("path")
        elif action == copy_all:
            self._copy_to_clipboard("all")
    
    def _copy_to_clipboard(self, copy_type):
        """Copy selected item details to clipboard."""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            return
        
        # Get the first selected item's row
        row = selected_items[0].row()
        
        if copy_type == "name":
            text = self.results_table.item(row, 0).text()
        elif copy_type == "path":
            text = self.results_table.item(row, 1).text()
        else:  # all
            name = self.results_table.item(row, 0).text()
            path = self.results_table.item(row, 1).text()
            type_ = self.results_table.item(row, 2).text()
            tags = self.results_table.item(row, 3).text()
            text = f"Name: {name}\nPath: {path}\nType: {type_}\nTags: {tags}"
        
        QApplication.clipboard().setText(text)
    
    def _export_results(self, format_type=None):
        """Export search results to a file."""
        if not self._all_results:
            return
        
        # Get export format if not specified
        if not format_type:
            format_type, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                "",
                "CSV Files (*.csv);;JSON Files (*.json)"
            )
            if not format_type:
                return
            format_type = format_type.split(".")[-1].lower()
        
        # Get default export directory from preferences
        export_dir = None
        try:
            from ui.customizer import UICustomizer
            prefs_file = os.path.expanduser("~/.file_explorer_preferences.json")
            if os.path.exists(prefs_file):
                import json
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                export_dir = prefs.get('export_dir', None)
        except Exception:
            pass
        
        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"search_results_{timestamp}.{format_type}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            os.path.join(export_dir, default_name) if export_dir else default_name,
            f"{format_type.upper()} Files (*.{format_type})"
        )
        
        if not file_path:
            return
        
        try:
            if format_type == "csv":
                self._export_csv(file_path)
            else:  # json
                self._export_json(file_path)
            
            QMessageBox.information(self, "Success", f"Results exported to {file_path}")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results: {str(e)}"
            )
    
    def _export_csv(self, file_path):
        """Export results to CSV file."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Name", "Path", "Type", "Tags", "Size", "Modified"])
            
            # Write data
            for row in range(self.results_table.rowCount()):
                name = self.results_table.item(row, 0).text()
                path = self.results_table.item(row, 1).text()
                type_ = self.results_table.item(row, 2).text()
                tags = self.results_table.item(row, 3).text()
                
                # Get file details
                file_path = os.path.join(path, name)
                try:
                    stat = os.stat(file_path)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)
                except:
                    size = 0
                    modified = None
                
                writer.writerow([
                    name,
                    path,
                    type_,
                    tags,
                    size,
                    modified.strftime("%Y-%m-%d %H:%M:%S") if modified else ""
                ])
    
    def _export_json(self, file_path):
        """Export results to JSON file."""
        results = []
        
        for row in range(self.results_table.rowCount()):
            name = self.results_table.item(row, 0).text()
            path = self.results_table.item(row, 1).text()
            type_ = self.results_table.item(row, 2).text()
            tags = self.results_table.item(row, 3).text()
            
            # Get file details
            file_path = os.path.join(path, name)
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
            except:
                size = 0
                modified = None
            
            results.append({
                "name": name,
                "path": path,
                "type": type_,
                "tags": tags.split(", ") if tags else [],
                "size": size,
                "modified": modified.strftime("%Y-%m-%d %H:%M:%S") if modified else None
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_results": len(results),
                "results": results
            }, f, indent=2)
    
    def _on_selection_changed(self):
        """Handle selection change in the results table."""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            self.file_preview.clear_preview()
            return
        
        # Get the file path from the first selected item
        file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_preview.preview_file(file_path)
    
    def display_results(self, files, search_type="name"):
        """
        Display search results in the table.
        
        Args:
            files: List of file paths or (file_path, tags) tuples
            search_type: Type of search ("name" or "tags")
        """
        self._all_results = files
        self._current_search_type = search_type
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply current filters to the results."""
        # Temporarily disable sorting while updating
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        
        if not self._all_results:
            self.results_label.setText("No results found")
            self.results_table.setSortingEnabled(True)
            self.file_preview.clear_preview()
            return
        
        # Get filter values
        filter_type = self.filter_type.currentText()
        filter_text = self.filter_text.text()
        case_sensitive = self.case_sensitive.isChecked()
        
        # Apply filters
        filtered_results = []
        for file_info in self._all_results:
            if self._current_search_type == "tags":
                file_path, tags = file_info
            else:
                file_path = file_info
                tags = []
            
            # Type filter
            if filter_type != "All":
                is_folder = os.path.isdir(file_path)
                if (filter_type == "Files" and is_folder) or \
                   (filter_type == "Folders" and not is_folder):
                    continue
            
            # Text filter
            if filter_text:
                name = os.path.basename(file_path)
                path = os.path.dirname(file_path)
                tags_text = ", ".join(tags)
                
                if not case_sensitive:
                    filter_text = filter_text.lower()
                    name = name.lower()
                    path = path.lower()
                    tags_text = tags_text.lower()
                
                if filter_text not in name and \
                   filter_text not in path and \
                   filter_text not in tags_text:
                    continue
            
            filtered_results.append(file_info)
        
        # Display filtered results
        self.results_table.setRowCount(len(filtered_results))
        
        for row, file_info in enumerate(filtered_results):
            if self._current_search_type == "tags":
                file_path, tags = file_info
            else:
                file_path = file_info
                tags = []
            
            # File name
            name = os.path.basename(file_path)
            name_item = SortableTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.results_table.setItem(row, 0, name_item)
            
            # File path
            path = os.path.dirname(file_path)
            path_item = SortableTableWidgetItem(path)
            self.results_table.setItem(row, 1, path_item)
            
            # File type
            if os.path.isdir(file_path):
                type_text = "Folder"
                type_sort = "0"  # Sort folders first
            else:
                ext = os.path.splitext(file_path)[1]
                type_text = ext or "File"
                type_sort = "1" + type_text.lower()  # Sort files after folders
            type_item = SortableTableWidgetItem(type_text, type_sort)
            self.results_table.setItem(row, 2, type_item)
            
            # Tags
            tags_text = ", ".join(sorted(tags))
            tags_item = SortableTableWidgetItem(tags_text)
            self.results_table.setItem(row, 3, tags_item)
        
        self.results_label.setText(f"Showing {len(filtered_results)} of {len(self._all_results)} results")
        
        # Re-enable sorting
        self.results_table.setSortingEnabled(True)
        
        # Sort by name by default
        self.results_table.sortItems(0, Qt.SortOrder.AscendingOrder)
        
        # Clear preview if no selection
        if not self.results_table.selectedItems():
            self.file_preview.clear_preview()
    
    def _clear_filters(self):
        """Clear all filters."""
        self.filter_type.setCurrentText("All")
        self.filter_text.clear()
        self.case_sensitive.setChecked(False)
        self._apply_filters()
    
    def clear_results(self):
        """Clear the search results."""
        self._all_results = []
        self._current_search_type = "name"
        self._clear_filters()
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        self.results_label.setText("No search results")
        self.results_table.setSortingEnabled(True)
        self.file_preview.clear_preview()
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on a result item."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_selected.emit(file_path)
    
    def _on_header_clicked(self, column):
        """Handle header click for sorting."""
        # Get current sort order
        current_order = self.results_table.horizontalHeader().sortIndicatorOrder()
        
        # Toggle sort order
        new_order = (Qt.SortOrder.DescendingOrder 
                    if current_order == Qt.SortOrder.AscendingOrder 
                    else Qt.SortOrder.AscendingOrder)
        
        # Sort the table
        self.results_table.sortItems(column, new_order)

    def _apply_theme_styles(self, is_dark):
        """Apply theme-specific styles to the search results view."""
        if is_dark:
            # Dark theme styles
            self.results_table.setStyleSheet("""
                QTableWidget {
                    background-color: #353535;
                    color: white;
                    gridline-color: #404040;
                    border: 1px solid #404040;
                }
                QTableWidget::item {
                    padding: 4px;
                    color: white;
                }
                QTableWidget::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #404040;
                    color: white;
                    padding: 4px;
                    border: 1px solid #505050;
                }
                QTableWidget QTableCornerButton::section {
                    background-color: #404040;
                    border: 1px solid #505050;
                }
            """)
            
            self.results_label.setStyleSheet("""
                QLabel {
                    color: white;
                    padding: 4px;
                }
            """)
            
            self.filter_text.setStyleSheet("""
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
            
            self.filter_type.setStyleSheet("""
                QComboBox {
                    padding: 4px;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    background-color: #353535;
                    color: white;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(down_arrow_white.png);
                }
                QComboBox QAbstractItemView {
                    background-color: #353535;
                    color: white;
                    selection-background-color: #2a82da;
                }
            """)
            
            self.case_sensitive.setStyleSheet("""
                QCheckBox {
                    color: white;
                }
                QCheckBox::indicator {
                    border: 1px solid #404040;
                    background-color: #353535;
                }
                QCheckBox::indicator:checked {
                    background-color: #2a82da;
                }
            """)
            
            self.clear_filters.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #404040;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
            """)
            
            self.export_button.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #2a82da;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3a92ea;
                }
                QPushButton:pressed {
                    background-color: #1a72ca;
                }
            """)
            
            self.clear_button.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #404040;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
            """)
        else:
            # Light theme styles
            self.results_table.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    color: black;
                    gridline-color: #dcdcdc;
                    border: 1px solid #dcdcdc;
                }
                QTableWidget::item {
                    padding: 4px;
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: #0078d7;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    color: black;
                    padding: 4px;
                    border: 1px solid #dcdcdc;
                }
                QTableWidget QTableCornerButton::section {
                    background-color: #f5f5f5;
                    border: 1px solid #dcdcdc;
                }
            """)
            
            self.results_label.setStyleSheet("""
                QLabel {
                    color: black;
                    padding: 4px;
                }
            """)
            
            self.filter_text.setStyleSheet("""
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
            
            self.filter_type.setStyleSheet("""
                QComboBox {
                    padding: 4px;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(down_arrow_black.png);
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: #0078d7;
                }
            """)
            
            self.case_sensitive.setStyleSheet("""
                QCheckBox {
                    color: black;
                }
                QCheckBox::indicator {
                    border: 1px solid #dcdcdc;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078d7;
                }
            """)
            
            self.clear_filters.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
                QPushButton:pressed {
                    background-color: #d5d5d5;
                }
            """)
            
            self.export_button.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1088e7;
                }
                QPushButton:pressed {
                    background-color: #0068c7;
                }
            """)
            
            self.clear_button.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
                QPushButton:pressed {
                    background-color: #d5d5d5;
                }
            """) 