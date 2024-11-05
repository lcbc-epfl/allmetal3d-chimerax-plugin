# vim: set expandtab shiftwidth=4 softtabstop=4:

# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

from chimerax.core.tools import ToolInstance


class TutorialTool(ToolInstance):

    # Inheriting from ToolInstance makes us known to the ChimeraX tool mangager,
    # so we can be notified and take appropriate action when sessions are closed,
    # saved, or restored, and we will be listed among running tools and so on.
    #
    # If cleaning up is needed on finish, override the 'delete' method
    # but be sure to call 'delete' from the superclass at the end.

    SESSION_ENDURING = False  # Does this instance persist when session closes
    SESSION_SAVE = True  # We do save/restore in sessions
    help = "help:user/tools/tutorial.html"
    # Let ChimeraX know about our help page

    def __init__(self, session, tool_name):
        # 'session'   - chimerax.core.session.Session instance
        # 'tool_name' - string

        # Initialize base class.
        super().__init__(session, tool_name)

        # Set name displayed on title bar (defaults to tool_name)
        # Must be after the superclass init, which would override it.
        self.display_name = "Tutorial — Qt-based"

        # Create the main window for our tool.  The window object will have
        # a 'ui_area' where we place the widgets composing our interface.
        # The window isn't shown until we call its 'manage' method.
        #
        # Note that by default, tool windows are only hidden rather than
        # destroyed when the user clicks the window's close button.  To change
        # this behavior, specify 'close_destroys=True' in the MainToolWindow
        # constructor.
        from chimerax.ui import MainToolWindow

        self.tool_window = MainToolWindow(self)

        # We will be adding an item to the tool's context menu, so override
        # the default MainToolWindow fill_context_menu method
        self.tool_window.fill_context_menu = self.fill_context_menu

        # Our user interface is simple enough that we could probably inline
        # the code right here, but for any kind of even moderately complex
        # interface, it is probably better to put the code in a method so
        # that this __init__ method remains readable.
        self._build_ui()

    def _build_ui(self):
        # Put our widgets in the tool window

        # We will use two editable single-line text input fields (QLineEdit)
        # with descriptive text labels to the left of them (QLabel).
        # To arrange them horizontally side by side we use QHBoxLayout.
        from PyQt5.QtWidgets import (
            QLabel,
            QLineEdit,
            QHBoxLayout,
            QVBoxLayout,
            QComboBox,
            QPushButton,
            QSpinBox,
        )

        layout = QVBoxLayout()

        # First row: Number input 1
        probability_cutoff_label = QLabel("Probability cutoff:")
        self.probability_cutoff = QSpinBox()
        self.probability_cutoff.setMinimum(1)
        self.probability_cutoff.setMaximum(7)
        layout.addWidget(probability_cutoff_label)
        layout.addWidget(self.probability_cutoff)

        # Second row: Number input 2
        clustering_threshold_label = QLabel("Clustering threshold (A):")
        self.clustering_threshold = QSpinBox()
        self.clustering_threshold.setMinimum(1)
        self.clustering_threshold.setMaximum(7)
        layout.addWidget(clustering_threshold_label)
        layout.addWidget(self.clustering_threshold)

        # Third row: Dropdown
        dropdown_mode_label = QLabel("Mode:")
        self.dropdown_mode = QComboBox()
        self.dropdown_mode.addItem("Fast")
        self.dropdown_mode.addItem("All")
        self.dropdown_mode.addItem("Around a specific residue")
        layout.addWidget(dropdown_mode_label)
        layout.addWidget(self.dropdown_mode)

        dropdown_modelstorun_label = QLabel("Models to run:")
        self.dropdown_modelstorun = QComboBox()
        self.dropdown_modelstorun.addItem("AllMetal3D + Water3D")
        self.dropdown_modelstorun.addItem("Only Water3D")
        self.dropdown_modelstorun.addItem("Only AllMetal3D")
        layout.addWidget(dropdown_modelstorun_label)
        layout.addWidget(self.dropdown_modelstorun)

        self.resid_label = QLabel("Around residue ID")
        self.resid = QLineEdit()
        layout.addWidget(self.resid_label)
        layout.addWidget(self.resid)

        # Second row: Number input 2
        self.residue_around_label = QLabel("Radius of residues to include(A):")
        self.residue_around = QSpinBox()
        self.residue_around.setMinimum(1)
        layout.addWidget(self.residue_around_label)
        layout.addWidget(self.residue_around)

        # Show this section only when dropdown_mode is set to "Around a specific residue"
        def toggle_residue_section():
            if self.dropdown_mode.currentText() == "Around a specific residue":
                self.resid_label.setVisible(True)
                self.resid.setVisible(True)
                self.residue_around_label.setVisible(True)
                self.residue_around.setVisible(True)
            else:
                self.resid_label.setVisible(False)
                self.resid.setVisible(False)
                self.residue_around_label.setVisible(False)
                self.residue_around.setVisible(False)

        self.dropdown_mode.currentIndexChanged.connect(toggle_residue_section)
        toggle_residue_section()

        # Fourth row: Run button
        self.run_button = QPushButton("Run")
        layout.addWidget(self.run_button)

        # Set the layout as the contents of our window
        self.tool_window.ui_area.setLayout(layout)

        # Show the window on the user-preferred side of the ChimeraX
        # main window
        self.tool_window.manage("side")

    def return_pressed(self):
        # The use has pressed the Return key; log the current text as HTML
        from chimerax.core.commands import run

        # ToolInstance has a 'session' attribute...
        run(self.session, "log html %s" % self.line_edit.text())

    def fill_context_menu(self, menu, x, y):
        # Add any tool-specific items to the given context menu (a QMenu instance).
        # The menu will then be automatically filled out with generic tool-related actions
        # (e.g. Hide Tool, Help, Dockable Tool, etc.)
        #
        # The x,y args are the x() and y() values of QContextMenuEvent, in the rare case
        # where the items put in the menu depends on where in the tool interface the menu
        # was raised.
        from Qt.QtGui import QAction

        clear_action = QAction("Clear", menu)
        clear_action.triggered.connect(lambda *args: self.line_edit.clear())
        menu.addAction(clear_action)

    def take_snapshot(self, session, flags):
        return {"version": 1, "current text": self.line_edit.text()}

    @classmethod
    def restore_snapshot(class_obj, session, data):
        # Instead of using a fixed string when calling the constructor below, we could
        # have saved the tool name during take_snapshot() (from self.tool_name, inherited
        # from ToolInstance) and used that saved tool name.  There are pros and cons to
        # both approaches.
        inst = class_obj(session, "AllMetal3D/Water3D")
        inst.line_edit.setText(data["current text"])
        return inst
