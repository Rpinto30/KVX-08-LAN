import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt


# ==============================================================================
# SECCION: PANEL DE LA PESTANA "AUTOMATA"
# Tabla de solo lectura con la traza de transiciones del automata:
# Paso / Estado actual / Lee / Transicion / Nuevo estado / Explicacion.
# ==============================================================================
class AutomatonTablePanel(QWidget):
    """
    Tabla de solo lectura que muestra la traza de ejecucion del automata
    (una fila por paso). Usa el mismo objectName ("tablaRegistros") que la
    tabla de registros/ASCII para heredar automaticamente el estilo del
    tema activo, sin agregar reglas QSS nuevas.

    Los datos se cargan mediante cargar_json(), que acepta:
      - una lista de dicts ya parseada,
      - un string con contenido JSON,
      - la ruta (str o Path) a un archivo .json.

    Cada elemento (paso) debe tener las claves:
      paso, estado_actual, lee, transicion, nuevo_estado, explicacion

    Claves opcionales por paso:
      inicio     (bool) -> marca el estado actual con "→" (por defecto,
                            se asume True solo para el paso 0).
      aceptacion (bool) -> marca el nuevo estado con "◎" (por defecto se
                            detecta si "explicacion" contiene "acept").

    Ejemplo de JSON esperado:
      [
        {"paso": 0, "estado_actual": "q0", "lee": "—", "transicion": "—",
         "nuevo_estado": "q0", "explicacion": "Inicio"},
        {"paso": 1, "estado_actual": "q0", "lee": "A",
         "transicion": "δ(q0,A)=q1", "nuevo_estado": "q1",
         "explicacion": "Correcto"},
        {"paso": 3, "estado_actual": "q2", "lee": "C",
         "transicion": "δ(q2,C)=q3", "nuevo_estado": "q3",
         "explicacion": "Cadena aceptada"}
      ]
    """

    COLUMNAS = ("Paso", "Estado actual", "Lee", "Transición", "Nuevo estado", "Explicación")

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabla_automata = QTableWidget(0, len(self.COLUMNAS))
        self.tabla_automata.setObjectName("tablaRegistros")
        self.tabla_automata.setHorizontalHeaderLabels(list(self.COLUMNAS))
        self.tabla_automata.verticalHeader().setVisible(False)
        self.tabla_automata.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_automata.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        cabecera = self.tabla_automata.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla_automata.setShowGrid(False)
        self.tabla_automata.setWordWrap(True)

        layout.addWidget(self.tabla_automata)

    # --------------------------------------------------------------------
    # API publica: carga la tabla a partir de JSON (lista, string o ruta)
    # --------------------------------------------------------------------
    def cargar_json(self, datos):
        filas = self._normalizar_datos(datos)
        self.cargar_transiciones(filas)

    def _normalizar_datos(self, datos) -> list[dict]:
        if isinstance(datos, (list, tuple)):
            return list(datos)
        if isinstance(datos, (str, Path)):
            texto = str(datos)
            ruta = Path(texto)
            if ruta.suffix.lower() == ".json" and ruta.exists():
                texto = ruta.read_text(encoding="utf-8")
            return json.loads(texto)
        raise TypeError("Formato de datos del automata no soportado (se esperaba lista, str o Path).")

    # --------------------------------------------------------------------
    # API publica: carga la tabla a partir de una lista de dicts ya lista
    # --------------------------------------------------------------------
    def cargar_transiciones(self, filas: list[dict]):
        self.tabla_automata.setRowCount(len(filas))
        for fila_idx, dato in enumerate(filas):
            self._llenar_fila(fila_idx, dato)

    # --------------------------------------------------------------------
    # API publica: agrega un solo paso al final (util para traza en vivo)
    # --------------------------------------------------------------------
    def agregar_paso(self, dato: dict):
        fila_idx = self.tabla_automata.rowCount()
        self.tabla_automata.insertRow(fila_idx)
        self._llenar_fila(fila_idx, dato)
        self.tabla_automata.scrollToBottom()

    def limpiar(self):
        self.tabla_automata.setRowCount(0)

    # --------------------------------------------------------------------
    # Interno: coloca los valores de una fila, aplicando los marcadores
    # "→" (estado inicial) y "◎" (estado de aceptacion).
    # --------------------------------------------------------------------
    def _llenar_fila(self, fila_idx: int, dato: dict):
        paso = dato.get("paso", fila_idx)
        estado_actual = str(dato.get("estado_actual", ""))
        lee = str(dato.get("lee", "—"))
        transicion = str(dato.get("transicion", "—"))
        nuevo_estado = str(dato.get("nuevo_estado", ""))
        explicacion = str(dato.get("explicacion", ""))

        marca_inicio = dato.get("inicio", paso in (0, "0"))
        marca_aceptacion = dato.get("aceptacion", "acept" in explicacion.lower())

        if marca_inicio:
            estado_actual = f"→ {estado_actual}"
        if marca_aceptacion:
            nuevo_estado = f"◎ {nuevo_estado}"

        valores = (str(paso), estado_actual, lee, transicion, nuevo_estado, explicacion)
        for columna, valor in enumerate(valores):
            item = QTableWidgetItem(valor)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_automata.setItem(fila_idx, columna, item)
