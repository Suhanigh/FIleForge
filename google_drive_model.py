from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QIcon, QPixmap

from google_drive_api import list_google_drive_files

class GoogleDriveItem:
    """Represents an item (file or folder) in Google Drive."""
    def __init__(self, item_data, parent_item=None):
        self._item_data = item_data
        self._parent_item = parent_item
        self._child_items = []
        self._is_fetched = False # To track if children have been fetched

    def append_child(self, item):
        """Adds a child item to this item."""
        self._child_items.append(item)

    def child(self, row):
        """Returns the child item at the specified row."""
        if 0 <= row < len(self._child_items):
            return self._child_items[row]
        return None

    def child_count(self):
        """Returns the number of child items."""
        return len(self._child_items)

    def column_count(self):
        """Returns the number of data columns for this item."""
        return 3 # Name, Type, Modified Time

    def data(self, column):
        """Returns the data for the specified column."""
        if column == 0:
            return self._item_data.get('name', '')
        elif column == 1:
            mime_type = self._item_data.get('mimeType', '')
            if self._item_data.get('is_folder'):
                return "Folder"
            # Basic MIME type to human-readable conversion
            if mime_type == 'application/vnd.google-apps.document': return "Google Doc"
            if mime_type == 'application/vnd.google-apps.spreadsheet': return "Google Sheet"
            if mime_type == 'application/vnd.google-apps.presentation': return "Google Slides"
            return mime_type
        elif column == 2:
            return self._item_data.get('modifiedTime', '')
        return QVariant()

    def row(self):
        """Returns the row number of this item within its parent's children list."""
        if self._parent_item:
            return self._parent_item._child_items.index(self)
        return 0

    def parent_item(self):
        """Returns the parent item."""
        return self._parent_item

    def item_data(self):
        """Returns the raw item data from the API."""
        return self._item_data

    def is_folder(self):
        """Returns True if the item is a folder, False otherwise."""
        return self._item_data.get('is_folder', False)

    def item_id(self):
        """Returns the ID of the item."""
        return self._item_data.get('id', None)

    def set_children(self, children_data):
        """Sets the children of this item from fetched data."""
        self._child_items = []
        for item_data in children_data:
            self._child_items.append(GoogleDriveItem(item_data, self))
        self._is_fetched = True


class GoogleDriveModel(QAbstractItemModel):
    """Custom model for displaying Google Drive files and folders."""
    def __init__(self, credentials, parent=None):
        super().__init__(parent)
        self._credentials = credentials
        self._root_item = GoogleDriveItem({'id': 'root', 'name': 'My Drive', 'mimeType': 'application/vnd.google-apps.folder', 'is_folder': True})
        self._headers = ['Name', 'Type', 'Modified Time']

        # Fetch root children initially
        self.fetch_children(self._root_item)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns."""
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for the specified index and role."""
        if not index.isValid():
            return QVariant()

        item = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        
        # TODO: Add icons based on mime type
        # if role == Qt.ItemDataRole.DecorationRole:
        #     if item.is_folder():
        #         return QIcon.fromTheme('folder')
        #     else:
        #         return QIcon.fromTheme('text-x-generic')

        # Store the actual item data in a custom role for easy access
        if role == Qt.ItemDataRole.UserRole:
            return item.item_data()

        return QVariant()

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index for the item at the specified row and column under the parent."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        """Returns the parent of the item at the specified index."""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent_item()

        if parent_item == self._root_item:
            return QModelIndex()

        if parent_item:
            return self.createIndex(parent_item.row(), 0, parent_item)

        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows (children) for the given parent."""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        if parent_item._is_fetched:
             return parent_item.child_count()
        
        # For unfetched folders, return 1 to show the expandable arrow
        if parent_item.is_folder():
             return 1 # Indicate that there are children to fetch

        return 0 # Not a folder and not fetched, so no children

    def hasChildren(self, parent=QModelIndex()):
         """Returns True if the parent item has children."""
         if not parent.isValid(): # Root item
             return self._root_item.child_count() > 0 or (not self._root_item._is_fetched and self._root_item.is_folder())

         item = parent.internalPointer()
         if item.is_folder():
             return item.child_count() > 0 or not item._is_fetched
         return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Returns the header data."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return QVariant()
    
    # --- Lazy Loading --- #
    def fetchMore(self, parent):
        """Fetches more data for the specified parent index."""
        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        if parent_item.is_folder() and not parent_item._is_fetched:
            # Fetch children in a separate thread to avoid freezing the UI
            self.fetch_children(parent_item)
            
    def canFetchMore(self, parent):
        """Returns True if there is more data to fetch for the parent."""
        if not parent.isValid():
             parent_item = self._root_item
        else:
             parent_item = parent.internalPointer()
             
        return parent_item.is_folder() and not parent_item._is_fetched

    def fetch_children(self, parent_item):
        """Fetches children for the given parent item using the Google Drive API."""
        # Use a WorkerThread to fetch data asynchronously
        # We need to pass the credentials and the parent item's ID
        if not self._credentials:
             print("Error: Google Drive credentials not available.")
             parent_item._is_fetched = True # Mark as fetched to prevent repeated attempts
             self.beginInsertRows(self.index(parent_item.row(), 0, self.parent(self.createIndex(parent_item.row(), 0, parent_item))), 0, -1) # Notify views before changing data
             self.endInsertRows() # Notify views after changing data
             return

        def do_fetch():
            print(f"Fetching children for folder ID: {parent_item.item_id()}")
            return list_google_drive_files(self._credentials, parent_item.item_id())

        def on_fetch_done(result, error):
            if error:
                print(f"Error fetching Google Drive children: {error}")
                parent_item._is_fetched = True # Mark as fetched even on error to avoid loops
            elif result is not None:
                self.beginInsertRows(self.index(parent_item.row(), 0, self.parent(self.createIndex(parent_item.row(), 0, parent_item))), 0, len(result) - 1) # Notify views before changing data
                parent_item.set_children(result)
                self.endInsertRows() # Notify views after changing data
                print(f"Fetched {len(result)} children for folder ID: {parent_item.item_id()}")
            else:
                 parent_item._is_fetched = True # Mark as fetched if result is None (e.g., empty folder)
                 self.beginInsertRows(self.index(parent_item.row(), 0, self.parent(self.createIndex(parent_item.row(), 0, parent_item))), 0, -1) # Notify views before changing data
                 self.endInsertRows() # Notify views after changing data

            # Clean up the worker thread (assuming it's a simple WorkerThread like in main.py)
            # In a more complex app, you might manage threads differently
            worker_thread = self.sender() # Get the thread that emitted the signal
            if worker_thread:
                 worker_thread.quit()
                 worker_thread.wait()
                 worker_thread.deleteLater()

        # Assuming a WorkerThread class similar to the one in main.py that emits result on completion
        # You might need to adapt this based on your actual threading implementation
        from main import WorkerThread # Assuming WorkerThread is in main.py
        worker = WorkerThread(do_fetch)
        worker.result.connect(on_fetch_done)
        worker.start() 