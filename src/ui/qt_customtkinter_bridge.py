"""
Qt Bridge for CustomTkinter API - Compatibility Layer
Provides CustomTkinter-like API using PyQt6 widgets.
This allows existing code to work with minimal changes while using Qt under the hood.
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import Optional, Callable, Any, Union
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
        QTextEdit, QCheckBox, QRadioButton, QComboBox, QSpinBox, QDoubleSpinBox,
        QSlider, QProgressBar, QTabWidget, QScrollArea, QVBoxLayout,
        QHBoxLayout, QGridLayout, QSizePolicy, QApplication, QFileDialog,
        QMessageBox, QInputDialog, QScrollBar
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
    from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QImage
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QMainWindow = object
    QWidget = object

logger = logging.getLogger(__name__)


class CTk(QMainWindow):
    """Qt-based replacement for customtkinter.CTk main window."""
    
    def __init__(self):
        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 is required for Qt UI")
        
        super().__init__()
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        self._main_layout = QVBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # Track child widgets for winfo_children compatibility
        self._children = []
        
        # For iconphoto compatibility
        self._icon_photo = None
        
    def title(self, text: str):
        """Set window title."""
        self.setWindowTitle(text)
    
    def geometry(self, geom: str):
        """Set window geometry in format 'WIDTHxHEIGHT' or 'WIDTHxHEIGHT+X+Y'."""
        if '+' in geom:
            size_part, pos_part = geom.split('+', 1)
            width, height = map(int, size_part.split('x'))
            x, y = map(int, pos_part.split('+'))
            self.setGeometry(x, y, width, height)
        else:
            width, height = map(int, geom.split('x'))
            self.resize(width, height)
    
    def minsize(self, width: int, height: int):
        """Set minimum window size."""
        self.setMinimumSize(width, height)
    
    def protocol(self, protocol: str, callback: Callable):
        """Set protocol handler (e.g., WM_DELETE_WINDOW)."""
        if protocol == "WM_DELETE_WINDOW":
            self.closeEvent = lambda event: callback() or event.ignore()
    
    def iconbitmap(self, path: str):
        """Set window icon from .ico file."""
        self.setWindowIcon(QIcon(path))
    
    def iconphoto(self, default: bool, photo):
        """Set window icon from PhotoImage."""
        # Store reference to prevent garbage collection
        self._icon_photo = photo
        # Qt icons are set via iconbitmap or setWindowIcon
    
    def after(self, ms: int, callback: Callable):
        """Execute callback after delay in milliseconds."""
        QTimer.singleShot(ms, callback)
    
    def configure(self, **kwargs):
        """Configure widget properties."""
        if 'fg_color' in kwargs:
            color = kwargs['fg_color']
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(color))
            self.setPalette(palette)
    
    def winfo_children(self):
        """Get list of child widgets."""
        return self._children
    
    def winfo_exists(self):
        """Check if widget exists."""
        return not self.isHidden()
    
    def winfo_screenwidth(self):
        """Get screen width."""
        screen = QApplication.primaryScreen()
        return screen.size().width()
    
    def winfo_screenheight(self):
        """Get screen height."""
        screen = QApplication.primaryScreen()
        return screen.size().height()
    
    def destroy(self):
        """Destroy the window."""
        self.close()
    
    def mainloop(self):
        """Start Qt event loop (handled by QApplication)."""
        # This is called from main, but QApplication.exec() is used instead
        pass


class CTkToplevel(QWidget):
    """Qt-based replacement for customtkinter.CTkToplevel (dialog/window)."""
    
    def __init__(self, master=None):
        super().__init__(parent=master, flags=Qt.WindowType.Window)
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
    
    def title(self, text: str):
        self.setWindowTitle(text)
    
    def geometry(self, geom: str):
        if '+' in geom:
            size_part, pos_part = geom.split('+', 1)
            width, height = map(int, size_part.split('x'))
            x, y = map(int, pos_part.split('+'))
            self.setGeometry(x, y, width, height)
        else:
            width, height = map(int, geom.split('x'))
            self.resize(width, height)
    
    def overrideredirect(self, flag: bool):
        """Remove window decorations."""
        if flag:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    
    def winfo_screenwidth(self):
        screen = QApplication.primaryScreen()
        return screen.size().width()
    
    def winfo_screenheight(self):
        screen = QApplication.primaryScreen()
        return screen.size().height()
    
    def update(self):
        """Process pending events."""
        QApplication.processEvents()
    
    def after(self, ms: int, callback: Callable):
        QTimer.singleShot(ms, callback)
    
    def destroy(self):
        self.close()


class CTkFrame(QFrame):
    """Qt-based replacement for customtkinter.CTkFrame."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self._layout = None
        
        # Handle corner_radius (Qt uses stylesheet)
        corner_radius = kwargs.get('corner_radius', 0)
        if corner_radius > 0:
            self.setStyleSheet(f"border-radius: {corner_radius}px;")
        
        # Handle border
        border_width = kwargs.get('border_width', 0)
        border_color = kwargs.get('border_color', '#000000')
        if border_width > 0:
            self.setStyleSheet(f"border: {border_width}px solid {border_color};")
        
        # Handle height
        height = kwargs.get('height', None)
        if height:
            self.setFixedHeight(height)
    
    def pack(self, **kwargs):
        """Pack widget (simulated via parent layout)."""
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        # Handle fill and expand
        fill = kwargs.get('fill', None)
        expand = kwargs.get('expand', False)
        
        if fill == 'both' or expand:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        elif fill == 'x':
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        elif fill == 'y':
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)


