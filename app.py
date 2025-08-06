import sys
import StratColumnMaker as scm

from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = scm.StratColumnMaker()

    # Connect class level signals
    window.display_options_changed.connect(window.strat_column.update_display_options)

    # Display
    window.show()
    sys.exit(app.exec())