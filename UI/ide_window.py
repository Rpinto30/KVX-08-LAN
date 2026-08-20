"""
==============================================================================
 IDE - PyQt6 (solo interfaz grafica)
 Interfaz estilo entorno de desarrollo: barra de control superior, panel de
 registros, editor de codigo con numeracion de linea, panel de tema (en la
 cabecera del editor) y consola de mensajes.

 TEMAS incluidos (seleccionables desde la cabecera del editor):
   - MATRIX : monocromo verde fosforo sobre negro (estetica original).
   - piOS   : inspirado en la terminal "Omni-piOS" de SUPERHOT (blanco /
              cian helado sobre negro, con acentos rojos de alerta).
   - CTOS   : inspirado en el panel de control cTOS de Watch_Dogs (azul /
              cian sobre negro-azulado, paneles redondeados).

 FUNCIONES HABILITADAS:
   - Menu File: New / Open... / Save / Save As... (con QFileDialog real).
   - Menu Help: Documentation / About.
   - Panel de registros (solo visual, valores estaticos).
   - Selector de tema y ornamentacion (glow neon, scanlines CRT).

 NOTA: Este archivo contiene UNICAMENTE interfaz grafica. No incluye
 validador de sintaxis, simulador de ejecucion, breakpoints ni ninguna
 otra funcionalidad de automata; tampoco incluye la funcionalidad de
 "compilar y correr codigo" (ese boton y su logica fueron removidos).
==============================================================================
"""

import os
import sys
import time
from string import Template

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QMenu, QAbstractItemView, QSizePolicy,
    QGraphicsDropShadowEffect, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QPainter, QAction, QPixmap


from UI.code_editor import EditorPanel
from UI.ascii_table import AsciiTablePanel
from UI.process_worker import ProcessDrawer


# ==============================================================================
# SECCION: UTILIDADES DE ORNAMENTACION (glow neon)
# ==============================================================================
def aplicar_glow(widget: QWidget, color: str = "#00ff41", radio: int = 14):
    """Agrega un resplandor neon (drop shadow) a cualquier widget."""
    efecto = QGraphicsDropShadowEffect(widget)
    efecto.setBlurRadius(radio)
    efecto.setColor(QColor(color))
    efecto.setOffset(0, 0)
    widget.setGraphicsEffect(efecto)


# ==============================================================================
# SECCION: OVERLAY DE SCANLINES (efecto CRT decorativo)
# ==============================================================================
class ScanlineOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, evento):
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0, 32))
        for y in range(0, self.height(), 3):
            painter.drawLine(0, y, self.width(), y)