class CTkLabel(QLabel):
    """Qt-based replacement for customtkinter.CTkLabel."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        # Handle text
        text = kwargs.get('text', '')
        self.setText(text)
        
        # Handle font
        font = kwargs.get('font', None)
        if font:
            font_family, font_size = font[0], font[1]
            qfont = QFont(font_family, font_size)
            if 'Bold' in font_family:
                qfont.setBold(True)
            self.setFont(qfont)
        
        # Handle text color
        text_color = kwargs.get('text_color', None)
        if text_color:
            self.setStyleSheet(f"color: {text_color};")
        
        # Handle image (CTkImage support)
        image = kwargs.get('image', None)
        if image and hasattr(image, '_qt_pixmap'):
            self.setPixmap(image._qt_pixmap)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        # Handle padding
        pady = kwargs.get('pady', 0)
        padx = kwargs.get('padx', 0)
        if isinstance(pady, tuple):
            # Margins: top, bottom
            self.setContentsMargins(padx, pady[0], padx, pady[1])
        else:
            self.setContentsMargins(padx, pady, padx, pady)


class CTkButton(QPushButton):
    """Qt-based replacement for customtkinter.CTkButton."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        # Handle text
        text = kwargs.get('text', '')
        self.setText(text)
        
        # Handle command
        command = kwargs.get('command', None)
        if command:
            self.clicked.connect(command)
        
        # Handle width
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
        
        # Handle font
        font = kwargs.get('font', None)
        if font:
            font_family, font_size = font[0], font[1]
            qfont = QFont(font_family, font_size)
            if 'Bold' in font_family:
                qfont.setBold(True)
            self.setFont(qfont)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        side = kwargs.get('side', None)
        if side == 'right':
            # Add stretch before to push to right
            if hasattr(self.parent(), '_layout'):
                self.parent()._layout.addStretch()
        
        padx = kwargs.get('padx', 0)
        pady = kwargs.get('pady', 0)
        if isinstance(pady, tuple):
            self.setContentsMargins(padx, pady[0], padx, pady[1])
        else:
            self.setContentsMargins(padx, pady, padx, pady)


