from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QDateTimeEdit, QComboBox, QTextEdit, QFormLayout, QMessageBox
from PySide6.QtCore import QDateTime, Qt
import json
import os

REMINDERS_FILE = 'reminders.json'

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=4)

class ReminderDialog(QDialog):
    def __init__(self, file_path, parent=None, existing_reminder=None):
        super().__init__(parent)
        self.file_path = file_path
        self.existing_reminder = existing_reminder # Store existing reminder data

        if existing_reminder:
            self.setWindowTitle('Edit Reminder for '+ os.path.basename(file_path))
        else:
            self.setWindowTitle('Set Reminder for '+ os.path.basename(file_path))

        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        form_layout.addRow('Date & Time:', self.datetime_edit)

        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(['None', 'Daily', 'Weekly', 'Monthly', 'Yearly'])
        form_layout.addRow('Repeat:', self.recurrence_combo)

        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText('Custom message (optional)')
        form_layout.addRow('Message:', self.message_edit)

        self.action_combo = QComboBox()
        self.action_combo.addItems(['Notify Only', 'Open File', 'Open Folder'])
        form_layout.addRow('Action on Reminder:', self.action_combo)

        layout.addLayout(form_layout)

        if existing_reminder:
            self.save_btn = QPushButton('Save Changes', clicked=self.save_reminder)
            self.load_existing_data()
        else:
            self.save_btn = QPushButton('Set Reminder', clicked=self.save_reminder)
        layout.addWidget(self.save_btn)

    def load_existing_data(self):
        """Load existing reminder data into the form"""
        if self.existing_reminder:
            self.datetime_edit.setDateTime(QDateTime.fromString(self.existing_reminder['datetime'], Qt.ISODate))
            self.recurrence_combo.setCurrentText(self.existing_reminder['recurrence'])
            self.message_edit.setPlainText(self.existing_reminder['message'])
            self.action_combo.setCurrentText(self.existing_reminder['action'])

    def save_reminder(self):
        reminders = load_reminders()
        
        if self.existing_reminder:
            # Find and update the existing reminder
            reminders = [r for r in reminders if r != self.existing_reminder] # Remove old version

        reminder = {
            'file_path': self.file_path,
            'datetime': self.datetime_edit.dateTime().toString(Qt.ISODate),
            'recurrence': self.recurrence_combo.currentText(),
            'message': self.message_edit.toPlainText(),
            'action': self.action_combo.currentText(),
            'set_time': QDateTime.currentDateTime().toString(Qt.ISODate) # Update set time on edit
        }
        reminders.append(reminder)
        save_reminders(reminders)
        QMessageBox.information(self, 'Reminder Saved', 'Reminder saved successfully!')
        self.accept() 