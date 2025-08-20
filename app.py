import sys
import StratColumnMaker as scm

from PySide6.QtWidgets import QApplication
from enum import Enum

class ScalingMode(Enum):
    FORMATION_TOP_THICKNESS = "Formation top / thickness"
    CHRONOLOGY = "Chronology"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = scm.StratColumnMaker()

    # Connect class level signals
    window.display_options_changed.connect(window.strat_column.update_display_options)
    window.show_uncomformity_changed.connect(window.strat_column.update_uncomformity)

    # Display
    window.show()
    sys.exit(app.exec())