class CTkCheckBox(QCheckBox):
    """Qt-based replacement for customtkinter.CTkCheckBox."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        text = kwargs.get('text', '')
        self.setText(text)
        
        variable = kwargs.get('variable', None)
        if variable:
            self._variable = variable
            self.setChecked(variable.get())
            self.stateChanged.connect(lambda state: variable.set(state == Qt.CheckState.Checked.value))
        
        command = kwargs.get('command', None)
        if command:
            self.stateChanged.connect(lambda: command())
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)


class BooleanVar:
    """Qt-compatible variable for boolean values."""
    
    def __init__(self, value=False):
        self._value = value
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = value


class CTkImage:
    """Qt-based replacement for CTkImage."""
    
    def __init__(self, light_image=None, dark_image=None, size=(20, 20)):
        self._light_image = light_image
        self._dark_image = dark_image
        self._size = size
        
        # Convert PIL image to QPixmap
        image = light_image or dark_image
        if image:
            # Convert PIL to QPixmap
            if hasattr(image, 'convert'):
                image = image.convert('RGBA')
                data = image.tobytes('raw', 'RGBA')
                qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
                self._qt_pixmap = QPixmap.fromImage(qimage).scaled(
                    size[0], size[1], Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            else:
                self._qt_pixmap = QPixmap()


# Qt dialog replacements for tkinter dialogs
class filedialog:
    """Qt file dialog replacements."""
    
    @staticmethod
    def askopenfilename(**kwargs):
        """Open file dialog."""
        title = kwargs.get('title', 'Open File')
        filetypes = kwargs.get('filetypes', [])
        initialdir = kwargs.get('initialdir', '')
        
        # Convert filetypes to Qt format
        filter_str = ';;'.join([f"{name} ({ext})" for name, ext in filetypes]) if filetypes else ''
        
        filename, _ = QFileDialog.getOpenFileName(None, title, initialdir, filter_str)
        return filename
    
    @staticmethod
    def askdirectory(**kwargs):
        """Open directory dialog."""
        title = kwargs.get('title', 'Select Directory')
        initialdir = kwargs.get('initialdir', '')
        
        dirname = QFileDialog.getExistingDirectory(None, title, initialdir)
        return dirname
    
    @staticmethod
    def askopenfilenames(**kwargs):
        """Open multiple files dialog."""
        title = kwargs.get('title', 'Open Files')
        filetypes = kwargs.get('filetypes', [])
        initialdir = kwargs.get('initialdir', '')
        
        filter_str = ';;'.join([f"{name} ({ext})" for name, ext in filetypes]) if filetypes else ''
        
        filenames, _ = QFileDialog.getOpenFileNames(None, title, initialdir, filter_str)
        return filenames
    
    @staticmethod
    def asksaveasfilename(**kwargs):
        """Save file dialog."""
        title = kwargs.get('title', 'Save File')
        defaultextension = kwargs.get('defaultextension', '')
        filetypes = kwargs.get('filetypes', [])
        initialdir = kwargs.get('initialdir', '')
        initialfile = kwargs.get('initialfile', '')
        
        filter_str = ';;'.join([f"{name} ({ext})" for name, ext in filetypes]) if filetypes else ''
        
        filename, _ = QFileDialog.getSaveFileName(None, title, str(Path(initialdir) / initialfile), filter_str)
        return filename


class messagebox:
    """Qt message box replacements."""
    
    @staticmethod
    def showinfo(title, message):
        """Show information message."""
        QMessageBox.information(None, title, message)
    
    @staticmethod
    def showwarning(title, message):
        """Show warning message."""
        QMessageBox.warning(None, title, message)
    
    @staticmethod
    def showerror(title, message):
        """Show error message."""
        QMessageBox.critical(None, title, message)
    
    @staticmethod
    def askyesno(title, message):
        """Ask yes/no question."""
        result = QMessageBox.question(None, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return result == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def askyesnocancel(title, message):
        """Ask yes/no/cancel question."""
        result = QMessageBox.question(None, title, message,
                                     QMessageBox.StandardButton.Yes | 
                                     QMessageBox.StandardButton.No | 
                                     QMessageBox.StandardButton.Cancel)
        if result == QMessageBox.StandardButton.Yes:
            return True
        elif result == QMessageBox.StandardButton.No:
            return False
        else:
            return None
    
    @staticmethod
    def askokcancel(title, message):
        """Ask OK/cancel question."""
        result = QMessageBox.question(None, title, message,
                                     QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        return result == QMessageBox.StandardButton.Ok


class simpledialog:
    """Qt simple dialog replacements."""
    
    @staticmethod
    def askstring(title, prompt, **kwargs):
        """Ask for string input."""
        text, ok = QInputDialog.getText(None, title, prompt)
        return text if ok else None




class CTkEntry(QLineEdit):
    """Qt-based replacement for customtkinter.CTkEntry."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        placeholder = kwargs.get('placeholder_text', '')
        if placeholder:
            self.setPlaceholderText(placeholder)
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def get(self):
        """Get entry text."""
        return self.text()
    
    def delete(self, start, end='end'):
        """Delete text."""
        if end == 'end':
            self.clear()
        else:
            text = self.text()
            self.setText(text[:start] + text[end:])
    
    def insert(self, index, text):
        """Insert text."""
        current = self.text()
        if index == 'end' or index >= len(current):
            self.setText(current + text)
        else:
            self.setText(current[:index] + text + current[index:])


