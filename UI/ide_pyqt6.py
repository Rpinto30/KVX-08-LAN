"""
==============================================================================
 IDE / DEBUGGER - PyQt6
 Interfaz completa estilo entorno de depuracion (barra de control, panel de
 registros con pestanas, editor de codigo con numeracion de linea y
 breakpoints, panel de ajustes con selector de tema, y consola de mensajes.

 TEMAS incluidos (seleccionables desde Settings):
   - MATRIX : monocromo verde fosforo sobre negro (estetica original).
   - piOS   : inspirado en la terminal "Omni-piOS" de SUPERHOT (blanco /
              cian helado sobre negro, con acentos rojos de alerta).
   - CTOS   : inspirado en el panel de control cTOS de Watch_Dogs (azul /
              cian sobre negro-azulado, paneles redondeados).

 FUNCIONES BASICAS HABILITADAS:
   - Menu File: New / Open... / Save / Save As... (con QFileDialog real).
   - Menu Help: Documentation / About.
   - Breakpoints: clic en el numero de linea del editor para alternarlos;
     se listan en la pestana "Breakpoints".
   - Simulador de ejecucion muy basico (Step Into/Over/Out, Continue,
     Stop, Restart, Reload) que avanza linea por linea sobre el codigo
     ya compilado, respeta breakpoints y actualiza algunos registros
     (movi / add) a modo de demostracion.
   - Compile and Load valida sintaxis, congela un "snapshot" del codigo
     y prepara la simulacion.

 NOTA: El validador de sintaxis y el simulador de instrucciones son
 IMPLEMENTACIONES BASICAS DE DEMOSTRACION. Los bloques marcados como
 "INTEGRACION AUTOMATA / JSON" quedan comentados y listos para conectar
 el automata real que se implementara por separado.
==============================================================================
"""

import os
import re
import sys
from string import Template

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPlainTextEdit, QLabel, QFrame, QTextEdit, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QSplitter, QMenu, QAbstractItemView, QGraphicsDropShadowEffect,
    QCheckBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QRect, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QTextCharFormat, QTextCursor, QAction
)


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
# SECCION: GUTTER DE NUMEROS DE LINEA
# Ademas de numerar, permite alternar breakpoints con un clic y dibuja el
# marcador de "linea actual de ejecucion" (pc) del simulador.
# ==============================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.code_editor = editor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, evento):
        self.code_editor.line_number_area_paint_event(evento)

    def mousePressEvent(self, evento):
        self.code_editor.gutter_mouse_press(evento)


