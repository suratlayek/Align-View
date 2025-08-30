import sys
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import (
    Qt, QPoint, QEvent, pyqtSignal, pyqtSlot, QCoreApplication,QFile, QTextStream
)
from PyQt5.QtGui import (
    QPixmap, QTransform, QMouseEvent, QWheelEvent, QCloseEvent, QDragEnterEvent, QDropEvent, QKeyEvent,QIcon
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QMessageBox, QFileDialog
)

# Import the UI definition from the separate UI file
from src.align_view_ui import Ui_ControlPanel
import src.resources_rc

APP_TITLE = "Align View"

#def load_stylesheet(file_path):
#    with open(file_path, "r") as f:
#        return f.read()
def load_stylesheet(path):
    """Loads a QSS file from the Qt resource system."""
    file = QFile(path)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        return stream.readAll()
    return ""

qss = load_stylesheet(":/adaptic.qss")

@dataclass
class OverlayState:
    """A simple data class to hold the overlay's current state."""
    opacity: float = 0.7
    scale: float = 1.0  # 1.0 = 100%
    rotation: float = 0.0  # degrees
    click_through: bool = False
    keep_on_top: bool = True
    mouse_events_locked: bool = False
    image_path: Optional[str] = None


class OverlayWindow(QWidget):
    """Frameless, draggable window that renders the transformed image."""

    # --- Signals for state changes ---
    opacity_changed = pyqtSignal(float)
    scale_changed = pyqtSignal(float)
    rotation_changed = pyqtSignal(float)
    view_reset = pyqtSignal()

    # --- Constants for mouse wheel actions ---
    WHEEL_ROTATE_STEP = 0.1   # 0.1 degrees per step
    WHEEL_OPACITY_STEP = 0.05 # 5% per step
    WHEEL_SCALE_FACTOR = 0.005 # 8% change per step

    def __init__(self):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle(APP_TITLE)

        self._pix: Optional[QPixmap] = None
        self._state = OverlayState()
        self.panel: Optional['ControlPanel'] = None

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        self._dragging = False
        self._drag_start_pos = QPoint()

        self.setAcceptDrops(True)
        self._label.installEventFilter(self)

        self.update_placeholder()

    def set_image(self, path: str) -> bool:
        pix = QPixmap(path)
        if pix.isNull():
            return False
        self._pix = pix
        self._state.image_path = path
        screen = QApplication.primaryScreen().availableGeometry()
        max_w, max_h = int(screen.width() * 0.6), int(screen.height() * 0.6)
        w, h = pix.width(), pix.height()
        scale = min(1.0, max_w / w if w > 0 else 1.0, max_h / h if h > 0 else 1.0)
        self._state.scale = scale
        self._state.rotation = 0.0
        self._apply_all()
        self.showNormal()
        return True

    def close_image(self):
        self._pix = None
        self._state.image_path = None
        self._label.clear()
        self.update_placeholder()
        self.reset_view()

    def set_opacity(self, value: float):
        self._state.opacity = max(0.1, min(1.0, value))
        self.setWindowOpacity(self._state.opacity)
        self.opacity_changed.emit(self._state.opacity)

    def set_scale(self, scale: float):
        self._state.scale = max(0.001, min(4.0, scale))
        self._apply_transform()
        self.scale_changed.emit(self._state.scale)

    def set_rotation(self, deg: float):
        self._state.rotation = ((deg + 180.0) % 360.0) - 180.0
        self._apply_transform()
        self.rotation_changed.emit(self._state.rotation)

    def set_click_through(self, enabled: bool):
        self._state.click_through = enabled
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
        try:
            self.setWindowFlag(Qt.WindowTransparentForInput, enabled)
        except AttributeError:
            pass
        self.show()

    def set_keep_on_top(self, enabled: bool):
        self._state.keep_on_top = enabled
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.show()

    def set_mouse_lock(self, locked: bool):
        self._state.mouse_events_locked = locked

    def reset_view(self):
        self._state.scale = 1.0
        self._state.rotation = 0.0
        self._apply_transform()
        self.view_reset.emit()

    def current_state(self) -> OverlayState:
        return self._state

    def update_placeholder(self):
        if self._pix is None:
            self._label.setText(
                "<div style='color:#bbb; font-size:14px; padding:14px;'>"
                "<b>No image loaded</b><br/>"
                "Drag & Drop an image in the Control Panel."
                "</div>"
            )
        else:
            self._label.setText("")

    def _apply_all(self):
        self.set_opacity(self._state.opacity)
        self._apply_transform()
        self.update_placeholder()
        self.scale_changed.emit(self._state.scale)
        self.rotation_changed.emit(self._state.rotation)

    def _apply_transform(self):
        if self._pix is None:
            self.resize(300, 100)
            return
        t = QTransform()
        t.rotate(self._state.rotation)
        transformed = self._pix.transformed(t, Qt.SmoothTransformation)
        sw = max(1, int(round(transformed.width() * self._state.scale)))
        sh = max(1, int(round(transformed.height() * self._state.scale)))
        display_pixmap = transformed.scaled(sw, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._label.setPixmap(display_pixmap)
        self.resize(display_pixmap.size())

    def eventFilter(self, source, event):
        if source is self._label:
            if event.type() == QEvent.DragEnter:
                self.dragEnterEvent(event)
                return True
            elif event.type() == QEvent.Drop:
                self.dropEvent(event)
                return True
        return super().eventFilter(source, event)

    def closeEvent(self, event: QCloseEvent):
        if self.panel:
            self.panel.close()
        super().closeEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                if not self.set_image(path):
                    QMessageBox.warning(self, APP_TITLE, "Could not load this file.")
                if self.panel:
                    self.panel.sync_controls_to_state()
        event.acceptProposedAction()

    def mousePressEvent(self, e: QMouseEvent):
        if self._state.click_through:
            e.ignore()
            return
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()
        elif e.button() == Qt.RightButton:
            QMessageBox.information(self, APP_TITLE,
                "Shortcuts (when overlay is focused):\n"
                "  Mouse wheel: Zoom\n"
                "  Shift+Wheel: Rotate\n"
                "  Ctrl+Wheel: Opacity\n\n"
                "Keyboard Movement:\n"
                "  Ctrl + Arrow Keys: Move 1px\n"
                "  Shift + Arrow Keys: Move 10px")

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._state.click_through or not self._dragging:
            e.ignore()
            return
        self.move(e.globalPos() - self._drag_start_pos)
        e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._dragging = False
        e.accept()

    def wheelEvent(self, e: QWheelEvent):
        if self._state.click_through or self._state.mouse_events_locked:
            e.ignore()
            return
        delta = e.angleDelta().y() / 120.0
        mods = QApplication.keyboardModifiers()
        if mods & Qt.ShiftModifier:
            self.set_rotation(self._state.rotation + delta * self.WHEEL_ROTATE_STEP)
        elif mods & Qt.ControlModifier:
            self.set_opacity(self._state.opacity + delta * self.WHEEL_OPACITY_STEP)
        else:
            scale_multiplier = 1.0 + delta * self.WHEEL_SCALE_FACTOR
            self.set_scale(self._state.scale * scale_multiplier)

    def keyPressEvent(self, event: QKeyEvent):
        if self._state.click_through:
            event.ignore()
            return
        mods = event.modifiers()
        key = event.key()
        step = 0
        if mods == Qt.ControlModifier:
            step = 1
        elif mods == Qt.ShiftModifier:
            step = 10
        if step > 0:
            moved = False
            if key == Qt.Key_Left:
                self.move(self.x() - step, self.y()); moved = True
            elif key == Qt.Key_Right:
                self.move(self.x() + step, self.y()); moved = True
            elif key == Qt.Key_Up:
                self.move(self.x(), self.y() - step); moved = True
            elif key == Qt.Key_Down:
                self.move(self.x(), self.y() + step); moved = True
            if moved:
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class ControlPanel(QWidget):
    """A compact controller window for managing the overlay."""
    def __init__(self, overlay: OverlayWindow):
        super().__init__(None, Qt.Window)
        self.setWindowTitle(f"{APP_TITLE} - Control Panel")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self._overlay = overlay
        
        # Set up the UI from the imported class
        self.ui = Ui_ControlPanel()
        self.ui.setupUi(self)

        self.setAcceptDrops(True)
        
        # Position near the top-right of the screen
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.right() - self.width() - 24, screen_geo.top() + 24)
        
        # --- Initial State & Connections ---
        # FIX: Set the initial step values before connecting signals
        self.ui.scale_spin.setSingleStep(self.ui.scale_step_spin.value())
        self.ui.rot_spin.setSingleStep(self.ui.rot_step_spin.value())
        
        self.sync_controls_to_state()
        self._connect_signals()

    def _connect_signals(self):
        """Connects widget signals to overlay slots and vice versa."""
        self.ui.open_btn.clicked.connect(self.open_image)
        self.ui.close_img_btn.clicked.connect(self._overlay.close_image)
        self.ui.minimize_btn.clicked.connect(self._overlay.showMinimized)
        self.ui.show_btn.clicked.connect(self.show_overlay)
        self.ui.reset_btn.clicked.connect(self._overlay.reset_view)
        self.ui.opacity_slider.valueChanged.connect(lambda v: self._overlay.set_opacity(v / 100.0))
        self.ui.scale_spin.valueChanged.connect(self._overlay.set_scale)
        self.ui.rot_spin.valueChanged.connect(self._overlay.set_rotation)
        self.ui.top_cb.toggled.connect(self._overlay.set_keep_on_top)
        self.ui.click_cb.toggled.connect(self._overlay.set_click_through)
        self.ui.lock_cb.toggled.connect(self._overlay.set_mouse_lock)
        
        # Connect the step spin boxes to update the main spin boxes' singleStep property
        self.ui.scale_step_spin.valueChanged.connect(self.ui.scale_spin.setSingleStep)
        self.ui.rot_step_spin.valueChanged.connect(self.ui.rot_spin.setSingleStep)

        # Connect signals from the overlay back to the control panel
        self._overlay.opacity_changed.connect(lambda v: self.ui.opacity_slider.setValue(int(v * 100)))
        self._overlay.scale_changed.connect(self.ui.scale_spin.setValue)
        self._overlay.rotation_changed.connect(self.ui.rot_spin.setValue)
        self._overlay.view_reset.connect(self.sync_controls_to_state)

    @pyqtSlot()
    def sync_controls_to_state(self):
        st = self._overlay.current_state()
        # Block signals to prevent feedback loops while setting values
        self.ui.opacity_slider.blockSignals(True)
        self.ui.scale_spin.blockSignals(True)
        self.ui.rot_spin.blockSignals(True)
        self.ui.top_cb.blockSignals(True)
        self.ui.click_cb.blockSignals(True)
        self.ui.lock_cb.blockSignals(True)

        self.ui.opacity_slider.setValue(int(st.opacity * 100))
        self.ui.scale_spin.setValue(st.scale)
        self.ui.rot_spin.setValue(st.rotation)
        self.ui.top_cb.setChecked(st.keep_on_top)
        self.ui.click_cb.setChecked(st.click_through)
        self.ui.lock_cb.setChecked(st.mouse_events_locked)

        # Unblock signals
        self.ui.opacity_slider.blockSignals(False)
        self.ui.scale_spin.blockSignals(False)
        self.ui.rot_spin.blockSignals(False)
        self.ui.top_cb.blockSignals(False)
        self.ui.click_cb.blockSignals(False)
        self.ui.lock_cb.blockSignals(False)

    @pyqtSlot()
    def show_overlay(self):
        self._overlay.showNormal()
        self._overlay.activateWindow()

    @pyqtSlot()
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;All Files (*)",
        )
        if path:
            if not self._overlay.set_image(path):
                QMessageBox.warning(self, APP_TITLE, "Could not load this file.")
        self.sync_controls_to_state()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                if not self._overlay.set_image(path):
                    QMessageBox.warning(self, APP_TITLE, "Could not load this file.")
                self.sync_controls_to_state()
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent):
        QApplication.instance().quit()
        event.accept()


class App:
    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setWindowIcon(QIcon(':/align_view_icon.png'))
        self.qapp.setStyleSheet(qss)
        self.overlay = OverlayWindow()
        self.panel = ControlPanel(self.overlay)
        self.overlay.panel = self.panel
        self.panel.show()
        self.overlay.show()

    def run(self):
        sys.exit(self.qapp.exec_())


if __name__ == "__main__":
    app = App()
    app.run()

