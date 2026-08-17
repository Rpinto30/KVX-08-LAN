import sys
import time
from PyQt6.QtWidgets import QApplication

from UI.ide_window import IDEWindow


def main():
    app = QApplication(sys.argv)
    ventana = IDEWindow()
    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
