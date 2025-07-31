import sys
import StratColumnMaker as scm

from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = scm.StratColumnMaker()
    window.show()
    sys.exit(app.exec())