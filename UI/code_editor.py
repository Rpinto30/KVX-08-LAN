"""
==============================================================================
 code_editor.py
 UI de la seccion "editor de codigo" del IDE.

 Contiene:
   - LineNumberArea : gutter que dibuja los numeros de renglon.
   - CodeEditor      : QPlainTextEdit extendido con numeracion de linea y
                        resaltado del renglon actual (SOLO interfaz, sin
                        validacion de sintaxis ni ejecucion).
   - EditorPanel     : panel completo de la seccion derecha del IDE
                        (titulo + cabecera con selector de TEMA y nombre de
                        archivo + pestana "Editor" que contiene un
                        CodeEditor). Esta es la clase que IDEWindow
                        instancia para mostrar la seccion de codigo.
==============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QTextEdit,
    QComboBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont, QTextCursor


# ==============================================================================
# SECCION: GUTTER DE NUMEROS DE LINEA (solo numeracion, sin breakpoints ni
# marcador de linea de ejecucion, ya que no hay simulador).
# ==============================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, evento):
        self.code_editor.line_number_area_paint_event(evento)


# ==============================================================================
# SECCION: EDITOR DE CODIGO
# QPlainTextEdit extendido con gutter numerado y resaltado del renglon
# actual. No incluye validacion de sintaxis ni ninguna otra funcionalidad
# de automata: es unicamente la interfaz grafica del editor.
# ==============================================================================
class CodeEditor(QPlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorCodigo")

        # Colores dinamicos (los actualiza IDEWindow segun el tema activo)
        self.color_normal = QColor("#0c6b1f")
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

    # --------------------------------------------------------------------
    # Ancho dinamico del gutter (segun cantidad de digitos)
    # --------------------------------------------------------------------
    def line_number_area_width(self) -> int:
        digitos = len(str(max(1, self.blockCount())))
        espacio = 20 + self.fontMetrics().horizontalAdvance("9") * digitos
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
    # Dibuja unicamente los numeros de renglon.
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
                painter.setPen(self.color_normal)
                painter.drawText(
                    0, top, self.line_number_area.width() - 6, alto,
                    Qt.AlignmentFlag.AlignRight, str(numero_linea)
                )
            bloque = bloque.next()
            top += alto
            numero_bloque += 1

    # --------------------------------------------------------------------
    # Resalta el renglon donde esta el cursor.
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
        self.setExtraSelections(selecciones)


# ==============================================================================
# SECCION: PANEL COMPLETO DEL EDITOR (seccion derecha del IDE)
# Titulo + cabecera (selector de TEMA y nombre de archivo) + pestana unica
# "Editor" que contiene el CodeEditor.
# ==============================================================================
class EditorPanel(QWidget):

    # Se emite cuando el usuario cambia el tema desde el combobox de esta
    # seccion. IDEWindow debe conectarse a esta senal para aplicar el tema.
    tema_cambiado = pyqtSignal(str)

    # Se emite cada vez que el contenido del editor cambia (para que
    # IDEWindow pueda marcar el archivo como modificado).
    contenido_modificado = pyqtSignal()

    TEMAS = (
        ("Matrix", "matrix"),
        ("piOS (SUPERHOT)", "pios"),
        ("cTOS (Watch_Dogs)", "ctos"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titulo = QLabel("KVX-08 L4N")
        titulo.setObjectName("tituloSeccion")
        layout.addWidget(titulo)

        fila_cabecera = QWidget()
        fila_cabecera.setObjectName("filaCabeceraEditor")
        layout_cabecera = QHBoxLayout(fila_cabecera)
        layout_cabecera.setContentsMargins(10, 6, 10, 6)

        layout_cabecera.addWidget(QLabel("Theme:"))
        self.combo_tema = QComboBox()
        for etiqueta, clave in self.TEMAS:
            self.combo_tema.addItem(etiqueta, userData=clave)
        self.combo_tema.currentIndexChanged.connect(self._on_cambiar_tema)
        layout_cabecera.addWidget(self.combo_tema)

        layout_cabecera.addStretch()

        self.label_archivo = QLabel()
        self.label_archivo.setObjectName("labelArchivo")
        layout_cabecera.addWidget(self.label_archivo)

        layout.addWidget(fila_cabecera)

        tabs_editor = QTabWidget()
        tabs_editor.setObjectName("tabsEditor")
        tabs_editor.setTabPosition(QTabWidget.TabPosition.South)

        self.editor = CodeEditor()
        self.editor.setPlainText(
            ".global _start\n_start:\n\tmovi r2, 5\n\taddi r3, r2, 10\n\tret\n"
        )
        self.editor.textChanged.connect(self.contenido_modificado.emit)

        tabs_editor.addTab(self.editor, "Editor (Ctrl+E)")

        layout.addWidget(tabs_editor)

    # --------------------------------------------------------------------
    # Callback interno del combobox de tema.
    # --------------------------------------------------------------------
    def _on_cambiar_tema(self, _indice: int):
        clave = self.combo_tema.currentData()
        if clave:
            self.tema_cambiado.emit(clave)

    # --------------------------------------------------------------------
    # API publica para que IDEWindow sincronice el combobox sin disparar
    # la senal (por ejemplo, al aplicar el tema inicial).
    # --------------------------------------------------------------------
    def set_tema_actual(self, clave: str):
        indice = self.combo_tema.findData(clave)
        if indice >= 0:
            self.combo_tema.blockSignals(True)
            self.combo_tema.setCurrentIndex(indice)
            self.combo_tema.blockSignals(False)
