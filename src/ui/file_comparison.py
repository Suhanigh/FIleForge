"""
File comparison dialog for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFileDialog, QComboBox,
    QSplitter, QWidget
)
from PySide6.QtCore import Qt
import difflib
import os

class FileComparisonDialog(QDialog):
    """Dialog for comparing two files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Comparison")
        self.setMinimumSize(800, 600)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # File selection
        file_selection = QHBoxLayout()
        
        # Left file
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("File 1:"))
        self.left_file = QLineEdit()
        self.left_file.setReadOnly(True)
        left_layout.addWidget(self.left_file)
        self.left_browse = QPushButton("Browse")
        self.left_browse.clicked.connect(lambda: self._browse_file(self.left_file))
        left_layout.addWidget(self.left_browse)
        file_selection.addLayout(left_layout)
        
        # Right file
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("File 2:"))
        self.right_file = QLineEdit()
        self.right_file.setReadOnly(True)
        right_layout.addWidget(self.right_file)
        self.right_browse = QPushButton("Browse")
        self.right_browse.clicked.connect(lambda: self._browse_file(self.right_file))
        right_layout.addWidget(self.right_browse)
        file_selection.addLayout(right_layout)
        
        layout.addLayout(file_selection)
        
        # Comparison options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Comparison Type:"))
        self.comparison_type = QComboBox()
        self.comparison_type.addItems(["Text", "Binary"])
        options_layout.addWidget(self.comparison_type)
        self.compare_button = QPushButton("Compare")
        self.compare_button.clicked.connect(self._compare_files)
        options_layout.addWidget(self.compare_button)
        layout.addLayout(options_layout)
        
        # Comparison results
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left text
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("File 1 Content:"))
        self.left_text = QTextEdit()
        self.left_text.setReadOnly(True)
        left_layout.addWidget(self.left_text)
        self.splitter.addWidget(left_widget)
        
        # Right text
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("File 2 Content:"))
        self.right_text = QTextEdit()
        self.right_text.setReadOnly(True)
        right_layout.addWidget(self.right_text)
        self.splitter.addWidget(right_widget)
        
        # Diff view
        diff_widget = QWidget()
        diff_layout = QVBoxLayout(diff_widget)
        diff_layout.addWidget(QLabel("Differences:"))
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        diff_layout.addWidget(self.diff_text)
        self.splitter.addWidget(diff_widget)
        
        layout.addWidget(self.splitter)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
    
    def _browse_file(self, line_edit):
        """Open file dialog and set the selected file path."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)
    
    def _compare_files(self):
        """Compare the selected files."""
        file1 = self.left_file.text()
        file2 = self.right_file.text()
        
        if not file1 or not file2:
            return
        
        if not os.path.exists(file1) or not os.path.exists(file2):
            return
        
        comparison_type = self.comparison_type.currentText()
        
        if comparison_type == "Text":
            self._compare_text_files(file1, file2)
        else:
            self._compare_binary_files(file1, file2)
    
    def _compare_text_files(self, file1, file2):
        """Compare two text files."""
        try:
            with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
                text1 = f1.readlines()
                text2 = f2.readlines()
            
            self.left_text.setText(''.join(text1))
            self.right_text.setText(''.join(text2))
            
            # Generate diff
            diff = difflib.unified_diff(
                text1, text2,
                fromfile=os.path.basename(file1),
                tofile=os.path.basename(file2)
            )
            
            self.diff_text.setText(''.join(diff))
            
        except Exception as e:
            self.diff_text.setText(f"Error comparing files: {str(e)}")
    
    def _compare_binary_files(self, file1, file2):
        """Compare two binary files."""
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                data1 = f1.read()
                data2 = f2.read()
            
            # Show hex dump
            self.left_text.setText(self._hex_dump(data1))
            self.right_text.setText(self._hex_dump(data2))
            
            # Compare bytes
            diff = []
            min_len = min(len(data1), len(data2))
            max_len = max(len(data1), len(data2))
            
            for i in range(max_len):
                if i >= min_len:
                    diff.append(f"Position {i:08x}: {'File 1' if i < len(data1) else 'File 2'} has extra data")
                elif data1[i] != data2[i]:
                    diff.append(f"Position {i:08x}: {data1[i]:02x} != {data2[i]:02x}")
            
            self.diff_text.setText('\n'.join(diff))
            
        except Exception as e:
            self.diff_text.setText(f"Error comparing files: {str(e)}")
    
    def _hex_dump(self, data, bytes_per_line=16):
        """Generate a hex dump of binary data."""
        result = []
        for i in range(0, len(data), bytes_per_line):
            chunk = data[i:i + bytes_per_line]
            hex_values = ' '.join(f'{b:02x}' for b in chunk)
            ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            result.append(f"{i:08x}: {hex_values:<48} {ascii_values}")
        return '\n'.join(result)
    
    def _apply_theme_styles(self, is_dark):
        """Apply theme-specific styles."""
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #353535;
                    color: white;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QLineEdit {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QComboBox {
                    background-color: #2d2d2d;
                    color: white;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: white;
                    color: black;
                }
                QTextEdit {
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QLineEdit {
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: black;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QComboBox {
                    background-color: #f5f5f5;
                    color: black;
                    border: 1px solid #dcdcdc;
                    border-radius: 4px;
                    padding: 5px;
                }
            """) 