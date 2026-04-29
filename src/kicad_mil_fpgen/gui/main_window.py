"""Main application window — PySide6-based desktop UI."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStatusBar,
    QToolBar,
    QTabWidget,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon


class MainWindow(QMainWindow):
    """Top-level window for the footprint generator application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KiCad MIL IPC-7351 Footprint Generator")
        self.setMinimumSize(1200, 800)

        self._setup_actions()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()

    def _setup_actions(self):
        self.act_quit = QAction("&Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        self.act_open = QAction("&Open Library...", self)
        self.act_open.setShortcut("Ctrl+O")

        self.act_export = QAction("&Export Footprint...", self)
        self.act_export.setShortcut("Ctrl+E")

        self.act_report = QAction("Generate &Report...", self)
        self.act_report.setShortcut("Ctrl+R")

        self.act_about = QAction("&About", self)

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_export)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.act_report)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.act_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_export)
        self.addToolBar(toolbar)

    def _setup_central_widget(self):
        self.tabs = QTabWidget()
        self.tabs.addTab(QLabel("Quick Generate — coming soon"), "Quick Generate")
        self.tabs.addTab(QLabel("Advanced Editor — coming soon"), "Advanced Editor")
        self.tabs.addTab(QLabel("Library Manager — coming soon"), "Library Manager")
        self.setCentralWidget(self.tabs)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.status.showMessage("Ready")
        self.setStatusBar(self.status)
