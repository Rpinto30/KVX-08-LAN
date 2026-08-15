"""
==============================================================================
 ascii_table.py
 Panel visual con la tabla del alfabeto latino (A-Z, a-z) y su codigo
 correspondiente en la tabla ASCII, en formato Decimal y Hexadecimal.

 Datos de referencia: https://elcodigoascii.com.ar/
   - Letras mayusculas: ASCII 65 (0x41) a 90 (0x5A)
   - Letras minusculas: ASCII 97 (0x61) a 122 (0x7A)

 Pensado para agregarse como una pestana nueva dentro del QTabWidget del
 panel izquierdo del IDE (el mismo que hoy solo tiene la pestana
 "Registers"). Solo interfaz grafica, sin ninguna logica adicional.
==============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt


# ==============================================================================
# SECCION: DATOS -> letras del alfabeto latino y su codigo ASCII
# ==============================================================================
def _generar_filas_alfabeto():
    """
    Devuelve una lista de tuplas (caracter, decimal, hexadecimal) para
    todas las letras del alfabeto latino, mayusculas primero y luego
    minusculas, siguiendo la tabla ASCII estandar.
    """
    filas = []
    for codigo in range(ord("A"), ord("Z") + 1):
        filas.append((chr(codigo), codigo, f"0x{codigo:02X}"))
    for codigo in range(ord("a"), ord("z") + 1):
        filas.append((chr(codigo), codigo, f"0x{codigo:02X}"))
    return filas


FILAS_ALFABETO_ASCII = _generar_filas_alfabeto()


# ==============================================================================
# SECCION: PANEL DE LA PESTANA "ASCII"
# ==============================================================================
class AsciiTablePanel(QWidget):
    """
    Tabla de solo lectura con 3 columnas: Caracter / Decimal / Hex.
    Usa el mismo objectName ("tablaRegistros") que la tabla de registros
    para heredar automaticamente el mismo estilo visual (colores del tema
    activo) sin necesidad de agregar reglas QSS nuevas.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabla_ascii = QTableWidget(len(FILAS_ALFABETO_ASCII), 3)
        self.tabla_ascii.setObjectName("tablaRegistros")
        self.tabla_ascii.setHorizontalHeaderLabels(["Caracter", "Decimal", "Hexadecimal"])
        self.tabla_ascii.verticalHeader().setVisible(False)
        self.tabla_ascii.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_ascii.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla_ascii.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_ascii.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_ascii.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_ascii.setShowGrid(False)

        for fila, (caracter, decimal, hexadecimal) in enumerate(FILAS_ALFABETO_ASCII):
            item_caracter = QTableWidgetItem(caracter)
            item_decimal = QTableWidgetItem(str(decimal))
            item_hex = QTableWidgetItem(hexadecimal)

            item_caracter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_decimal.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_hex.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabla_ascii.setItem(fila, 0, item_caracter)
            self.tabla_ascii.setItem(fila, 1, item_decimal)
            self.tabla_ascii.setItem(fila, 2, item_hex)

        layout.addWidget(self.tabla_ascii)