# ==============================================================================
# SECCION: VENTANA PRINCIPAL DEL IDE
# ==============================================================================
class IDEWindow(QMainWindow):
    REGISTROS = (
        ["pc"] + [f"r{i}" for i in range(24)] +
        ["et", "bt", "ea", "ba", "sp", "fp", "gp", "ra",
         "status", "estatus", "bstatus", "ienable", "ipending"]
    )

    SECUENCIA_ARRANQUE = [
        "SYSTEM BOOT — INICIALIZANDO NUCLEO...",
        "> Cargando banco de registros... OK",
        "> Montando editor de codigo... OK",
        "> Enlazando consola de mensajes... OK",
        "> Sistema listo.",
    ]

    # --------------------------------------------------------------------
    # PALETAS DE TEMA
    # --------------------------------------------------------------------
    PALETAS = {
        "matrix": {
            "fondo": "#000000", "fondo_panel": "#010c02",
            "primario": "#00ff41", "brillante": "#39ff14", "tenue": "#0c6b1f",
            "alerta": "#39ff14", "radio": "2px", "borde_estilo": "solid",
            "fuente": "'Consolas', 'Courier New', monospace",
        },
        "pios": {
            "fondo": "#000000", "fondo_panel": "#0a0a0a",
            "primario": "#dff7ff", "brillante": "#8fefff", "tenue": "#3a4a4d",
            "alerta": "#ff2d4b", "radio": "0px", "borde_estilo": "double",
            "fuente": "'Consolas', 'Courier New', monospace",
        },
        "ctos": {
            "fondo": "#04070c", "fondo_panel": "#081824",
            "primario": "#58d6ff", "brillante": "#00e5ff", "tenue": "#123246",
            "alerta": "#ff3b3b", "radio": "10px", "borde_estilo": "solid",
            "fuente": "'Consolas', 'Courier New', monospace",
        },"codeblocks": {
            "fondo": "#ffffff", 
            "fondo_panel": "#f0f0f0",
            "primario": "#000000", 
            "brillante": "#0066cc", 
            "tenue": "#d0d0d0",
            "alerta": "#cc0000", 
            "radio": "0px", 
            "borde_estilo": "solid",
            "fuente": "'Consolas', 'Courier New', monospace",
        },
        "macos": {
            "fondo": "#1e1e1e", 
            "fondo_panel": "#282828",
            "primario": "#f5f5f7", 
            "brillante": "#0a84ff", 
            "tenue": "#424244",
            "alerta": "#ff453a", 
            "radio": "8px", 
            "borde_estilo": "solid",
            "fuente": "'-apple-system', 'SF Pro Text', 'Menlo', monospace",
        }
    }

    VERSIONES = {
        "matrix": "Omni-nOS-v3.13.37",
        "pios": "Omni-piOS-v2.1.01p",
        "ctos": "cTOS Server v3.26",
        "codeblocks": "Code::Blocks v20.03",
        "macos": "macOS Sequoia v15.0"
    }

    request_stop = pyqtSignal()
    request_gen_all_diagrams = pyqtSignal()
    request_gen_diagrams = pyqtSignal()
    request_on_draw = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE")
        self.resize(1520, 860)

        # ---- Estado interno (debe existir antes de construir la UI) ----
        self.ruta_archivo_actual: str | None = None
        self._modificado = False
        self.tema_actual = "ctos"
        self._paleta_actual = self.PALETAS["ctos"]

        self._setup_ui()
        self._aplicar_tema("ctos")
        self._configurar_ornamentos()
        self._reproducir_secuencia_arranque()
        
        self.thread = QThread()
        self.worker = ProcessDrawer()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start_process)
        self.worker.on_draw.connect(self.request_on_draw)
        #self.request_gen_all_diagrams.connect(self.worker.generate)
        self.request_stop.connect(self.worker.stop_process)
        
        def message_log_drawer(mensaje: str):
            self._console_log(mensaje)
        
        self.worker.on_draw.connect(message_log_drawer)

        self.thread.start()

    # --------------------------------------------------------------------
    # setupUI general: arma la ventana en bloques (barra de control, area
    # principal con splitter, consola de mensajes, pie de pagina)
    # --------------------------------------------------------------------
    def _setup_ui(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_raiz = QVBoxLayout(widget_central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        layout_raiz.addWidget(self._setup_barra_control())

        splitter_principal = QSplitter(Qt.Orientation.Vertical)
        splitter_principal.setObjectName("splitterPrincipal")

        splitter_horizontal = QSplitter(Qt.Orientation.Horizontal)
        splitter_horizontal.setObjectName("splitterHorizontal")
        splitter_horizontal.addWidget(self._setup_panel_izquierdo())
        splitter_horizontal.addWidget(self._setup_panel_editor())
        splitter_horizontal.setSizes([380, 1140])

        splitter_principal.addWidget(splitter_horizontal)
        splitter_principal.addWidget(self._setup_panel_mensajes())
        splitter_principal.setSizes([640, 190])

        layout_raiz.addWidget(splitter_principal)
        layout_raiz.addWidget(self._setup_pie_pagina())

        # ---- Overlay decorativo de scanlines (efecto CRT), sobre todo ----
        self.overlay_scanlines = ScanlineOverlay(widget_central)
        self.overlay_scanlines.setGeometry(widget_central.rect())
        self.overlay_scanlines.raise_()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        if hasattr(self, "overlay_scanlines"):
            self.overlay_scanlines.setGeometry(self.centralWidget().rect())

    # --------------------------------------------------------------------
    # SECCION: Barra de control superior (indicador de estado, File, Help)
    # --------------------------------------------------------------------
    def _setup_barra_control(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("barraControl")
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self.label_online = QLabel("● ONLINE")
        self.label_online.setObjectName("labelOnline")
        layout.addWidget(self.label_online)

        layout.addStretch()

        layout.addWidget(self._crear_menu_boton("File", [
            ("New", self._on_nuevo_archivo),
            ("Open...", self._on_abrir_archivo),
            ("Save", self._on_guardar_archivo),
            ("Save As...", self._on_guardar_como),
        ]))
        layout.addWidget(self._crear_menu_boton("Help", [
            ("Documentation", self._on_ayuda_documentacion),
            ("About", self._on_ayuda_about),
        ]))

        return barra

    def _crear_menu_boton(self, titulo: str, opciones: list[tuple[str, callable]]) -> QPushButton:
        boton = QPushButton(f"{titulo}  ▾")
        boton.setObjectName("botonMenu")
        menu = QMenu(boton)
        menu.setObjectName("menuDesplegable")
        for nombre, callback in opciones:
            accion = QAction(nombre, self)
            if callback:
                accion.triggered.connect(callback)
            menu.addAction(accion)
        boton.setMenu(menu)
        return boton

    def _separador_vertical(self) -> QFrame:
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.VLine)
        linea.setObjectName("separadorVertical")
        return linea

    # --------------------------------------------------------------------
    # SECCION: Panel izquierdo -> pestanas (unicamente "Registers")
    # --------------------------------------------------------------------
    def _setup_panel_izquierdo(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_seccion("REGISTERS"))

        tabs = QTabWidget()
        tabs.setObjectName("tabsIzquierda")
        tabs.addTab(AsciiTablePanel(), "ASCII")
        #tabs.addTab(self._setup_tabla_registros(), "Registers")
        
        layout.addWidget(tabs)

        return panel

    #tabla jorge
    def _setup_tabla_registros(self) -> QTableWidget:
        tabla = QTableWidget(len(self.REGISTROS), 2)
        tabla.setObjectName("tablaRegistros")
        tabla.setHorizontalHeaderLabels(["Registro", "Valor"])
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla.setShowGrid(False)

        self._indice_registros: dict[str, int] = {}
        for fila, nombre in enumerate(self.REGISTROS):
            item_nombre = QTableWidgetItem(nombre)
            item_valor = QTableWidgetItem("00000000")
            item_nombre.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_valor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla.setItem(fila, 0, item_nombre)
            tabla.setItem(fila, 1, item_valor)
            self._indice_registros[nombre] = fila

        self.tabla_registros = tabla
        return tabla

    def _titulo_seccion(self, texto: str) -> QLabel:
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("tituloSeccion")
        return etiqueta

    # --------------------------------------------------------------------
    # SECCION: Panel derecho -> code_editor.py
    # --------------------------------------------------------------------
    def _setup_panel_editor(self) -> QWidget:
        self.panel_editor = EditorPanel()
        self.panel_editor.tema_cambiado.connect(self._on_cambiar_tema)
        self.panel_editor.contenido_modificado.connect(self._marcar_modificado)

        # Alias de conveniencia hacia el CodeEditor interno.
        self.editor = self.panel_editor.editor

        self._refrescar_label_archivo()
        return self.panel_editor

    # --------------------------------------------------------------------
    # SECCION: Consola de mensajes inferior (no editable) con boton Clear
    # --------------------------------------------------------------------
    def _setup_panel_mensajes(self) -> QWidget:
        # Panel principal contenedor
        panel_contenedor = QWidget()
        layout_principal = QHBoxLayout(panel_contenedor)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # 1. Widget de la Consola (Log)
        widget_consola = self._crear_subpanel_consola()
        layout_principal.addWidget(widget_consola)

        # 2. Nuevo Panel a la derecha
        nuevo_panel = self._crear_panel_graficos()
        layout_principal.addWidget(nuevo_panel)

        # Opcional: Ajustar proporciones de tamaño (ej. 1:1 o 2:1)
        layout_principal.setStretch(0, 1) 
        layout_principal.setStretch(1, 1)

        return panel_contenedor

    def _crear_subpanel_consola(self) -> QWidget:
        panel_consola = QWidget()
        layout = QVBoxLayout(panel_consola)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera
        cabecera = QWidget()
        cabecera.setObjectName("cabeceraMensajes")
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(10, 4, 10, 4)
        layout_cabecera.addWidget(self._titulo_seccion("KVX-LOG"))
        layout_cabecera.addStretch()

        boton_clear = QPushButton("Clear")
        boton_clear.setObjectName("botonClear")
        boton_clear.clicked.connect(self.limpiar_mensajes)
        layout_cabecera.addWidget(boton_clear)

        layout.addWidget(cabecera)

        # QPlainTextEdit / Consola
        from PyQt6.QtWidgets import QPlainTextEdit
        self.consola_mensajes = QPlainTextEdit()
        self.consola_mensajes.setObjectName("consolaMensajes")
        self.consola_mensajes.setReadOnly(True)
        layout.addWidget(self.consola_mensajes)

        return panel_consola

    def _crear_panel_graficos(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera
        cabecera = QWidget()
        cabecera.setObjectName("cabeceraGraficos")
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(10, 4, 10, 4)
        layout_cabecera.addWidget(self._titulo_seccion("KVX-STATES"))
        layout_cabecera.addStretch()

        layout.addWidget(cabecera)

        self.panel_img = QWidget()
        self.panel_img.setObjectName("nuevoPanelDerecho")
        layout_principal = QHBoxLayout(self.panel_img)
        layout_principal.setContentsMargins(5, 5, 5, 5)
        layout_principal.setSpacing(10)

        # --- 1. COLUMNA IZQUIERDA: LISTA DE 7 BOTONES ---
        layout_botones = QVBoxLayout()
        layout_botones.setSpacing(4)

        self.label_imagen = QLabel()
        self.label_imagen.setObjectName("visorImagen")
        self.label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.label_imagen.setScaledContents(True) 
        #self.label_imagen.setSizePolicy(
        #    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        def load_diagra(i):
            print(i)
            img = {
                1:"./Automate/result/diagramas/assing_variables.png",
                2:"./Automate/result/diagramas/comments.png",
                3:"./Automate/result/diagramas/conditions.png",
                4:"./Automate/result/diagramas/loops.png",
                5:"./Automate/result/diagramas/string_conditions.png",
                6:"./Automate/result/diagramas/strings.png",
                7:"./Automate/result/diagramas/variables.png"
            }

            if os.path.exists(img[i]):
                pixmap = QPixmap(img[i])  
                self.label_imagen.setFixedSize(650, 300) 
                pixmap = pixmap.scaled(
                    self.label_imagen.size(),                    
                    Qt.AspectRatioMode.KeepAspectRatio,             
                    Qt.TransformationMode.SmoothTransformation      
                )
                self.label_imagen.setPixmap(pixmap)
                self.label_imagen.setScaledContents(True)

        self.botones_panel = []  # Referencia para conectar eventos externamente
        for i in range(1, 8):
            btn = QPushButton(f"BOTON {i}")
            btn.setObjectName(f"btnImagen_{i}")
            # Conectar acción enviando el índice del botón
            btn.clicked.connect(
                lambda checked, idx=i: load_diagra(idx)
            )
            layout_botones.addWidget(btn)
            self.botones_panel.append(btn)

        layout_botones.addStretch()  # Empuja los botones hacia arriba
        layout_principal.addLayout(layout_botones)

        # --- 2. COLUMNA DERECHA: VISOR DE IMAGEN ---
        self.label_imagen.setText("CARGANDO IMAGENES...")
        layout_principal.addWidget(self.label_imagen)

        # Asignar proporciones de espacio entre la columna de botones y la imagen
        layout_principal.setStretch(0, 1)  # Columna botones
        layout_principal.setStretch(1, 3)  # Espacio imagen
        #here
        layout.addWidget(self.panel_img)

        return panel
    
    # --------------------------------------------------------------------
    # SECCION: Pie de pagina decorativo (prompt + version del "sistema")
    # --------------------------------------------------------------------
    def _setup_pie_pagina(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("piePagina")
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(10, 3, 10, 3)

        self.label_prompt = QLabel("C:\\>")
        self.label_prompt.setObjectName("labelPrompt")
        layout.addWidget(self.label_prompt)
        layout.addStretch()

        self.label_version = QLabel()
        self.label_version.setObjectName("labelVersion")
        layout.addWidget(self.label_version)

        return barra

    # --------------------------------------------------------------------
    # API publica de la consola de mensajes
    # --------------------------------------------------------------------
    def agregar_mensaje(self, texto: str):
        self.consola_mensajes.appendPlainText(texto)

    def limpiar_mensajes(self):
        self.consola_mensajes.clear()

    # --------------------------------------------------------------------
    # Archivo: seguimiento de nombre / estado modificado
    # --------------------------------------------------------------------
    def _marcar_modificado(self):
        self._modificado = True
        self._refrescar_label_archivo()

    def _refrescar_label_archivo(self):
        nombre = os.path.basename(self.ruta_archivo_actual) if self.ruta_archivo_actual else "untitled.s"
        sufijo = "  [changed since save]" if self._modificado else ""
        self.panel_editor.label_archivo.setText(nombre + sufijo)

    # --------------------------------------------------------------------
    # FUNCIONES: menu File
    # --------------------------------------------------------------------
    def _on_nuevo_archivo(self):
        self.editor.setPlainText("")
        self.ruta_archivo_actual = None
        self._modificado = False
        self._refrescar_label_archivo()
        self.agregar_mensaje("> Nuevo archivo creado.")

    def _on_abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "", "Ensamblador (*.s *.asm);;Todos los archivos (*)"
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except OSError as error:
            self.agregar_mensaje(f"> Error al abrir archivo: {error}")
            return
        self.editor.setPlainText(contenido)
        self.ruta_archivo_actual = ruta
        self._modificado = False
        self._refrescar_label_archivo()
        self.agregar_mensaje(f"> Archivo cargado: {ruta}")

    def _on_guardar_archivo(self):
        if not self.ruta_archivo_actual:
            self._on_guardar_como()
            return
        self._guardar_en_ruta(self.ruta_archivo_actual)

    def _on_guardar_como(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "untitled.s", "Ensamblador (*.s);;Todos los archivos (*)"
        )
        if not ruta:
            return
        self.ruta_archivo_actual = ruta
        self._guardar_en_ruta(ruta)

    def _guardar_en_ruta(self, ruta: str):
        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(self.editor.toPlainText())
        except OSError as error:
            self.agregar_mensaje(f"> Error al guardar: {error}")
            return
        self._modificado = False
        self._refrescar_label_archivo()
        self.agregar_mensaje(f"> Archivo guardado: {ruta}")

    def _on_ayuda_documentacion(self):
        QMessageBox.information(
            self, "Documentation",
            "Escribe tu codigo en el editor.\n\n"
            "Usa el menu File para crear, abrir y guardar archivos.\n"
            "El tema visual se cambia desde el selector 'Theme' en la "
            "cabecera del editor."
        )

    def _on_ayuda_about(self):
        QMessageBox.information(
            self, "About",
            f"IDE\nTema actual: {self.tema_actual.upper()}\n\n"
            "Interfaz construida con PyQt6."
        )

    # --------------------------------------------------------------------
    # ORNAMENTACION: glow neon + parpadeo del indicador ONLINE +
    # reproduccion animada de la secuencia de arranque
    # --------------------------------------------------------------------
    def _configurar_ornamentos(self):
        self._brillo_online = True
        self.timer_parpadeo = QTimer(self)
        self.timer_parpadeo.timeout.connect(self._alternar_parpadeo_online)
        self.timer_parpadeo.start(650)

    def _alternar_parpadeo_online(self):
        self._brillo_online = not self._brillo_online
        paleta = self._paleta_actual
        color = paleta["brillante"] if self._brillo_online else paleta["tenue"]
        self.label_online.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _reproducir_secuencia_arranque(self):
        for indice, linea in enumerate(self.SECUENCIA_ARRANQUE):
            QTimer.singleShot(180 * indice, lambda texto=linea: self.agregar_mensaje(texto))

    def _console_log(self, message):
        QTimer.singleShot(180, lambda : self.agregar_mensaje(message))
        

    def _aplicar_glows_tema(self, paleta: dict):
        aplicar_glow(self.label_online, color=paleta["primario"], radio=18)
        aplicar_glow(self.label_version, color=paleta["primario"], radio=8)
        for etiqueta in self.findChildren(QLabel, "tituloSeccion"):
            aplicar_glow(etiqueta, color=paleta["primario"], radio=10)

    # --------------------------------------------------------------------
    # TEMA: callback que llega desde la senal tema_cambiado del EditorPanel
    # --------------------------------------------------------------------
    def _on_cambiar_tema(self, clave: str):
        self._aplicar_tema(clave)
        self.agregar_mensaje(f"> Tema visual cambiado a '{clave.upper()}'.")

    # --------------------------------------------------------------------
    # Aplica un tema completo: hoja de estilos + colores dinamicos del
    # editor + glow + version en el pie + sincroniza el combobox
    # --------------------------------------------------------------------
    def _aplicar_tema(self, clave: str):
        paleta = self.PALETAS[clave]
        self.tema_actual = clave
        self._paleta_actual = paleta

        self.setStyleSheet(Template(self._PLANTILLA_QSS).substitute(paleta))

        self.editor.color_normal = QColor(paleta["tenue"])
        color_linea_actual = QColor(paleta["primario"])
        color_linea_actual.setAlpha(28)
        self.editor.color_linea_actual = color_linea_actual
        self.editor.highlight_current_line()
        self.editor.line_number_area.update()

        #fila_pc = self._indice_registros.get("pc")
        #if fila_pc is not None:
        #    color_fondo = QColor(paleta["brillante"])
        #    color_texto = QColor(paleta["fondo"])
        #    for columna in (0, 1):
        #        item = self.tabla_registros.item(fila_pc, columna)
        #        if item:
        #            item.setBackground(color_fondo)
        #            item.setForeground(color_texto)

        self._aplicar_glows_tema(paleta)
        self.label_version.setText(self.VERSIONES.get(clave, ""))
        self.panel_editor.set_tema_actual(clave)

    def closeEvent(self, event):
        self.request_stop.emit()
        self.thread.quit()
        self.thread.wait()
        event.accept()
        

    # --------------------------------------------------------------------
    # PLANTILLA DE ESTILOS (usa $placeholders sustituidos con la paleta
    # activa mediante string.Template, para no chocar con las llaves { }
    # propias de la sintaxis QSS)
    # --------------------------------------------------------------------
    _PLANTILLA_QSS = """
        * { font-family: $fuente; }

        QMainWindow, QWidget {
            background-color: $fondo;
            color: $primario;
        }

        /* ---------------- Barra de control superior ---------------- */
        QWidget#barraControl {
            background-color: $fondo_panel;
            border-bottom: 2px $borde_estilo $primario;
        }
        QLabel#labelOnline { color: $brillante; font-weight: bold; padding: 6px 8px; }
        QLabel#labelPrompt { color: $tenue; font-weight: bold; }
        QLabel#labelVersion { color: $tenue; font-style: italic; font-size: 11px; }
        QFrame#separadorVertical { color: $tenue; }

        QPushButton#botonMenu {
            background-color: $fondo; color: $primario;
            border: 1px solid $tenue; padding: 6px 12px; border-radius: $radio;
        }
        QPushButton#botonMenu:hover { border: 1px solid $brillante; color: $brillante; }

        QMenu#menuDesplegable { background-color: $fondo_panel; color: $primario; border: 1px solid $primario; }
        QMenu#menuDesplegable::item:selected { background-color: $primario; color: $fondo; }

        /* ---------------- Titulos de seccion (barras) --------------- */
        QLabel#tituloSeccion {
            background-color: $fondo_panel; color: $primario;
            font-weight: bold; letter-spacing: 2px; font-size: 12px;
            padding: 6px 10px; border-top: 1px solid $tenue;
            border-bottom: 2px $borde_estilo $primario;
        }

        /* ---------------- Splitters ---------------------------------- */
        QSplitter::handle { background-color: $tenue; }
        QSplitter::handle:hover { background-color: $brillante; }

        /* ---------------- Tabla de registros -------------------------- */
        QTableWidget#tablaRegistros {
            background-color: $fondo; color: $primario;
            gridline-color: $tenue; border: none; selection-background-color: transparent;
        }
        QTableWidget#tablaRegistros::item { padding: 2px 6px; }
        QHeaderView::section {
            background-color: $fondo_panel; color: $brillante;
            border: none; border-bottom: 1px solid $primario; padding: 4px; font-weight: bold;
        }

        /* ---------------- Pestanas (QTabWidget) ------------------------ */
        QTabWidget::pane { border: 2px $borde_estilo $tenue; background-color: $fondo; border-radius: $radio; }
        QTabBar::tab { background-color: $fondo_panel; color: $tenue; padding: 6px 12px; border: 1px solid $tenue; }
        QTabBar::tab:selected { background-color: $primario; color: $fondo; font-weight: bold; }
        QTabBar::tab:hover:!selected { color: $brillante; }

        /* ---------------- Editor de codigo ------------------------------ */
        QPlainTextEdit#editorCodigo {
            background-color: $fondo; color: $primario; border: none;
            selection-background-color: $primario; selection-color: $fondo; padding: 6px;
        }

        QWidget#filaCabeceraEditor { background-color: $fondo_panel; border-bottom: 1px solid $tenue; }

        QLabel#labelArchivo { color: $tenue; font-style: italic; padding-left: 12px; }

        /* ---------------- Consola de mensajes ---------------------------- */
        QWidget#cabeceraMensajes { background-color: $fondo_panel; border-top: 2px $borde_estilo $primario; }
        QPlainTextEdit#consolaMensajes { background-color: $fondo; color: $primario; border: none; padding: 6px 10px; font-size: 12px; }
        QPushButton#botonClear { background-color: $fondo; color: $primario; border: 1px solid $tenue; padding: 3px 14px; border-radius: $radio; }
        QPushButton#botonClear:hover { background-color: $primario; color: $fondo; }

        /* ---------------- Pie de pagina ------------------------------------ */
        QWidget#piePagina { background-color: $fondo_panel; border-top: 1px solid $tenue; }

        /* ---------------- Combos --------------------------------------- */
        QComboBox {
            background-color: $fondo; color: $primario; border: 1px solid $tenue;
            padding: 3px 6px; border-radius: $radio;
        }
        QComboBox:hover { border: 1px solid $brillante; }
        QComboBox QAbstractItemView { background-color: $fondo_panel; color: $primario; selection-background-color: $primario; selection-color: $fondo; }

        /* ---------------- Scrollbars ------------------------------------- */
        QScrollBar:vertical, QScrollBar:horizontal { background: $fondo_panel; width: 10px; height: 10px; }
        QScrollBar::handle { background: $tenue; border-radius: 5px; min-height: 20px; }
        QScrollBar::handle:hover { background: $brillante; }
        
        /* ---------------- Panel de Imagenes y Botones Laterales ---------------- */
        QWidget#nuevoPanelDerecho {
            background-color: $fondo;
            border-top: 2px $borde_estilo $primario;
            border-left: 1px solid $tenue;
        }
        
        /* Visor de imagen */
        QLabel#visorImagen {
            background-color: $fondo_panel;
            border: 1px solid $tenue;
            border-radius: $radio;
        }
        
        /* Botones laterales (Botón 1 al 7) */
        QPushButton[objectName^="btnImagen_"] {
            background-color: $fondo_panel;
            color: $primario;
            border: 1px solid $tenue;
            border-radius: $radio;
            padding: 8px 10px;
            font-size: 11px;
            font-weight: bold;
        }
        
        /* Efecto Hover para botones laterales */
        QPushButton[objectName^="btnImagen_"]:hover {
            background-color: $primario; 
            color: $fondo;
            border: 1px solid $brillante;
        }
        
        /* Efecto presionado */
        QPushButton[objectName^="btnImagen_"]:pressed {
            background-color: $brillante;
            color: $fondo;
            border: 1px solid $fondo;
        }
    """


