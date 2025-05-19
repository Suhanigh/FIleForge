# File System Explorer

A cross-platform file system explorer built with Python and PyQt6, featuring advanced file management capabilities.

## Features

- File system tree view with QFileSystemModel
- Basic file operations (create, rename, delete)
- Advanced search functionality
- File tagging system
- Batch operations
- Customizable UI with theme support
- Cross-platform compatibility

## Requirements

- Python 3.8 or higher
- PyQt6

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd file-system-explorer
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python src/main.py
```

## Project Structure

```
file-system-explorer/
├── src/
│   ├── main.py              # Application entry point
│   ├── ui/
│   │   ├── main_window.py   # Main window implementation
│   │   ├── search_bar.py    # Search functionality
│   │   └── customizer.py    # UI customization
│   └── utils/
│       ├── file_operations.py  # File handling logic
│       └── tag_manager.py      # Tag management system
├── resources/
│   └── icons/               # Application icons
├── requirements.txt         # Project dependencies
└── README.md               # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