class CTkTextbox(QTextEdit):
    """Qt-based replacement for customtkinter.CTkTextbox."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        width = kwargs.get('width', None)
        height = kwargs.get('height', None)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        
        # Handle wrap
        wrap = kwargs.get('wrap', 'word')
        if wrap == 'none':
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        fill = kwargs.get('fill', None)
        expand = kwargs.get('expand', False)
        
        if fill == 'both' or expand:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        elif fill == 'x':
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        elif fill == 'y':
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    
    def insert(self, position, text):
        """Insert text at position."""
        if position == 'end' or position == '0.0':
            self.append(text.rstrip('\n'))
        else:
            self.insertPlainText(text)
    
    def see(self, position):
        """Scroll to position."""
        if position == 'end':
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


class CTkProgressBar(QProgressBar):
    """Qt-based replacement for customtkinter.CTkProgressBar."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.setRange(0, 100)
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def set(self, value):
        """Set progress value (0.0 to 1.0)."""
        self.setValue(int(value * 100))
    
    def get(self):
        """Get progress value (0.0 to 1.0)."""
        return self.value() / 100.0


class CTkSlider(QSlider):
    """Qt-based replacement for customtkinter.CTkSlider."""
    
    def __init__(self, master, **kwargs):
        orientation = kwargs.get('orientation', 'horizontal')
        if orientation == 'horizontal':
            super().__init__(Qt.Orientation.Horizontal, master)
        else:
            super().__init__(Qt.Orientation.Vertical, master)
        
        from_val = kwargs.get('from_', 0)
        to_val = kwargs.get('to', 100)
        self.setRange(int(from_val), int(to_val))
        
        # Store variable
        variable = kwargs.get('variable', None)
        if variable:
            self._variable = variable
            self.setValue(int(variable.get()))
            self.valueChanged.connect(lambda val: variable.set(val))
        
        command = kwargs.get('command', None)
        if command:
            self.valueChanged.connect(lambda val: command(val))
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def set(self, value):
        """Set slider value."""
        self.setValue(int(value))
    
    def get(self):
        """Get slider value."""
        return self.value()


class CTkComboBox(QComboBox):
    """Qt-based replacement for customtkinter.CTkComboBox."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        values = kwargs.get('values', [])
        if values:
            self.addItems(values)
        
        variable = kwargs.get('variable', None)
        if variable:
            self._variable = variable
            self.setCurrentText(str(variable.get()))
            self.currentTextChanged.connect(lambda text: variable.set(text))
        
        command = kwargs.get('command', None)
        if command:
            self.currentTextChanged.connect(lambda text: command(text))
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def set(self, value):
        """Set selected value."""
        self.setCurrentText(str(value))
    
    def get(self):
        """Get selected value."""
        return self.currentText()


class CTkOptionMenu(QComboBox):
    """Qt-based replacement for customtkinter.CTkOptionMenu."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        values = kwargs.get('values', [])
        if values:
            self.addItems(values)
        
        variable = kwargs.get('variable', None)
        if variable:
            self._variable = variable
            self.setCurrentText(str(variable.get()))
            self.currentTextChanged.connect(lambda text: variable.set(text))
        
        command = kwargs.get('command', None)
        if command:
            self.currentTextChanged.connect(lambda text: command(text))
        
        width = kwargs.get('width', None)
        if width:
            self.setFixedWidth(width)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def set(self, value):
        """Set selected value."""
        self.setCurrentText(str(value))
    
    def get(self):
        """Get selected value."""
        return self.currentText()


