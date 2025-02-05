import os
import sys
from PyQt5 import uic

def convert_ui_to_py(ui_file, output_file):
    """Convert .ui file to .py file"""
    try:
        # Check if input file exists
        if not os.path.exists(ui_file):
            print(f"Error: Input file {ui_file} not found.")
            return False

        # Create output directory (if not exists)
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Use uic to convert .ui file to .py file
        with open(output_file, 'w', encoding='utf-8') as f:
            uic.compileUi(ui_file, f, from_imports=True)

        print(f"Conversion successful: {ui_file} -> {output_file}")
        return True

    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return False

def compile_resources(qrc_file, output_file):
    """Compile resource file"""
    try:
        if not os.path.exists(qrc_file):
            print(f"Error: Resource file {qrc_file} not found.")
            return False

        # Use pyrcc5 to compile resource file
        os.system(f'"{sys.executable}" -m PyQt5.pyrcc_main {qrc_file} -o {output_file}')
        print(f"Resource file compilation successful: {qrc_file} -> {output_file}")
        return True

    except Exception as e:
        print(f"Error during resource file compilation: {str(e)}")
        return False

if __name__ == "__main__":
    # Set file paths
    ui_file = "main.ui"
    py_file = "modules/ui_main.py"
    qrc_file = "resources.qrc"
    rc_file = "modules/resources_rc.py"

    # Convert UI file
    if convert_ui_to_py(ui_file, py_file):
        print("UI file conversion completed.")

        # Compile resource file
        if compile_resources(qrc_file, rc_file):
            print("Resource file compilation completed.")

            # Modify import statements
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Modify resource file import and ensure single path
            if "from . import resources_rc" in content:
                content = content.replace(
                    "from . import resources_rc",
                    "from modules import resources_rc"
                )
            else:
                content = content.replace(
                    "import resources_rc",
                    "from modules import resources_rc"
                )

            # Add SlidingStackedWidget import and usage
            content = content.replace(
                "from PyQt5 import QtCore, QtGui, QtWidgets",
                "from PyQt5 import QtCore, QtGui, QtWidgets\nfrom widgets.sliding_stacked_widgets import SlidingStackedWidget"
            )
            content = content.replace(
                "self.stackedWidget = QtWidgets.QStackedWidget(self.pagesContainer)",
                "self.stackedWidget = SlidingStackedWidget(self.pagesContainer)"
            )

            # Save modified file
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print("File modification completed.")

            # Reminder for animation settings in main program
            print("\nPlease add the following code in your main program to set up page transition animations:")
            print("self.ui.stackedWidget.setSpeed(120)  # Set animation duration to 120ms")
            print("self.ui.stackedWidget.setAnimation(QtCore.QEasingCurve.Linear)  # Set animation curve")
            print("self.ui.stackedWidget.setDirection(QtCore.Qt.Horizontal)  # Set horizontal slide direction")