import os

from chimerax.core.tools import ToolInstance

from chimerax.atomic.structure import selected_residues


from Qt.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QTabWidget,
)


class AllMetal3D(ToolInstance):

    SESSION_ENDURING = False  # Does this instance persist when session closes
    SESSION_SAVE = True  # We do save/restore in sessions
    help = "help:user/tools/tutorial.html"

    def __init__(self, session, tool_name):
        # 'session'   - chimerax.core.session.Session instance
        # 'tool_name' - string

        # Initialize base class.
        super().__init__(session, tool_name)

        # Set name displayed on title bar (defaults to tool_name)
        self.display_name = "AllMetal3D/Water3D"

        self.tab_names = ["Metal", "Water"]
        self.table_metals = []
        self.table_water = []
        self.tab_widget = QTabWidget()

        self._build_dialogbox()

    def _build_dialogbox(self):
        from chimerax.ui import MainToolWindow

        self.tool_window = MainToolWindow(self)
        parent = self.tool_window.ui_area

        from Qt.QtWidgets import (
            QLabel,
            QLineEdit,
            QHBoxLayout,
            QDoubleSpinBox,
            QVBoxLayout,
            QComboBox,
            QPushButton,
            QSpinBox,
        )
        from Qt.QtCore import Qt as QtCoreQt

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        parent.setLayout(layout)

        from chimerax.atomic.widgets import AtomicStructureListWidget

        self.tool_window.title = "AllMetal3D/Water3D"

        class ShortASList(AtomicStructureListWidget):
            def sizeHint(self):
                hint = super().sizeHint()
                hint.setHeight(hint.height() // 2)
                return hint

        input_struc_label = QLabel("Input structure:")
        layout.addWidget(input_struc_label)
        self.structure_list = ShortASList(self.session)
        layout.addWidget(self.structure_list, alignment=QtCoreQt.AlignLeft)

        ressource_label = QLabel("Resources to use:")
        self.ressource = QComboBox()
        self.ressource.addItem("HuggingFace ZeroGPU")
        self.ressource.addItem("Local GPU")
        layout.addWidget(ressource_label)
        layout.addWidget(self.ressource)

        self.server_url_label = QLabel("Server URL")
        self.server_url = QLineEdit()
        layout.addWidget(self.server_url_label)
        layout.addWidget(self.server_url)

        def toggle_server_section():
            if self.ressource.currentText() == "Local GPU":
                self.server_url_label.setVisible(True)
                self.server_url.setVisible(True)
            else:
                self.server_url_label.setVisible(False)
                self.server_url.setVisible(False)

        self.ressource.currentIndexChanged.connect(toggle_server_section)
        toggle_server_section()

        probability_cutoff_label = QLabel("Probability cutoff:")
        self.probability_cutoff = QDoubleSpinBox()

        self.probability_cutoff.setValue(0.25)
        self.probability_cutoff.setSingleStep(0.05)
        self.probability_cutoff.setDecimals(2)
        self.probability_cutoff.setRange(0.0, 1.0)
        layout.addWidget(probability_cutoff_label)
        layout.addWidget(self.probability_cutoff)

        clustering_threshold_label = QLabel("Clustering threshold (A):")
        self.clustering_threshold = QSpinBox()
        self.clustering_threshold.setMinimum(1)
        self.clustering_threshold.setMaximum(7)
        self.clustering_threshold.setValue(7)
        layout.addWidget(clustering_threshold_label)
        layout.addWidget(self.clustering_threshold)

        dropdown_mode_label = QLabel("Mode:")
        self.dropdown_mode = QComboBox()
        self.dropdown_mode.addItem("fast")
        self.dropdown_mode.addItem("all")
        self.dropdown_mode.addItem("around a specific residue")
        self.dropdown_mode.addItem("current selection")
        layout.addWidget(dropdown_mode_label)
        layout.addWidget(self.dropdown_mode)

        residues = selected_residues(self.session)
        if len(residues) > 0:
            self.dropdown_mode.setCurrentText("current selection")

        self.resid_label = QLabel("Around residue ID")
        self.resid = QLineEdit()
        layout.addWidget(self.resid_label)
        layout.addWidget(self.resid)

        self.residue_around_label = QLabel("Radius of residues to include(A):")
        self.residue_around = QSpinBox()
        self.residue_around.setMinimum(1)
        layout.addWidget(self.residue_around_label)
        layout.addWidget(self.residue_around)

        def toggle_residue_section():
            if self.dropdown_mode.currentText() == "Around a specific residue":
                self.resid_label.setVisible(True)
                self.resid.setVisible(True)
                self.residue_around_label.setVisible(True)
                self.residue_around.setVisible(True)
            elif self.dropdown_mode.currentText() == "current selection":
                self.resid_label.setVisible(False)
                self.resid.setVisible(False)
                self.residue_around_label.setVisible(True)
                self.residue_around.setVisible(True)
            else:
                self.resid_label.setVisible(False)
                self.resid.setVisible(False)
                self.residue_around_label.setVisible(False)
                self.residue_around.setVisible(False)

        self.dropdown_mode.currentIndexChanged.connect(toggle_residue_section)
        toggle_residue_section()

        dropdown_modelstorun_label = QLabel("Models to run:")
        self.dropdown_modelstorun = QComboBox()
        self.dropdown_modelstorun.addItem("AllMetal3D + Water3D")
        self.dropdown_modelstorun.addItem("Only Water3D")
        self.dropdown_modelstorun.addItem("Only AllMetal3D")
        layout.addWidget(dropdown_modelstorun_label)
        layout.addWidget(self.dropdown_modelstorun)

        from Qt.QtWidgets import QDialogButtonBox as qbbox

        bbox = qbbox(qbbox.Ok | qbbox.Cancel)
        bbox.accepted.connect(self.predict)
        bbox.rejected.connect(self.delete)
        layout.addWidget(bbox)
        self.tool_window.manage(None)

    def _res_sel_cb(self, newly_selected, newly_deselected):
        self._selected_treatment(self.res_table.selected)

    def _res_sel_cb_water(self, newly_selected, newly_deselected):
        self._selected_treatment(self.water_table.selected)

    def _selected_treatment(self, selected):
        from chimerax.core.commands import run

        if len(selected) == 0:
            return
        model = selected[0][0]
        index = selected[0][1]
        run(self.session, f"select {model}/X:{index}")
        run(self.session, f"display {model}/X:{index} :<4")
        run(self.session, f"view {model}/X:{index} @<4")

    def show_tab(self, tab_name):
        index = self.tab_names.index(tab_name)
        self.tab_widget.setCurrentIndex(index)

    def _add_tab(self, tab_name):
        tab_area = QWidget()
        if tab_name == "Metal":
            self._fill_metal_tab(tab_area)
        elif tab_name == "Water":
            self._fill_water_tab(tab_area)
        else:
            raise AssertionError("Don't know how to create tab '%s'" % tab_name)
        self.tab_widget.addTab(tab_area, tab_name)

    def _fill_metal_tab(self, tab_area):
        from chimerax.ui.widgets import ItemTable

        table_layout = QHBoxLayout()
        tab_area.setLayout(table_layout)
        self.res_table = ItemTable()
        self.res_table.add_column("Model", lambda x: x[0])
        self.res_table.add_column("Index", lambda x: x[1])
        self.res_table.add_column("p(loc)", lambda x: x[2])
        self.res_table.add_column("Metal", lambda x: x[3])
        self.res_table.add_column("p(identity)", lambda x: x[4])
        self.res_table.add_column("Geometry", lambda x: x[5])
        self.res_table.add_column("p(geometry)", lambda x: x[6])
        table_layout.addWidget(self.res_table, stretch=1)
        self.res_table.data = self.table_metals
        self.res_table.selection_changed.connect(self._res_sel_cb)

        self.res_table.launch(session_info=None)

    def _fill_water_tab(self, tab_area):
        from chimerax.ui.widgets import ItemTable

        table_layout = QHBoxLayout()
        tab_area.setLayout(table_layout)
        self.water_table = ItemTable()
        self.water_table.add_column("Model", lambda x: x[0])
        self.water_table.add_column("Index", lambda x: x[1])
        self.water_table.add_column("p(loc)", lambda x: x[2])
        table_layout.addWidget(self.water_table, stretch=1)
        self.water_table.data = self.table_water
        self.water_table.selection_changed.connect(self._res_sel_cb_water)

        self.water_table.launch(session_info=None)

    def _build_loadingscreen(self):
        from chimerax.ui import MainToolWindow
        from chimerax.ui.widgets import Citation
        from Qt.QtCore import Qt as QtCoreQt
        from Qt.QtWidgets import (
            QHBoxLayout,
            QVBoxLayout,
        )
        from Qt.QtWidgets import QLabel
        from Qt.QtCore import QTimer

        self.tool_window_loading = tw = MainToolWindow(self, close_destroys=False)
        parent = tw.ui_area

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        parent.setLayout(layout)

        self.label = QLabel("Loading")
        self.label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.dots = ""
        self.max_dots = 3

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(500)

        self.tool_window_loading.fill_context_menu = self.fill_context_menu

        self.tool_window_loading.manage("side")

    def update_animation(self):
        # Update the dots for the animation
        if len(self.dots) < self.max_dots:
            self.dots += "."
        else:
            self.dots = ""
        self.label.setText(f"Loading {self.dots}")

    def _build_resultui(self):
        from Qt.QtCore import Qt as QtCoreQt

        old_models = self.session.models.list()
        old_models = [m.id[0] for m in old_models]

        print("models", old_models)
        print(self.table_metals)
        from chimerax.ui import MainToolWindow
        from chimerax.ui.widgets import Citation

        # hide loading window
        self.tool_window_loading.destroy()

        self.tool_window = tw = MainToolWindow(self, close_destroys=False)
        parent = tw.ui_area
        from Qt.QtWidgets import (
            QHBoxLayout,
            QVBoxLayout,
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        parent.setLayout(layout)

        layout.addWidget(self.tab_widget)

        # add tabs for Metal and Water
        for tab_name in self.tab_names:
            self._add_tab(tab_name)

        layout.addWidget(
            Citation(
                self.session,
                "S.L. Dürr and U. Rothlisberger.\n" "AllMetal3D.\n" "BioRxiv",
                prefix="Publications using AllMetal3D results should cite:",
                pubmed_id=0,
            ),
            alignment=QtCoreQt.AlignCenter,
        )
        self.tool_window.fill_context_menu = self.fill_context_menu

        self.tool_window.manage("side")

    def _result_callback(
        self,
        html,
        metal_probe,
        metal_cube,
        water_probe,
        water_cube,
        results_json,
        water_json,
    ):
        try:
            res = (
                html,
                metal_probe,
                metal_cube,
                water_probe,
                water_cube,
                results_json,
                water_json,
            )
            from chimerax.core.commands import run

            structures_to_load = {
                "metal_probes": {"model_spec": None, "color": None, "loaded": False},
                "metal_cube": {
                    "model_spec": None,
                    "color": "#ffffff28",
                    "loaded": False,
                },
                "water_probes": {"model_spec": None, "color": "red", "loaded": False},
                "water_cube": {
                    "model_spec": None,
                    "color": "#00aaff28",
                    "loaded": False,
                },
            }

            from chimerax.atomic import structure

            old_models = self.session.models.list()
            old_models = [
                m for m in old_models if isinstance(m, structure.AtomicStructure)
            ]
            old_models = [m.id[0] for m in old_models]
            # sort models by id
            old_models.sort()

            models = old_models

            # get next model id that is not set, model ids might have gaps
            def get_new_modelid(m_s, old_models):
                while m_s in old_models:
                    m_s = m_s + 1
                return m_s

            m_s = 1

            for j, struc in enumerate(structures_to_load.keys()):
                i = j + 1

                # check if the file is visible
                if not res[i]["visible"]:
                    continue

                if "probes" in struc:
                    self.session.ui.thread_safe(
                        run, self.session, f"open {res[i]['value']}"
                    )

                    # m_s, old_models = get_new_modelid(self, old_models)
                    # print("models", old_models)
                    m_s = get_new_modelid(m_s, models)
                    models.append(m_s)
                    structures_to_load[struc]["model_spec"] = m_s
                    structures_to_load[struc]["loaded"] = True
                    if structures_to_load[struc]["color"] is not None:
                        self.session.ui.thread_safe(
                            run,
                            self.session,
                            f"color #{m_s} {structures_to_load[struc]['color']}",
                        )
                else:
                    self.session.ui.thread_safe(
                        run, self.session, f"open {res[i]['value']}"
                    )
                    structures_to_load[struc]["loaded"] = True
                    m_s = get_new_modelid(m_s, models)
                    models.append(m_s)
                    self.session.ui.thread_safe(
                        run,
                        self.session,
                        f"color #{m_s} {structures_to_load[struc]['color']}",
                    )
                    structures_to_load[struc]["model_spec"] = m_s

            self.table_metals = []

            if structures_to_load["metal_probes"]["loaded"]:
                results_json = res[5]

                for i, res in enumerate(results_json, start=1):
                    max_prob = max(res["probabilities_identity"])
                    max_index = res["probabilities_identity"].index(max_prob)
                    max_prob_geo = max(res["probabilities_geometry"])
                    max_index_geo = res["probabilities_geometry"].index(max_prob_geo)
                    labels = ["Alkali", "MG", "CA", "ZN", "NonZNTM", "NoMetal"]
                    labels_geometry = [
                        "tetrahedron",
                        "octahedron",
                        "pentagonal bipyramid",
                        "square",
                        "irregular",
                        "other",
                        "NoMetal",
                    ]
                    self.table_metals.append(
                        (
                            f'#{structures_to_load["metal_probes"]["model_spec"]}',
                            res["index"],
                            res["location_confidence"],
                            labels[max_index],
                            max_prob,
                            labels_geometry[max_index_geo],
                            max_prob_geo,
                        )
                    )

            self.table_water = []
            if structures_to_load["water_probes"]["loaded"]:
                for i, res in enumerate(water_json, start=1):
                    self.table_water.append(
                        (
                            f'#{structures_to_load["water_probes"]["model_spec"]}',
                            i,
                            f"{res:.2f}",
                        )
                    )

            # build results ui in threadsafe mode
            self.session.ui.thread_safe(self._build_resultui)
        except ValueError as e:
            raise UserError(str(e))

    def predict(self):
        from chimerax.core.commands import run
        from chimerax.core.errors import UserError

        from gradio_client import Client

        s = self.structure_list.value
        if not len(s) > 0:
            raise UserError("No structure chosen for checking")

        if self.dropdown_mode.currentText() == "Around a specific residue":
            if not self.resid.text():
                raise UserError("No residue ID given")
            resid = self.resid.text()
            residue_around = self.residue_around.value()
        else:
            resid = ""
            residue_around = 4

        # close dialog
        self.delete()

        server_url = self.server_url.text()

        if self.ressource.currentText() == "Local GPU":
            if not server_url:
                raise UserError("No server URL given")
            server = server_url
            api_name = "/predict"
        else:
            server = "simonduerr/allmetal3d"
            api_name = "/predict_zero_gpu"

        try:
            client = Client(server)
        except:
            raise UserError("Couldn't connect to server")
        mode = self.dropdown_mode.currentText()
        if mode == "current selection":
            mode = "Around a specific residue"

            residues = selected_residues(self.session)
            if not residues:
                raise UserError("No residues selected")
            resid = [str(r.number) for r in residues]
            resid = " ".join(resid)

        try:
            result = client.submit(
                s[0].filename,
                self.dropdown_modelstorun.currentText(),
                float(self.probability_cutoff.value()),
                float(self.clustering_threshold.value()),
                50,
                str(self.dropdown_mode.currentText()),
                resid,
                float(residue_around),
                api_name=api_name,
                result_callbacks=[self._result_callback],
            )
        except ValueError as e:
            raise UserError(str(e))
        self.session.logger.status("AllMetal3D/Water3D job submitted, running")
        self._build_loadingscreen()

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
        from chimerax.atomic import Residue

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
