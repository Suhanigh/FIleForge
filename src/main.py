#!/usr/bin/env python3
"""
File System Explorer - Main Entry Point
A cross-platform file system explorer with advanced features.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("File System Explorer")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 