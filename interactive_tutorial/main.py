import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QPoint
from overlay import OverlayApp
from detect_button import detect_button

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = OverlayApp()
    overlay.show()
    
    def update_overlay():
        top_left, bottom_right = detect_button('resources/button_image.png')
        if top_left and bottom_right:
            # Calculate the position to place the overlay next to the button
            button_position = QPoint(top_left[0] + 25, top_left[1] + 25)  # Adjust offset as needed
            overlay.updateInstruction("Click here!", button_position)
        else:
            overlay.updateInstruction("Button not found", QPoint(100, 100))  # Default position
        
    timer = QTimer()
    timer.timeout.connect(update_overlay)
    timer.start(10)  # Update every second
    
    sys.exit(app.exec_())
