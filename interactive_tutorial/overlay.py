from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class OverlayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        layout = QVBoxLayout()
        self.label = QLabel("Initializing...", self)
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 0.5);")
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        
    def updateInstruction(self, text, position):
        self.label.setText(text)
        self.setGeometry(position.x(), position.y(), self.label.sizeHint().width() + 10, self.label.sizeHint().height() + 10)
