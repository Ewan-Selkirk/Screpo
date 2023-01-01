import enum

import numpy as np
from PIL import Image
from PySide6.QtCore import QObject, QEvent, Slot
from PySide6.QtGui import QIcon, QPalette, QPixmap, QCloseEvent, QShortcut, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy, QPushButton, QInputDialog,
                               QStatusBar, QHBoxLayout, QScrollArea, QMenuBar, QGroupBox)

from src.utils import Utils


class Tools(enum.Enum):
    MOVE = -1
    SELECTION = 0
    BRUSH = 1
    SHAPE = 2
    BUCKET = 3

    def __str__(self):
        return self.name[0] + self.name[1:].lower() + " Tool"


class ToolButton(QPushButton):
    def __init__(self, tool: Tools):
        super().__init__()

        self.tool = tool
        self.setText(str(tool))
        self.setIcon(QIcon(f":/icons/{str(tool)}"))

        self.setBaseSize(50, 50)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)

        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        editor = self.topLevelWidget()

        if editor.currentTool is not self.tool:
            print(f"Editor: Changing tool from {editor.currentTool} to {self.tool}")

            editor.statusBar.showMessage(f"Changed tool to {self.tool}")
            editor.currentTool = self.tool


class LayerGroup(QGroupBox):
    def __init__(self, parent=None):
        super(LayerGroup, self).__init__(parent)

        self.setLayout(QVBoxLayout())

        self.imageLayers: list[Image] = parent.layers
        self.layerItems: list[LayerItem] = []

    def make_new_layer(self, index):
        self.layerItems.append(LayerItem(self.imageLayers, index))

        [self.layout().addWidget(w) for w in self.layerItems]


class LayerItem(QWidget):
    def __init__(self, layers, index):
        super().__init__()

        self.setStyleSheet("LayerItem { border-style: solid; border-width: 5px; border-color: rgb(253, 142, 53); }")

        self.layers = layers
        self.index = index

        self.layout = QVBoxLayout()

        self.name = QLabel(f"Layer {index}")

        self.thumbnail = QLabel()
        self.thumbnail.setPixmap(QPixmap(self.make_thumbnail().toqimage()))

        self.layout.addWidget(self.name)
        self.layout.addWidget(self.thumbnail)

        self.setLayout(self.layout)

        self.setBaseSize(100, 75)
        self.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        super().eventFilter(watched, event)

        if event is QEvent.Type.MouseButtonDblClick:
            print(f"{watched} doubled clicked")

            if watched is self.name:
                self.edit_layer_name()

        return False

    def edit_layer_name(self):
        text, ok = QInputDialog.getText(self, "Edit Layer Name", "New Name", text=self.name.text())

        if ok:
            self.name.setText(text)

    def make_thumbnail(self) -> Image:
        size = 128, 128
        thumbnail = self.layers[self.index - 1].copy()

        if type(thumbnail) is Image.Image:
            thumbnail.thumbnail(size)
        elif type(thumbnail) is np.ndarray:
            thumbnail = Image.fromarray(thumbnail, mode="RGBA")
            thumbnail.thumbnail(size)

        return thumbnail


class EditorWindow(QMainWindow):
    def __init__(self, parent=None, image: Image = None, utils: Utils = None):
        super(EditorWindow, self).__init__()

        self.setWindowTitle("Screpo Editor")
        self.setWindowIcon(utils.desktopIcon)

        self.parent = parent

        self.currentLayer = 0
        self.currentTool: Tools = Tools.MOVE
        self.layers = []
        self.scaleFactor = 1.0

        self.utils = utils or parent.__getattribute__("utils")
        self.image = image

        self.canvasSize = image.size
        self.layers.append(image)

        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.menuBar = QMenuBar()
        self.menuBar.setNativeMenuBar(True)
        self.create_menus()

        self.content = QHBoxLayout()

        self.content__tools = QVBoxLayout()
        [self.content__tools.addWidget(w) for w in self.make_tool_buttons()]

        self.content__image = QLabel()
        self.content__image.setBaseSize(750, 750)
        self.content__image.setPixmap(QPixmap.fromImage(self.image.toqimage()))
        self.content__image.setBackgroundRole(QPalette.ColorRole.Base)
        self.content__image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.content__image.setScaledContents(True)

        self.content__imageArea = QScrollArea()
        self.content__imageArea.setBackgroundRole(QPalette.ColorRole.Dark)
        self.content__imageArea.setWidget(self.content__image)

        self.content__layers = QVBoxLayout()

        self.layerScrollBox = QScrollArea()

        self.layersWidget = LayerGroup(self)
        self.layerItems = QVBoxLayout()

        self.layersWidget.make_new_layer(1)

        self.layerScrollBox.setWidget(self.layersWidget)
        self.layerScrollBox.setMaximumWidth(250)
        self.layerScrollBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.layer__newButton = QPushButton("+")
        self.layer__newButton.setFixedSize(20, 20)
        self.layer__newButton.clicked.connect(self._add_new_layer)

        self.layerButtons = QHBoxLayout()
        self.layerButtons.addWidget(self.layer__newButton)

        self.content__layers.addWidget(self.layerScrollBox)
        self.content__layers.addLayout(self.layerButtons)

        self.content.addLayout(self.content__tools)
        self.content.addWidget(self.content__imageArea)
        self.content.addLayout(self.content__layers)

        [self.content.setStretch(i, s) for i, s in enumerate([1, 14, 3])]

        self.statusBar = QStatusBar()

        self.setMenuBar(self.menuBar)
        self.layout.addLayout(self.content)
        self.setStatusBar(self.statusBar)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.resize(self.utils.app_ref.primaryScreen().availableSize() / 2)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parent.editorWindow = None
        super().closeEvent(event)

    def create_menus(self):
        file_menu = self.menuBar.addMenu("&File")

        file_menu.addAction("&Quit", self.close)

        edit_menu = self.menuBar.addMenu("&Edit")

        view_menu = self.menuBar.addMenu("&View")

        zoom_in = view_menu.addAction("Zoom In", self._zoom_in)
        zoom_in.setShortcut("Ctrl+=")

        zoom_out = view_menu.addAction("Zoom Out", self._zoom_out)
        zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)

    def _add_new_layer(self):
        self.layers.append(np.zeros(self.canvasSize))
        self.layersWidget.make_new_layer(len(self.layers))

    @Slot()
    def _zoom_in(self):
        self._scale_image(1.2)

    @Slot()
    def _zoom_out(self):
        self._scale_image(0.8)

    def _scale_image(self, factor):
        self.scaleFactor *= factor

        new_size = self.scaleFactor * self.content__image.pixmap().size()
        self.content__image.resize(new_size)

        self._adjust_scrollbar(self.content__imageArea.horizontalScrollBar(), factor)
        self._adjust_scrollbar(self.content__imageArea.verticalScrollBar(), factor)

    @staticmethod
    def _adjust_scrollbar(scroll, factor):
        pos = int(factor * scroll.value() + ((factor - 1) * scroll.pageStep() / 2))
        scroll.setValue(pos)

    @staticmethod
    def make_tool_buttons():
        for t in Tools:
            yield ToolButton(t)