# ==============================================================================
# SECCION: EDITOR DE CODIGO
# QPlainTextEdit extendido con: gutter numerado + breakpoints, resaltado
# del renglon actual, subrayado de errores de sintaxis EN TIEMPO REAL y la
# API publica que usaran tanto el simulador como el futuro automata.
# ==============================================================================
class CodeEditor(QPlainTextEdit):
    errores_cambiaron = pyqtSignal(dict)     # {linea: mensaje}
    breakpoints_cambiaron = pyqtSignal(set)  # {lineas}

    # --------------------------------------------------------------------
    # Validador BASICO temporal (ensamblador tipo Nios II). Sera sustituido
    # / complementado por el automata definido en JSON (ver mas abajo).
    # --------------------------------------------------------------------
    INSTRUCCIONES_VALIDAS = {
        "add", "sub", "mul", "div", "and", "or", "xor", "nor",
        "addi", "subi", "andi", "ori", "xori",
        "ldw", "stw", "ldb", "stb", "ldh", "sth",
        "beq", "bne", "blt", "bge", "bltu", "bgeu", "br",
        "call", "callr", "ret", "jmp", "jmpi",
        "mov", "movi", "movhi", "movia",
        "nop", "cmpeq", "cmpne", "cmplt", "cmpge",
        "sll", "srl", "sra", "trap", "break", "sync",
    }
    DIRECTIVAS_VALIDAS = {
        ".global", ".text", ".data", ".word", ".byte", ".half",
        ".ascii", ".asciiz", ".align", ".equ", ".section", ".skip", ".space",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorCodigo")

        self.lineas_con_error: dict[int, str] = {}
        self.lineas_breakpoint: set[int] = set()
        self.linea_pc: int | None = None

        # Colores dinamicos (los actualiza IDEWindow segun el tema activo)
        self.color_normal = QColor("#0c6b1f")
        self.color_error = QColor("#39ff14")
        self.color_breakpoint = QColor("#39ff14")
        self.color_pc = QColor("#39ff14")
        self.color_linea_actual = QColor("#062b0a")

        self.line_number_area = LineNumberArea(self)

        fuente = QFont("Consolas", 11)
        fuente.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(fuente)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # ---- Analisis de sintaxis EN TIEMPO REAL (con pequeno "debounce") ----
        self.timer_analisis = QTimer(self)
        self.timer_analisis.setSingleShot(True)
        self.timer_analisis.timeout.connect(self.analizar_sintaxis_basico)
        self.textChanged.connect(lambda: self.timer_analisis.start(250))

        # ==================================================================
        # INTEGRACION AUTOMATA / JSON (pendiente de implementar por separado)
        # ------------------------------------------------------------------
        # Cuando el automata este listo, este validador basico puede
        # reemplazarse (o combinarse) reconectando la señal, por ejemplo:
        #
        # self.timer_analisis.timeout.disconnect()
        # self.timer_analisis.timeout.connect(self.analizar_sintaxis_automata)
        # ==================================================================

    # --------------------------------------------------------------------
    # Ancho dinamico del gutter (numero + espacio para iconos de
    # breakpoint / flecha de linea actual)
    # --------------------------------------------------------------------
    def line_number_area_width(self) -> int:
        digitos = len(str(max(1, self.blockCount())))
        espacio = 30 + self.fontMetrics().horizontalAdvance("9") * digitos
        return espacio

    def update_line_number_area_width(self, _bloques_nuevos):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    # --------------------------------------------------------------------
    # Dibuja numeros de renglon, marcador de breakpoint (circulo) y flecha
    # de linea actual de ejecucion ("▶", usada por el simulador basico)
    # --------------------------------------------------------------------
    def line_number_area_paint_event(self, evento):
        painter = QPainter(self.line_number_area)
        painter.fillRect(evento.rect(), QColor("#000000"))

        bloque = self.firstVisibleBlock()
        numero_bloque = bloque.blockNumber()
        top = round(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())
        alto = round(self.blockBoundingRect(bloque).height())

        while bloque.isValid() and top <= evento.rect().bottom():
            if bloque.isVisible() and top >= evento.rect().top():
                numero_linea = numero_bloque + 1
                texto = str(numero_linea)

                painter.setPen(self.color_error if numero_linea in self.lineas_con_error else self.color_normal)
                painter.drawText(
                    0, top, self.line_number_area.width() - 6, alto,
                    Qt.AlignmentFlag.AlignRight, texto
                )

                if numero_linea in self.lineas_breakpoint:
                    painter.setBrush(self.color_breakpoint)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(4, top + (alto - 9) // 2, 9, 9)

                if numero_linea == self.linea_pc:
                    painter.setPen(self.color_pc)
                    painter.drawText(16, top, 14, alto, Qt.AlignmentFlag.AlignLeft, "▶")

            bloque = bloque.next()
            top += alto
            numero_bloque += 1

    # --------------------------------------------------------------------
    # Alterna un breakpoint al hacer clic sobre el gutter
    # --------------------------------------------------------------------
    def gutter_mouse_press(self, evento):
        y_clic = evento.position().y()
        bloque = self.firstVisibleBlock()
        numero_bloque = bloque.blockNumber()
        top = round(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())
        alto = round(self.blockBoundingRect(bloque).height())

        while bloque.isValid():
            if top <= y_clic <= top + alto:
                self.alternar_breakpoint(numero_bloque + 1)
                break
            bloque = bloque.next()
            top += alto
            numero_bloque += 1

    def alternar_breakpoint(self, numero_linea: int):
        if numero_linea in self.lineas_breakpoint:
            self.lineas_breakpoint.discard(numero_linea)
        else:
            self.lineas_breakpoint.add(numero_linea)
        self.line_number_area.update()
        self.breakpoints_cambiaron.emit(set(self.lineas_breakpoint))

    # --------------------------------------------------------------------
    # Marca la linea "actual" del simulador (dibuja la flecha y centra
    # el cursor en ella). None = sin ejecucion activa.
    # --------------------------------------------------------------------
    def marcar_linea_pc(self, numero_linea: int | None):
        self.linea_pc = numero_linea
        if numero_linea is not None:
            bloque = self.document().findBlockByNumber(numero_linea - 1)
            if bloque.isValid():
                self.setTextCursor(QTextCursor(bloque))
                self.centerCursor()
        self.line_number_area.update()

    # --------------------------------------------------------------------
    # Resalta el renglon donde esta el cursor y subraya (ondulado) las
    # lineas marcadas con error, en una sola operacion de extra selections.
    # --------------------------------------------------------------------
    def highlight_current_line(self):
        selecciones = []

        if not self.isReadOnly():
            seleccion = QTextEdit.ExtraSelection()
            seleccion.format.setBackground(self.color_linea_actual)
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            seleccion.cursor = self.textCursor()
            seleccion.cursor.clearSelection()
            selecciones.append(seleccion)

        selecciones.extend(self._selecciones_de_error())
        self.setExtraSelections(selecciones)

    def _selecciones_de_error(self):
        selecciones = []
        formato_error = QTextCharFormat()
        formato_error.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        formato_error.setUnderlineColor(self.color_error)
        formato_error.setFontWeight(QFont.Weight.Bold)

        for numero_linea in self.lineas_con_error:
            bloque = self.document().findBlockByNumber(numero_linea - 1)
            if not bloque.isValid():
                continue
            cursor = QTextCursor(bloque)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            seleccion = QTextEdit.ExtraSelection()
            seleccion.format = formato_error
            seleccion.cursor = cursor
            selecciones.append(seleccion)

        return selecciones

    # --------------------------------------------------------------------
    # API publica para marcar / limpiar errores manualmente (la usara
    # tambien el futuro automata externo)
    # --------------------------------------------------------------------
    def marcar_error(self, numero_linea: int, mensaje: str):
        self.lineas_con_error[numero_linea] = mensaje
        self.highlight_current_line()
        self.line_number_area.update()
        self.errores_cambiaron.emit(self.lineas_con_error)

    def limpiar_errores(self):
        self.lineas_con_error.clear()
        self.highlight_current_line()
        self.line_number_area.update()
        self.errores_cambiaron.emit(self.lineas_con_error)

    # --------------------------------------------------------------------
    # VALIDADOR BASICO EN TIEMPO REAL
    # --------------------------------------------------------------------
    def analizar_sintaxis_basico(self):
        pass

# ==============================================================================
# SECCION: BOTON DE BARRA DE HERRAMIENTAS (dos lineas: accion + atajo)
# ==============================================================================
def crear_boton_toolbar(titulo: str, atajo: str, callback=None) -> QPushButton:
    boton = QPushButton(f"{titulo}\n{atajo}")
    boton.setObjectName("botonToolbar")
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:
        boton.clicked.connect(callback)
    return boton


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
        "> Validador de sintaxis basico activo (temporal).",
        "> Esperando conexion del automata (JSON)...",
        "> Sistema listo.",
    ]

    # --------------------------------------------------------------------
    # PALETAS DE TEMA
    # fondo/fondo_panel: fondos principal y de barras/cabeceras
    # primario/brillante/tenue: texto y bordes (normal / hover-activo / apagado)
    # alerta: color de error / breakpoint / badges negativos
    # radio: radio de borde de paneles redondeados
    # borde_estilo: "solid" o "double" para bordes decorativos
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
        },
    }

    VERSIONES = {
        "matrix": "Omni-nOS-v3.13.37",
        "pios": "Omni-piOS-v2.1.01p",
        "ctos": "cTOS Server v3.26",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE - Debugger")
        self.resize(1520, 860)

        # ---- Estado interno (debe existir antes de construir la UI) ----
        self.ruta_archivo_actual: str | None = None
        self._modificado = False
        self.snapshot_codigo: str | None = None
        self.linea_actual_ejecucion = 0
        self.tema_actual = "ctos"
        self._paleta_actual = self.PALETAS["ctos"]

        self.timer_continue = QTimer(self)
        self.timer_continue.timeout.connect(self._paso_automatico)

        self._setup_ui()
        self._aplicar_tema("ctos")
        self._configurar_ornamentos()
        self._reproducir_secuencia_arranque()

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

        # Ahora que ambos paneles (y self.editor) existen, se conectan
        # las señales cruzadas entre el editor y el panel de breakpoints.
        self.editor.breakpoints_cambiaron.connect(self._actualizar_lista_breakpoints)

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
    # SECCION: Barra de control superior (Step Into/Over/Out, Continue,
    # Stop, Restart, Reload, File, Help) + indicadores de estado
    # --------------------------------------------------------------------
    def _setup_barra_control(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("barraControl")
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self.label_estado = QLabel("STOPPED")
        self.label_estado.setObjectName("labelEstado")
        layout.addWidget(self.label_estado)

        layout.addWidget(self._separador_vertical())

        layout.addWidget(crear_boton_toolbar("Step Into", "F2", self._on_step_into))
        layout.addWidget(crear_boton_toolbar("Step Over", "Ctrl+F2", self._on_step_over))
        layout.addWidget(crear_boton_toolbar("Step Out", "Shift+F2", self._on_step_out))
        layout.addWidget(self._separador_vertical())
        layout.addWidget(crear_boton_toolbar("Continue", "F3", self._on_continue))
        layout.addWidget(crear_boton_toolbar("Stop", "", self._on_stop))
        layout.addWidget(self._separador_vertical())
        layout.addWidget(crear_boton_toolbar("Restart", "Ctrl+R", self._on_restart))
        layout.addWidget(crear_boton_toolbar("Reload", "Ctrl+Shift+L", self._on_reload))

        layout.addStretch()

        self.label_online = QLabel("● ONLINE")
        self.label_online.setObjectName("labelOnline")
        layout.addWidget(self.label_online)

        layout.addWidget(self._separador_vertical())

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
    # SECCION: Panel izquierdo -> pestanas (Registers / Call stack / Trace
    # / Breakpoints / Watchpoints / Symbols / Counters / Settings)
    # --------------------------------------------------------------------
    def _setup_panel_izquierdo(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_seccion("REGISTERS"))

        tabs = QTabWidget()
        tabs.setObjectName("tabsIzquierda")
        tabs.addTab(self._setup_tabla_registros(), "Registers")
        tabs.addTab(self._panel_placeholder("Call stack vacio."), "Call stack")
        tabs.addTab(self._panel_placeholder("Sin traza de ejecucion."), "Trace")
        tabs.addTab(self._setup_tab_breakpoints(), "Breakpoints")
        tabs.addTab(self._panel_placeholder("No hay watchpoints."), "Watchpoints")
        tabs.addTab(self._panel_placeholder("Tabla de simbolos vacia."), "Symbols")
        tabs.addTab(self._panel_placeholder("Sin contadores."), "Counters")
        tabs.addTab(self._setup_tab_ajustes(), "Settings")

        layout.addWidget(tabs)

        return panel

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

    def _panel_placeholder(self, texto: str) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("labelPlaceholder")
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(etiqueta)
        return contenedor

    def _setup_tab_breakpoints(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)

        ayuda = QLabel("Clic en el numero de linea del editor para agregar o quitar un breakpoint.\nDoble clic aqui para eliminarlo.")
        ayuda.setObjectName("labelPlaceholder")
        ayuda.setWordWrap(True)
        layout.addWidget(ayuda)

        self.lista_breakpoints = QListWidget()
        self.lista_breakpoints.setObjectName("listaBreakpoints")
        self.lista_breakpoints.itemDoubleClicked.connect(self._quitar_breakpoint_desde_lista)
        layout.addWidget(self.lista_breakpoints)

        return contenedor

    # --------------------------------------------------------------------
    # SECCION: Panel de AJUSTES (Settings) -> tema visual, ornamentacion,
    # opciones del editor y formato de numeros de memoria/registros
    # --------------------------------------------------------------------
    def _setup_tab_ajustes(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # ---- Apariencia / tema ----
        layout.addWidget(self._subtitulo("Apariencia"))

        fila_tema = QHBoxLayout()
        fila_tema.addWidget(QLabel("Tema:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItem("Matrix", userData="matrix")
        self.combo_tema.addItem("piOS (SUPERHOT)", userData="pios")
        self.combo_tema.addItem("cTOS (Watch_Dogs)", userData="ctos")
        self.combo_tema.currentIndexChanged.connect(self._on_cambiar_tema)
        fila_tema.addWidget(self.combo_tema)
        layout.addLayout(fila_tema)

        self.check_scanlines = QCheckBox("Efecto CRT (scanlines)")
        self.check_scanlines.setChecked(True)
        self.check_scanlines.toggled.connect(self._on_toggle_scanlines)
        layout.addWidget(self.check_scanlines)

        self.check_glow = QCheckBox("Brillo neon (glow)")
        self.check_glow.setChecked(True)
        self.check_glow.toggled.connect(self._actualizar_glow)
        layout.addWidget(self.check_glow)

        # ---- Editor ----
        layout.addWidget(self._subtitulo("Editor"))
        fila_fuente = QHBoxLayout()
        fila_fuente.addWidget(QLabel("Tamano de fuente:"))
        self.spin_fuente = QSpinBox()
        self.spin_fuente.setRange(8, 24)
        self.spin_fuente.setValue(11)
        self.spin_fuente.valueChanged.connect(self._on_cambiar_tamano_fuente)
        fila_fuente.addWidget(self.spin_fuente)
        layout.addLayout(fila_fuente)

        # ---- Number Display Options ----
        layout.addWidget(self._subtitulo("Number Display Options"))
        grid = QGridLayout()
        grid.setSpacing(6)

        grid.addWidget(QLabel("Size:"), 0, 0)
        self.combo_size = QComboBox()
        self.combo_size.addItems(["Byte", "Half Word", "Word"])
        self.combo_size.setCurrentText("Word")
        grid.addWidget(self.combo_size, 0, 1)

        grid.addWidget(QLabel("Format:"), 1, 0)
        self.combo_formato = QComboBox()
        self.combo_formato.addItems(["Binary", "Decimal", "Hexadecimal"])
        self.combo_formato.setCurrentText("Hexadecimal")
        grid.addWidget(self.combo_formato, 1, 1)

        grid.addWidget(QLabel("Memory words per row:"), 2, 0)
        self.spin_memoria = QSpinBox()
        self.spin_memoria.setRange(1, 16)
        self.spin_memoria.setValue(4)
        grid.addWidget(self.spin_memoria, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

        return panel

    def _subtitulo(self, texto: str) -> QLabel:
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("labelSubtitulo")
        return etiqueta

    def _titulo_seccion(self, texto: str) -> QLabel:
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("tituloSeccion")
        return etiqueta

    # --------------------------------------------------------------------
    # SECCION: Panel derecho -> editor de codigo con cabecera (Compile and
    # Load, selector de lenguaje, nombre de archivo, estado de sintaxis en
    # vivo) y pestanas inferiores (Editor / Disassembly / Memory)
    # --------------------------------------------------------------------
    def _setup_panel_editor(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_seccion("KVX-08 L4N"))

        fila_cabecera = QWidget()
        fila_cabecera.setObjectName("filaCabeceraEditor")
        layout_cabecera = QHBoxLayout(fila_cabecera)
        layout_cabecera.setContentsMargins(10, 6, 10, 6)

        boton_compilar = QPushButton("Compile and Load (F5)")
        boton_compilar.setObjectName("botonCompilar")
        boton_compilar.setEnabled(False)
        #boton_compilar.clicked.connect(self._on_compilar)
        
        layout_cabecera.addWidget(boton_compilar)

        layout_cabecera.addWidget(QLabel("Language:"))
        self.combo_lenguaje = QComboBox()
        self.combo_lenguaje.addItems(["Nios II", "MIPS", "RISC-V"])
        layout_cabecera.addWidget(self.combo_lenguaje)

        layout_cabecera.addStretch()

        self.label_estado_sintaxis = QLabel("✓ SIN ERRORES")
        self.label_estado_sintaxis.setObjectName("labelSintaxisOk")
        layout_cabecera.addWidget(self.label_estado_sintaxis)

        self.label_archivo = QLabel()
        self.label_archivo.setObjectName("labelArchivo")
        layout_cabecera.addWidget(self.label_archivo)

        layout.addWidget(fila_cabecera)

        tabs_editor = QTabWidget()
        tabs_editor.setObjectName("tabsEditor")
        tabs_editor.setTabPosition(QTabWidget.TabPosition.South)

        self.editor = CodeEditor()
        self.editor.setPlainText(".global _start\n_start:\n\tmovi r2, 5\n\taddi r3, r2, 10\n\tret\n")
        self.editor.errores_cambiaron.connect(self._actualizar_estado_sintaxis)
        self.editor.textChanged.connect(self._marcar_modificado)
        self._refrescar_label_archivo()

        panel_disassembly = QPlainTextEdit("// Disassembly no disponible aun.")
        panel_disassembly.setObjectName("panelSecundario")
        panel_disassembly.setReadOnly(True)

        panel_memoria = QPlainTextEdit("// Vista de memoria no disponible aun.")
        panel_memoria.setObjectName("panelSecundario")
        panel_memoria.setReadOnly(True)

        tabs_editor.addTab(self.editor, "Editor (Ctrl+E)")
        tabs_editor.addTab(panel_disassembly, "Disassembly (Ctrl+D)")
        tabs_editor.addTab(panel_memoria, "Memory (Ctrl+M)")

        layout.addWidget(tabs_editor)

        return panel

    def _actualizar_estado_sintaxis(self, errores: dict):
        if not errores:
            self.label_estado_sintaxis.setObjectName("labelSintaxisOk")
            self.label_estado_sintaxis.setText("✓ SIN ERRORES")
        else:
            self.label_estado_sintaxis.setObjectName("labelSintaxisError")
            self.label_estado_sintaxis.setText(f"⚠ {len(errores)} ERROR(ES) DE SINTAXIS")
        self.label_estado_sintaxis.style().unpolish(self.label_estado_sintaxis)
        self.label_estado_sintaxis.style().polish(self.label_estado_sintaxis)

    # --------------------------------------------------------------------
    # SECCION: Consola de mensajes inferior (no editable) con boton Clear
    # --------------------------------------------------------------------
    def _setup_panel_mensajes(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cabecera = QWidget()
        cabecera.setObjectName("cabeceraMensajes")
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(10, 4, 10, 4)
        layout_cabecera.addWidget(self._titulo_seccion("MESSAGES"))
        layout_cabecera.addStretch()

        boton_clear = QPushButton("Clear")
        boton_clear.setObjectName("botonClear")
        boton_clear.clicked.connect(self.limpiar_mensajes)
        layout_cabecera.addWidget(boton_clear)

        layout.addWidget(cabecera)

        self.consola_mensajes = QPlainTextEdit()
        self.consola_mensajes.setObjectName("consolaMensajes")
        self.consola_mensajes.setReadOnly(True)
        layout.addWidget(self.consola_mensajes)

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

    def actualizar_consola_mensajes(self, errores: dict[int, str]):
        for numero, mensaje in sorted(errores.items()):
            self.agregar_mensaje(f"Linea {numero}: {mensaje}")

    # --------------------------------------------------------------------
    # Breakpoints: sincroniza la lista visual con el editor
    # --------------------------------------------------------------------
    def _actualizar_lista_breakpoints(self, conjunto_lineas: set):
        self.lista_breakpoints.clear()
        for numero in sorted(conjunto_lineas):
            self.lista_breakpoints.addItem(QListWidgetItem(f"● Linea {numero}"))

    def _quitar_breakpoint_desde_lista(self, item: QListWidgetItem):
        coincidencia = re.search(r"(\d+)", item.text())
        if coincidencia:
            self.editor.alternar_breakpoint(int(coincidencia.group(1)))

    # --------------------------------------------------------------------
    # Archivo: seguimiento de nombre / estado modificado
    # --------------------------------------------------------------------
    def _marcar_modificado(self):
        self._modificado = True
        self._refrescar_label_archivo()

    def _refrescar_label_archivo(self):
        nombre = os.path.basename(self.ruta_archivo_actual) if self.ruta_archivo_actual else "untitled.s"
        sufijos = []
        if self._modificado:
            sufijos.append("changed since save")
        if self.snapshot_codigo != self.editor.toPlainText():
            sufijos.append("changed since compile")
        extra = "  [" + "] [".join(sufijos) + "]" if sufijos else ""
        self.label_archivo.setText(nombre + extra)

    # --------------------------------------------------------------------
    # FUNCIONES BASICAS: menu File
    # --------------------------------------------------------------------
    def _on_nuevo_archivo(self):
        self.editor.setPlainText("")
        self.ruta_archivo_actual = None
        self.snapshot_codigo = None
        self._modificado = False
        self._reiniciar_simulacion()
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
        self.snapshot_codigo = None
        self._modificado = False
        self._reiniciar_simulacion()
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
            "1) Compile and Load (F5) valida la sintaxis y prepara la ejecucion.\n"
            "2) Clic en el numero de linea agrega/quita un breakpoint.\n"
            "3) Step Into/Over/Out avanzan una linea; Continue corre hasta un "
            "breakpoint o el final del programa."
        )

    def _on_ayuda_about(self):
        QMessageBox.information(
            self, "About",
            f"IDE - Debugger\nTema actual: {self.tema_actual.upper()}\n\n"
            "Interfaz construida con PyQt6."
        )

    # --------------------------------------------------------------------
    # FUNCIONES BASICAS: simulador de ejecucion (demostrativo)
    # El objetivo es que la barra de control haga algo real mientras se
    # conecta el automata/simulador definitivo (ver comentarios abajo).
    # --------------------------------------------------------------------
    def _reiniciar_simulacion(self):
        self.timer_continue.stop()
        self.linea_actual_ejecucion = 0
        self._reset_registros()
        self.editor.marcar_linea_pc(None)
        self.label_estado.setText("STOPPED")

    def _reset_registros(self):
        for fila in range(self.tabla_registros.rowCount()):
            self.tabla_registros.item(fila, 1).setText("00000000")

    def _siguiente_linea_ejecutable(self, desde: int) -> int | None:
        lineas = (self.snapshot_codigo or "").split("\n")
        for numero in range(desde + 1, len(lineas) + 1):
            texto = re.split(r"#|//", lineas[numero - 1], maxsplit=1)[0].strip()
            if texto:
                return numero
        return None

    def _ejecutar_paso(self, etiqueta_log: str) -> bool:
        if self.snapshot_codigo is None:
            self.agregar_mensaje("> Debes compilar (Compile and Load) antes de ejecutar.")
            return False

        siguiente = self._siguiente_linea_ejecutable(self.linea_actual_ejecucion)
        if siguiente is None:
            self.agregar_mensaje("> Fin del programa.")
            self.label_estado.setText("STOPPED")
            return False

        self.linea_actual_ejecucion = siguiente
        texto_linea = self.snapshot_codigo.split("\n")[siguiente - 1]

        self._simular_instruccion(texto_linea)
        self._set_valor_registro("pc", siguiente * 4)
        self.editor.marcar_linea_pc(siguiente)
        self.label_estado.setText("RUNNING")
        self.agregar_mensaje(f"> {etiqueta_log} -> linea {siguiente}: {texto_linea.strip()}")
        return True

    def _simular_instruccion(self, texto_linea: str):
        """
        Ejecucion MUY BASICA de demostracion: solo interpreta 'movi' y 'add'
        para mostrar que el panel de registros puede reaccionar en vivo.
        El automata / simulador real reemplazara esta logica por completo.
        """
        texto = re.split(r"#|//", texto_linea, maxsplit=1)[0].strip()

        coincidencia_movi = re.match(r"^(?:[A-Za-z_]\w*:\s*)?movi\s+r(\d+)\s*,\s*(-?\d+)", texto, re.IGNORECASE)
        if coincidencia_movi:
            indice, valor = coincidencia_movi.groups()
            self._set_valor_registro(f"r{indice}", int(valor))
            return

        coincidencia_add = re.match(
            r"^(?:[A-Za-z_]\w*:\s*)?add(?:i)?\s+r(\d+)\s*,\s*r(\d+)\s*,\s*r?(-?\d+)",
            texto, re.IGNORECASE,
        )
        if coincidencia_add:
            r_destino, r_a, operando_b = coincidencia_add.groups()
            valor_a = self._get_valor_registro(f"r{r_a}")
            valor_b = self._get_valor_registro(f"r{operando_b}") if f"r{operando_b}" in self._indice_registros else int(operando_b)
            self._set_valor_registro(f"r{r_destino}", valor_a + valor_b)

    def _get_valor_registro(self, nombre: str) -> int:
        fila = self._indice_registros.get(nombre)
        if fila is None:
            return 0
        try:
            return int(self.tabla_registros.item(fila, 1).text(), 16)
        except ValueError:
            return 0

    def _set_valor_registro(self, nombre: str, valor: int):
        fila = self._indice_registros.get(nombre)
        if fila is not None:
            self.tabla_registros.item(fila, 1).setText(f"{valor & 0xFFFFFFFF:08X}")

    # --------------------------------------------------------------------
    # ==================================================================
    # INTEGRACION AUTOMATA / JSON (pendiente de implementar por separado)
    # ------------------------------------------------------------------
    # El metodo _simular_instruccion de arriba es solo una demostracion.
    # Cuando el automata/simulador real este listo, puede reemplazar su
    # cuerpo (o el de _ejecutar_paso) para interpretar instrucciones de
    # forma completa segun la definicion cargada desde JSON, por ejemplo:
    #
    # def cargar_definicion_cpu(self, ruta_json: str):
    #     import json
    #     with open(ruta_json, "r", encoding="utf-8") as f:
    #         self.definicion_cpu = json.load(f)
    # ==================================================================
    # --------------------------------------------------------------------

    def _on_step_into(self):
        self._ejecutar_paso("Step Into")

    def _on_step_over(self):
        self._ejecutar_paso("Step Over")

    def _on_step_out(self):
        self._ejecutar_paso("Step Out")

    def _on_continue(self):
        if self.snapshot_codigo is None:
            self.agregar_mensaje("> Debes compilar (Compile and Load) antes de ejecutar.")
            return
        self.label_estado.setText("RUNNING")
        self.timer_continue.start(400)

    def _paso_automatico(self):
        avanzo = self._ejecutar_paso("Continue")
        if not avanzo:
            self.timer_continue.stop()
            return
        if self.linea_actual_ejecucion in self.editor.lineas_breakpoint:
            self.timer_continue.stop()
            self.label_estado.setText("STOPPED")
            self.agregar_mensaje(f"> Breakpoint alcanzado en linea {self.linea_actual_ejecucion}.")

    def _on_stop(self):
        self.timer_continue.stop()
        self.label_estado.setText("STOPPED")
        self.agregar_mensaje("> Ejecucion detenida.")

    def _on_restart(self):
        self._reiniciar_simulacion()
        self.agregar_mensaje("> Simulador reiniciado.")

    def _on_reload(self):
        self.timer_continue.stop()
        if self.snapshot_codigo is not None:
            self.editor.setPlainText(self.snapshot_codigo)
        self._reiniciar_simulacion()
        self.agregar_mensaje("> Programa recargado desde la ultima compilacion.")

    def _on_compilar(self):
        self.agregar_mensaje("> Compilando y cargando programa...")
        self.editor.analizar_sintaxis_basico()

        if self.editor.lineas_con_error:
            self.agregar_mensaje(f"> {len(self.editor.lineas_con_error)} error(es) encontrados:")
            self.actualizar_consola_mensajes(self.editor.lineas_con_error)
            self.agregar_mensaje("> Compilacion fallida.")
            return

        self.snapshot_codigo = self.editor.toPlainText()
        self._refrescar_label_archivo()
        self._reiniciar_simulacion()
        self.agregar_mensaje("> Compilacion exitosa. Listo para ejecutar (Step / Continue).")

        # ==================================================================
        # INTEGRACION AUTOMATA / JSON (pendiente de implementar por separado)
        # ------------------------------------------------------------------
        # self.editor.analizar_sintaxis_automata()
        # ==================================================================

    # --------------------------------------------------------------------
    # ORNAMENTACION: glow neon + parpadeo del indicador ONLINE (y del
    # badge RUNNING) + reproduccion animada de la secuencia de arranque
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

        if self.label_estado.text() == "RUNNING":
            self.label_estado.setStyleSheet(
                f"background-color: {color}; color: {paleta['fondo']}; "
                f"font-weight: bold; padding: 6px 14px; border-radius: {paleta['radio']};"
            )
        else:
            self.label_estado.setStyleSheet("")  # vuelve a heredar del tema global

    def _reproducir_secuencia_arranque(self):
        for indice, linea in enumerate(self.SECUENCIA_ARRANQUE):
            QTimer.singleShot(180 * indice, lambda texto=linea: self.agregar_mensaje(texto))

    def _aplicar_glows_tema(self, paleta: dict):
        aplicar_glow(self.label_estado, color=paleta["brillante"], radio=16)
        aplicar_glow(self.label_online, color=paleta["primario"], radio=18)
        aplicar_glow(self.label_version, color=paleta["primario"], radio=8)
        for etiqueta in self.findChildren(QLabel, "tituloSeccion"):
            aplicar_glow(etiqueta, color=paleta["primario"], radio=10)

    def _actualizar_glow(self, activo: bool):
        if activo:
            self._aplicar_glows_tema(self._paleta_actual)
        else:
            objetivos = [self.label_estado, self.label_online, self.label_version]
            objetivos.extend(self.findChildren(QLabel, "tituloSeccion"))
            for widget in objetivos:
                widget.setGraphicsEffect(None)

    # --------------------------------------------------------------------
    # SETTINGS: callbacks del panel de ajustes
    # --------------------------------------------------------------------
    def _on_cambiar_tema(self, _indice: int):
        clave = self.combo_tema.currentData()
        self._aplicar_tema(clave)
        self.agregar_mensaje(f"> Tema visual cambiado a '{clave.upper()}'.")

    def _on_toggle_scanlines(self, activo: bool):
        self.overlay_scanlines.setVisible(activo)

    def _on_cambiar_tamano_fuente(self, valor: int):
        fuente = self.editor.font()
        fuente.setPointSize(valor)
        self.editor.setFont(fuente)

    # --------------------------------------------------------------------
    # Aplica un tema completo: hoja de estilos + colores dinamicos del
    # editor (gutter/errores/breakpoints/pc) + glow + version en el pie
    # --------------------------------------------------------------------
    def _aplicar_tema(self, clave: str):
        paleta = self.PALETAS[clave]
        self.tema_actual = clave
        self._paleta_actual = paleta

        self.setStyleSheet(Template(self._PLANTILLA_QSS).substitute(paleta))

        self.editor.color_normal = QColor(paleta["tenue"])
        self.editor.color_error = QColor(paleta["alerta"])
        self.editor.color_breakpoint = QColor(paleta["alerta"])
        self.editor.color_pc = QColor(paleta["brillante"])
        color_linea_actual = QColor(paleta["primario"])
        color_linea_actual.setAlpha(28)
        self.editor.color_linea_actual = color_linea_actual
        self.editor.highlight_current_line()
        self.editor.line_number_area.update()

        fila_pc = self._indice_registros.get("pc")
        if fila_pc is not None:
            color_fondo = QColor(paleta["brillante"])
            color_texto = QColor(paleta["fondo"])
            for columna in (0, 1):
                item = self.tabla_registros.item(fila_pc, columna)
                if item:
                    item.setBackground(color_fondo)
                    item.setForeground(color_texto)

        if getattr(self, "check_glow", None) is None or self.check_glow.isChecked():
            self._aplicar_glows_tema(paleta)

        self.label_version.setText(self.VERSIONES.get(clave, ""))

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
        QLabel#labelEstado {
            color: $fondo;
            background-color: $brillante;
            font-weight: bold;
            padding: 6px 14px;
            border-radius: $radio;
        }
        QLabel#labelOnline { color: $brillante; font-weight: bold; padding: 6px 8px; }
        QLabel#labelPrompt { color: $tenue; font-weight: bold; }
        QLabel#labelVersion { color: $tenue; font-style: italic; font-size: 11px; }
        QFrame#separadorVertical { color: $tenue; }

        QPushButton#botonToolbar {
            background-color: $fondo; color: $primario;
            border: 1px solid $tenue; border-radius: $radio;
            padding: 4px 10px; font-size: 11px;
        }
        QPushButton#botonToolbar:hover { background-color: $primario; color: $fondo; border: 1px solid $brillante; }
        QPushButton#botonToolbar:pressed { background-color: $brillante; }

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
        QLabel#labelSubtitulo { color: $brillante; font-weight: bold; font-size: 11px; padding-top: 6px; }
        QLabel#labelPlaceholder { color: $tenue; font-style: italic; }

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

        /* ---------------- Listas (breakpoints, etc.) --------------------- */
        QListWidget#listaBreakpoints {
            background-color: $fondo; color: $alerta;
            border: 1px solid $tenue; border-radius: $radio;
        }
        QListWidget#listaBreakpoints::item { padding: 3px 6px; }
        QListWidget#listaBreakpoints::item:selected { background-color: $alerta; color: $fondo; }

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
        QPlainTextEdit#panelSecundario { background-color: $fondo; color: $tenue; border: none; padding: 10px; }

        QWidget#filaCabeceraEditor { background-color: $fondo_panel; border-bottom: 1px solid $tenue; }

        QPushButton#botonCompilar {
            background-color: $fondo; color: $brillante; border: 1px solid $brillante;
            border-radius: $radio; padding: 5px 12px; font-weight: bold;
        }
        QPushButton#botonCompilar:hover { background-color: $brillante; color: $fondo; }

        QLabel#labelArchivo { color: $tenue; font-style: italic; padding-left: 12px; }

        /* ---------------- Badge de estado de sintaxis (en vivo) --------- */
        QLabel#labelSintaxisOk { color: $primario; font-weight: bold; padding: 3px 10px; border: 1px solid $tenue; border-radius: $radio; }
        QLabel#labelSintaxisError { background-color: $alerta; color: $fondo; font-weight: bold; padding: 3px 10px; border-radius: $radio; }

        /* ---------------- Consola de mensajes ---------------------------- */
        QWidget#cabeceraMensajes { background-color: $fondo_panel; border-top: 2px $borde_estilo $primario; }
        QPlainTextEdit#consolaMensajes { background-color: $fondo; color: $primario; border: none; padding: 6px 10px; font-size: 12px; }
        QPushButton#botonClear { background-color: $fondo; color: $primario; border: 1px solid $tenue; padding: 3px 14px; border-radius: $radio; }
        QPushButton#botonClear:hover { background-color: $primario; color: $fondo; }

        /* ---------------- Pie de pagina ------------------------------------ */
        QWidget#piePagina { background-color: $fondo_panel; border-top: 1px solid $tenue; }

        /* ---------------- Combos / Spin boxes / Checkboxes ------------------ */
        QComboBox, QSpinBox {
            background-color: $fondo; color: $primario; border: 1px solid $tenue;
            padding: 3px 6px; border-radius: $radio;
        }
        QComboBox:hover, QSpinBox:hover { border: 1px solid $brillante; }
        QComboBox QAbstractItemView { background-color: $fondo_panel; color: $primario; selection-background-color: $primario; selection-color: $fondo; }

        QCheckBox { color: $primario; spacing: 8px; padding: 2px 0px; }
        QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid $tenue; background-color: $fondo; }
        QCheckBox::indicator:checked { background-color: $brillante; border: 1px solid $brillante; }

        /* ---------------- Scrollbars ------------------------------------- */
        QScrollBar:vertical, QScrollBar:horizontal { background: $fondo_panel; width: 10px; height: 10px; }
        QScrollBar::handle { background: $tenue; border-radius: 5px; min-height: 20px; }
        QScrollBar::handle:hover { background: $brillante; }
    """


# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = IDEWindow()
    ventana.show()
    sys.exit(app.exec())