class CTkRadioButton(QRadioButton):
    """Qt-based replacement for customtkinter.CTkRadioButton."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        text = kwargs.get('text', '')
        self.setText(text)
        
        variable = kwargs.get('variable', None)
        value = kwargs.get('value', None)
        if variable and value is not None:
            self._variable = variable
            self._value = value
            self.setChecked(variable.get() == value)
            self.toggled.connect(lambda checked: variable.set(value) if checked else None)
        
        command = kwargs.get('command', None)
        if command:
            self.toggled.connect(lambda: command())
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)


class CTkSwitch(QCheckBox):
    """Qt-based replacement for customtkinter.CTkSwitch."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        text = kwargs.get('text', '')
        self.setText(text)
        
        variable = kwargs.get('variable', None)
        if variable:
            self._variable = variable
            self.setChecked(variable.get())
            self.stateChanged.connect(lambda state: variable.set(state == Qt.CheckState.Checked.value))
        
        command = kwargs.get('command', None)
        if command:
            self.stateChanged.connect(lambda: command())
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)


class StringVar:
    """Qt-compatible variable for string values."""
    
    def __init__(self, value=''):
        self._value = value
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = str(value)


class IntVar:
    """Qt-compatible variable for integer values."""
    
    def __init__(self, value=0):
        self._value = int(value)
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = int(value)


class DoubleVar:
    """Qt-compatible variable for float values."""
    
    def __init__(self, value=0.0):
        self._value = float(value)
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = float(value)


class CTkScrollableFrame(QScrollArea):
    """Qt-based replacement for customtkinter.CTkScrollableFrame."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        # Create inner widget
        self._inner_widget = QWidget()
        self._layout = QVBoxLayout(self._inner_widget)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.setWidget(self._inner_widget)
        self.setWidgetResizable(True)
        
        width = kwargs.get('width', None)
        height = kwargs.get('height', None)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        fill = kwargs.get('fill', None)
        expand = kwargs.get('expand', False)
        
        if fill == 'both' or expand:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        elif fill == 'x':
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        elif fill == 'y':
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)


class CTkTabview(QTabWidget):
    """Qt-based replacement for customtkinter.CTkTabview."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self._tabs = {}
        
        width = kwargs.get('width', None)
        height = kwargs.get('height', None)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
        
        fill = kwargs.get('fill', None)
        expand = kwargs.get('expand', False)
        
        if fill == 'both' or expand:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def add(self, name):
        """Add a new tab."""
        if name not in self._tabs:
            tab_widget = QWidget()
            tab_widget._layout = QVBoxLayout(tab_widget)
            self._tabs[name] = tab_widget
            self.addTab(tab_widget, name)
        return self._tabs[name]
    
    def tab(self, name):
        """Get tab by name."""
        return self._tabs.get(name)


class CTkSegmentedButton(QWidget):
    """Qt-based replacement for customtkinter.CTkSegmentedButton."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self._buttons = []
        self._variable = kwargs.get('variable', None)
        self._command = kwargs.get('command', None)
        
        values = kwargs.get('values', [])
        for value in values:
            btn = QPushButton(value)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=value: self._on_button_click(v))
            self._buttons.append(btn)
            self._layout.addWidget(btn)
    
    def _on_button_click(self, value):
        """Handle button click."""
        # Uncheck all other buttons
        for btn in self._buttons:
            if btn.text() != value:
                btn.setChecked(False)
        
        if self._variable:
            self._variable.set(value)
        if self._command:
            self._command(value)
    
    def pack(self, **kwargs):
        if self.parent() and hasattr(self.parent(), '_layout'):
            parent_layout = self.parent()._layout
            if parent_layout:
                parent_layout.addWidget(self)
    
    def set(self, value):
        """Set selected value."""
        for btn in self._buttons:
            btn.setChecked(btn.text() == value)
    
    def get(self):
        """Get selected value."""
        for btn in self._buttons:
            if btn.isChecked():
                return btn.text()
        return None


def set_appearance_mode(mode: str):
    """Set Qt appearance mode (dark/light)."""
    if mode == 'dark':
        # Apply dark palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(37, 37, 37))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        QApplication.instance().setPalette(palette)


def set_default_color_theme(theme: str):
    """Set Qt default color theme."""
    # This is handled by stylesheets in Qt
    pass


def set_widget_scaling(scale: float):
    """Set Qt widget scaling."""
    font = QApplication.font()
    font.setPointSizeF(font.pointSizeF() * scale)
    QApplication.setFont(font)


def set_window_scaling(scale: float):
    """Set Qt window scaling."""
    # Qt handles DPI scaling automatically
    pass
