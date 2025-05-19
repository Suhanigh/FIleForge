"""
Preview panel for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage
import os
from datetime import datetime

class PreviewPanel(QWidget):
    """Preview panel showing file contents and properties."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Properties section
        self.properties_label = QLabel("Properties")
        self.properties_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.properties_label)
        
        self.properties_text = QTextEdit()
        self.properties_text.setReadOnly(True)
        self.properties_text.setMaximumHeight(150)
        layout.addWidget(self.properties_text)
        
        # Preview section
        self.preview_label = QLabel("Preview")
        self.preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.preview_label)
        
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.preview_content = QLabel()
        self.preview_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setWidget(self.preview_content)
        
        layout.addWidget(self.preview_area)
        layout.addStretch()
    
    def _format_size(self, size_bytes):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _format_date(self, timestamp):
        """Format date in a readable format."""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def update_preview(self, file_path):
        """Update the preview with file contents and properties."""
        if not os.path.exists(file_path):
            self.clear_preview()
            return
        
        # Get file properties
        stat = os.stat(file_path)
        properties = []
        properties.append(f"Name: {os.path.basename(file_path)}")
        properties.append(f"Path: {file_path}")
        properties.append(f"Size: {self._format_size(stat.st_size)}")
        properties.append(f"Created: {self._format_date(stat.st_ctime)}")
        properties.append(f"Modified: {self._format_date(stat.st_mtime)}")
        properties.append(f"Type: {'Directory' if os.path.isdir(file_path) else 'File'}")
        
        if os.path.isfile(file_path):
            properties.append(f"Extension: {os.path.splitext(file_path)[1]}")
        
        self.properties_text.setText('\n'.join(properties))
        
        # Show preview based on file type
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            
            # Image preview
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                pixmap = QPixmap(file_path)
                scaled_pixmap = pixmap.scaled(
                    self.preview_area.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_content.setPixmap(scaled_pixmap)
            
            # Text preview
            elif ext in ['.txt', '.py', '.json', '.xml', '.html', '.css', '.js']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.preview_content.setText(content)
                except:
                    self.preview_content.setText("Unable to preview file content")
            
            # Other file types
            else:
                self.preview_content.setText("Preview not available for this file type")
        else:
            self.preview_content.setText("Select a file to preview its contents")
    
    def clear_preview(self):
        """Clear the preview content."""
        self.properties_text.clear()
        self.preview_content.clear()
    
    def _apply_theme_styles(self, is_dark):
        """Apply theme-specific styles."""
        if is_dark:
            self.setStyleSheet("""
                QWidget {
                    background-color: #353535;
                    color: white;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QScrollArea {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: black;
                }
                QTextEdit {
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QScrollArea {
                    background-color: #f5f5f5;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
            """) 