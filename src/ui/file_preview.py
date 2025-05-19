"""
File preview component for the File System Explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QScrollArea, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtGui import QPixmap, QImage, QTextDocument
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import os
import mimetypes
from PIL import Image
import io
import fitz  # PyMuPDF for PDF preview
import wave
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class AudioWaveformWidget(QWidget):
    """Widget for displaying audio waveform."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the audio waveform UI."""
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure
        self.figure = plt.figure(figsize=(8, 2))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def plot_waveform(self, audio_path):
        """Plot audio waveform."""
        try:
            # Read audio file
            with wave.open(audio_path, 'rb') as wav_file:
                # Get audio parameters
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # Read audio data
                frames = wav_file.readframes(n_frames)
                
                # Convert to numpy array
                if sample_width == 2:
                    dtype = np.int16
                else:
                    dtype = np.int8
                
                audio_data = np.frombuffer(frames, dtype=dtype)
                
                # Convert to mono if stereo
                if n_channels == 2:
                    audio_data = audio_data.reshape((-1, 2)).mean(axis=1)
            
            # Clear previous plot
            self.figure.clear()
            
            # Create new plot
            ax = self.figure.add_subplot(111)
            ax.plot(audio_data, color='blue', linewidth=0.5)
            ax.set_axis_off()
            
            # Update canvas
            self.canvas.draw()
        
        except Exception as e:
            self._show_error(f"Error plotting waveform: {str(e)}")
    
    def _show_error(self, message):
        """Show error message."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, ha='center', va='center')
        ax.set_axis_off()
        self.canvas.draw()

class FilePreview(QWidget):
    """Widget for displaying file previews."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def _init_ui(self):
        """Initialize the preview UI components."""
        layout = QVBoxLayout(self)
        
        # Preview area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Preview content
        self.preview_content = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_content)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_layout.addWidget(self.preview_label)
        
        # Text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setVisible(False)
        self.preview_layout.addWidget(self.text_preview)
        
        # PDF preview
        self.pdf_preview = QTextEdit()
        self.pdf_preview.setReadOnly(True)
        self.pdf_preview.setVisible(False)
        self.preview_layout.addWidget(self.pdf_preview)
        
        # Audio preview
        self.audio_waveform = AudioWaveformWidget()
        self.audio_waveform.setVisible(False)
        self.preview_layout.addWidget(self.audio_waveform)
        
        # Video preview
        self.video_widget = QVideoWidget()
        self.video_widget.setVisible(False)
        self.preview_layout.addWidget(self.video_widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Progress bar for media
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.preview_layout.addWidget(self.progress_bar)
        
        self.scroll_area.setWidget(self.preview_content)
        layout.addWidget(self.scroll_area)
    
    def preview_file(self, file_path):
        """
        Preview a file's contents.
        
        Args:
            file_path: Path to the file to preview
        """
        if not os.path.exists(file_path):
            self._show_error("File not found")
            return
        
        try:
            # Hide all preview widgets
            self._hide_all_previews()
            
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if os.path.isdir(file_path):
                self._preview_directory(file_path)
            elif mime_type:
                if mime_type.startswith('image/'):
                    self._preview_image(file_path)
                elif mime_type.startswith('text/'):
                    self._preview_text(file_path)
                elif mime_type == 'application/pdf':
                    self._preview_pdf(file_path)
                elif mime_type.startswith('audio/'):
                    self._preview_audio(file_path)
                elif mime_type.startswith('video/'):
                    self._preview_video(file_path)
                else:
                    self._show_error("Preview not available for this file type")
            else:
                self._show_error("Unknown file type")
        
        except Exception as e:
            self._show_error(f"Error previewing file: {str(e)}")
    
    def _hide_all_previews(self):
        """Hide all preview widgets."""
        self.preview_label.setVisible(False)
        self.text_preview.setVisible(False)
        self.pdf_preview.setVisible(False)
        self.audio_waveform.setVisible(False)
        self.video_widget.setVisible(False)
        self.progress_bar.setVisible(False)
    
    def _preview_directory(self, dir_path):
        """Preview directory contents."""
        try:
            items = os.listdir(dir_path)
            content = f"Directory: {os.path.basename(dir_path)}\n\n"
            content += f"Path: {dir_path}\n\n"
            content += f"Contents ({len(items)} items):\n"
            
            # Sort items (directories first, then files)
            dirs = []
            files = []
            for item in items:
                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            # Add directories
            for item in sorted(dirs):
                content += f"📁 {item}/\n"
            
            # Add files
            for item in sorted(files):
                content += f"📄 {item}\n"
            
            self._show_text_preview(content)
        
        except Exception as e:
            self._show_error(f"Error reading directory: {str(e)}")
    
    def _preview_image(self, image_path):
        """Preview image file."""
        try:
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image to fit preview
                max_size = (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to QPixmap
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                
                self._show_image_preview(pixmap)
        
        except Exception as e:
            self._show_error(f"Error previewing image: {str(e)}")
    
    def _preview_text(self, text_path):
        """Preview text file."""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # Read first 10KB
                
                if len(content) == 10000:
                    content += "\n... (file truncated)"
                
                self._show_text_preview(content)
        
        except UnicodeDecodeError:
            self._show_error("File is not a text file")
        except Exception as e:
            self._show_error(f"Error reading file: {str(e)}")
    
    def _preview_pdf(self, pdf_path):
        """Preview PDF file."""
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Convert first page to image
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Convert to QPixmap
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            # Show preview
            self._show_image_preview(pixmap)
            
            # Add page count
            self.preview_label.setText(
                f"Page 1 of {len(doc)} pages\n"
                f"(Use arrow keys to navigate)"
            )
            
            # Store document for navigation
            self._current_pdf = doc
            self._current_pdf_page = 0
        
        except Exception as e:
            self._show_error(f"Error previewing PDF: {str(e)}")
    
    def _preview_audio(self, audio_path):
        """Preview audio file."""
        try:
            # Show waveform
            self.audio_waveform.setVisible(True)
            self.audio_waveform.plot_waveform(audio_path)
            
            # Set up media player
            self.media_player.setSource(QUrl.fromLocalFile(audio_path))
            self.media_player.play()
            
            # Show progress bar
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self.media_player.duration())
            
            # Update progress
            self._progress_timer = QTimer()
            self._progress_timer.timeout.connect(self._update_progress)
            self._progress_timer.start(1000)
        
        except Exception as e:
            self._show_error(f"Error previewing audio: {str(e)}")
    
    def _preview_video(self, video_path):
        """Preview video file."""
        try:
            # Show video widget
            self.video_widget.setVisible(True)
            
            # Set up media player
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            
            # Show progress bar
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self.media_player.duration())
            
            # Update progress
            self._progress_timer = QTimer()
            self._progress_timer.timeout.connect(self._update_progress)
            self._progress_timer.start(1000)
        
        except Exception as e:
            self._show_error(f"Error previewing video: {str(e)}")
    
    def _update_progress(self):
        """Update media progress bar."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.progress_bar.setValue(self.media_player.position())
    
    def _show_image_preview(self, pixmap):
        """Show image preview."""
        self.preview_label.setVisible(True)
        self.preview_label.setPixmap(pixmap)
    
    def _show_text_preview(self, text):
        """Show text preview."""
        self.text_preview.setVisible(True)
        self.text_preview.setPlainText(text)
    
    def _show_error(self, message):
        """Show error message."""
        self.preview_label.setVisible(True)
        self.preview_label.setText(f"⚠️ {message}")
    
    def clear_preview(self):
        """Clear the preview."""
        self._hide_all_previews()
        self.preview_label.setVisible(True)
        self.preview_label.clear()
        
        # Stop media playback
        if hasattr(self, '_progress_timer'):
            self._progress_timer.stop()
        self.media_player.stop()
        
        # Close PDF if open
        if hasattr(self, '_current_pdf'):
            self._current_pdf.close()
            del self._current_pdf
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if hasattr(self, '_current_pdf'):
            if event.key() == Qt.Key.Key_Right:
                self._next_pdf_page()
            elif event.key() == Qt.Key.Key_Left:
                self._prev_pdf_page()
        
        super().keyPressEvent(event)
    
    def _next_pdf_page(self):
        """Show next PDF page."""
        if self._current_pdf_page < len(self._current_pdf) - 1:
            self._current_pdf_page += 1
            self._show_pdf_page()
    
    def _prev_pdf_page(self):
        """Show previous PDF page."""
        if self._current_pdf_page > 0:
            self._current_pdf_page -= 1
            self._show_pdf_page()
    
    def _show_pdf_page(self):
        """Show current PDF page."""
        page = self._current_pdf[self._current_pdf_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self._show_image_preview(pixmap)
        self.preview_label.setText(
            f"Page {self._current_pdf_page + 1} of {len(self._current_pdf)} pages\n"
            f"(Use arrow keys to navigate)"
        ) 