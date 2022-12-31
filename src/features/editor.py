import enum

import numpy as np
from PIL import Image
from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QIcon, QPalette, QPixmap, QCloseEvent
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy, QPushButton, QInputDialog, \
    QStatusBar, QHBoxLayout, QScrollArea, QMenuBar

from src.utils import Utils


class Tools(enum.Enum):
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

        print(f"Editor: Changing tool from {editor.currentTool} to {self.tool}")

        editor.statusBar.showMessage(f"Changed tool to {self.tool}")
        editor.currentTool = self.tool


class LayerItem(QWidget):
    def __init__(self, index):
        super().__init__()

        self.layout = QVBoxLayout()

        self.name = QLabel(f"Layer {index}")

        self.thumbnail = QLabel()

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


class EditorWindow(QMainWindow):
    def __init__(self, parent=None, image: Image = None, utils: Utils = None):
        super(EditorWindow, self).__init__()

        self.setWindowTitle("Screpo Editor")
        self.setWindowIcon(utils.desktopIcon)

        self.parent = parent

        self.currentLayer = 0
        self.currentTool: Tools = Tools.SELECTION
        self.layers = []

        self.utils = utils or parent.__getattribute__("utils")
        self.image = image

        self.canvasSize = image.size
        self.layers.append(image.getbands())

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

        self.content__imageArea = QScrollArea()
        self.content__imageArea.setBackgroundRole(QPalette.ColorRole.Dark)
        self.content__imageArea.setWidget(self.content__image)

        self.content__layers = QVBoxLayout()

        self.layerScrollBox = QScrollArea()

        self.layersWidget = QWidget()
        self.layerItems = QVBoxLayout()
        self.layersWidget.setLayout(self.layerItems)

        self.layerItems.addWidget(LayerItem(1))

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

        [self.content.setStretch(i, s) for i, s in enumerate([1, 9, 2])]

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

    def _add_new_layer(self):
        self.layers.append(np.zeros(self.image.size))
        self.layerItems.addWidget(LayerItem(len(self.layers)))

    @staticmethod
    def make_tool_buttons():
        for t in Tools:
            yield ToolButton(t)

