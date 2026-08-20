import json
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush


# ==============================================================================
# SECCION: EVALUADOR Y SIMULADOR DEL AUTOMATA (AFD / AFND KVX)
# ==============================================================================
class KVXAutomatonEvaluator:
    """
    Evaluador y generador de trazas para el autómata KVX-08-LAN.
    Analiza cadenas de entrada, genera las transiciones paso a paso
    y detecta sintaxis no válida o errores sintácticos.
    """

    ALFABETO = set("0123456789ABCDEFabcdef{}xX,~$%#@=|-&* \t\r\n;")

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.pasos = []
        self.errores = []
        self.estado_actual = "q0"

    def analizar_cadena(self, texto: str) -> tuple[list[dict], list[dict]]:
        """
        Analiza el texto de entrada caracter a caracter o linea a linea
        retornando (lista_pasos_dict, lista_errores_dict).
        """
        self.reiniciar()
        paso_num = 0

        # Paso inicial
        self.pasos.append({
            "paso": paso_num,
            "estado_actual": "q0",
            "lee": "—",
            "transicion": "—",
            "nuevo_estado": "q0",
            "explicacion": "Inicio de análisis de autómata",
            "inicio": True,
            "es_error": False
        })

        lineas = texto.splitlines(keepends=True)
        num_linea = 1

        for linea in lineas:
            col = 1
            idx = 0
            len_linea = len(linea)

            while idx < len_linea:
                c = linea[idx]

                # Ignorar comentarios <!-- ... -->
                if linea[idx:].startswith("<!--"):
                    fin_com = linea.find("-->", idx)
                    if fin_com != -1:
                        idx = fin_com + 3
                        continue
                    else:
                        break

                # Ignorar espacios si estamos en q0
                if c in " \t\r\n" and self.estado_actual == "q0":
                    idx += 1
                    col += 1
                    continue

                paso_num += 1
                estado_previo = self.estado_actual
                nuevo_est, explicacion, es_err = self._transicion(c)

                trans_str = f"δ({estado_previo}, '{c}') = {nuevo_est}"

                step_info = {
                    "paso": paso_num,
                    "estado_actual": estado_previo,
                    "lee": c if c != "\n" else "\\n",
                    "transicion": trans_str,
                    "nuevo_estado": nuevo_est,
                    "explicacion": explicacion,
                    "inicio": False,
                    "aceptacion": (nuevo_est in ("q4", "q_acept") or "acept" in explicacion.lower()),
                    "es_error": es_err,
                    "linea": num_linea,
                    "columna": col
                }

                self.pasos.append(step_info)
                self.estado_actual = nuevo_est

                if es_err:
                    self.errores.append({
                        "linea": num_linea,
                        "columna": col,
                        "mensaje": explicacion,
                        "caracter": c
                    })
                    # Recuperación básica tras error
                    self.estado_actual = "q0"

                idx += 1
                col += 1

            num_linea += 1

        # Verificación final
        if self.estado_actual not in ("q0", "q4", "q_acept") and not self.errores:
            paso_num += 1
            self.pasos.append({
                "paso": paso_num,
                "estado_actual": self.estado_actual,
                "lee": "EOF",
                "transicion": "ERROR_FIN",
                "nuevo_estado": "q_err",
                "explicacion": f"Sintaxis no válida: cadena incompleta en estado {self.estado_actual}",
                "es_error": True,
                "linea": num_linea - 1,
                "columna": 1
            })

        return self.pasos, self.errores

    def _transicion(self, c: str) -> tuple[str, str, bool]:
        if c not in self.ALFABETO and c not in ("\n", "\r"):
            return "q_err", f"Sintaxis no válida: símbolo '{c}' no pertenece al alfabeto", True

        q = self.estado_actual

        if q == "q0":
            if c == '{':
                return "q1", "Apertura de bloque / conjunto", False
            elif c == '$':
                return "q_var", "Inicio de declaración de variable", False
            elif c in ("@", "%", "*"):
                return "q_ctrl", "Inicio de estructura de control", False
            elif c == ';':
                return "q0", "Fin de sentencia", False
            else:
                return "q1", f"Transición inicial con '{c}'", False

        elif q == "q1":
            if c == '~':
                return "q5", "Indicador de rango / valor numérico", False
            elif c in "0123456789abcdefABCDEFxX":
                return "q2", "Lectura de elemento / valor hexadecimal", False
            elif c == '}':
                return "q4", "Bloque vacío cerrado (Aceptado)", False
            else:
                return "q2", f"Procesando elemento '{c}'", False

        elif q == "q2":
            if c in "0123456789abcdefABCDEFxX":
                return "q2", "Continuación de valor / identificador", False
            elif c == ',':
                return "q3", "Separador de elementos", False
            elif c == '~':
                return "q5", "Transición a valor numérico", False
            elif c == '}':
                return "q4", "Cierre de bloque (Cadena aceptada)", False
            elif c in " \t\r\n":
                return "q2", "Espacio en bloque", False
            else:
                return "q_err", f"Sintaxis no válida: carácter '{c}' inesperado en bloque", True

        elif q == "q3":
            if c in "0123456789abcdefABCDEFxX":
                return "q2", "Siguiente elemento tras coma", False
            elif c == '~':
                return "q5", "Siguiente elemento numérico tras coma", False
            elif c == '{':
                return "q1", "Sub-bloque tras coma", False
            elif c in " \t\r\n":
                return "q3", "Espacio tras coma", False
            else:
                return "q_err", f"Sintaxis no válida: elemento esperado tras coma, se leyó '{c}'", True

        elif q == "q5":
            if c.isdigit():
                return "q6", "Lectura de dígitos numéricos", False
            elif c in " \t\r\n":
                return "q5", "Espacio en numérico", False
            else:
                return "q6", f"Lectura de valor tras '~': '{c}'", False

        elif q == "q6":
            if c.isdigit():
                return "q6", "Acumulando dígitos", False
            elif c == ',':
                return "q3", "Separador tras número", False
            elif c == '}':
                return "q4", "Cierre de bloque tras número (Aceptado)", False
            elif c in " \t\r\n":
                return "q6", "Espacio tras número", False
            else:
                return "q_err", f"Sintaxis no válida: carácter '{c}' inesperado tras número", True

        elif q in ("q4", "q_acept"):
            if c == ';':
                return "q0", "Fin de instrucción", False
            elif c == '=':
                return "q_asig", "Asignación tras bloque", False
            elif c in " \t\r\n":
                return "q4", "Espacio tras aceptación", False
            elif c == '{':
                return "q1", "Inicio de nuevo bloque", False
            else:
                return "q0", f"Nueva sentencia con '{c}'", False

        elif q in ("q_var", "q_ctrl", "q_asig"):
            if c == '{':
                return "q1", "Apertura de bloque en expresión", False
            elif c in "0123456789;=() \t\r\n":
                return "q0" if c == ';' else q, f"Procesando expresión '{c}'", False
            else:
                return "q2", f"Elemento '{c}' en expresión", False

        return "q2", f"Transición por defecto con '{c}'", False


# ==============================================================================
# SECCION: PANEL DE LA PESTANA "AUTOMATA"
# Tabla de solo lectura con la traza de transiciones del autómata
# ==============================================================================
class AutomatonTablePanel(QWidget):
    """
    Tabla de solo lectura que muestra la traza de ejecución del autómata
    (una fila por paso). Soporta:
      - Carga de JSON estándar o formato del compilador C++ (transitions/error).
      - Visualización paso a paso en tiempo real mediante QTimer.
      - Resaltado visual en rojo de sintaxis no válida o errores.
      - Emisión de señales para que el editor subraye sintaxis no válida.
    """

    sintaxis_no_valida_detectada = pyqtSignal(int, int, str)  # linea, col, mensaje
    analisis_completado = pyqtSignal(bool, list)             # tiene_errores, lista_errores

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

        # Evaluador de autómata interno
        self.evaluador = KVXAutomatonEvaluator()

        # Timer para animación / traza en tiempo real
        self._timer_tiempo_real = QTimer(self)
        self._timer_tiempo_real.timeout.connect(self._on_timer_paso)
        self._cola_pasos: list[dict] = []

        # Registro de errores de sintaxis
        self.errores_sintaxis: list[dict] = []

    # --------------------------------------------------------------------
    # API publica: analiza un texto directamente con el autómata
    # --------------------------------------------------------------------
    def analizar_cadena(self, texto: str, en_tiempo_real: bool = True, interval_ms: int = 60):
        pasos, errores = self.evaluador.analizar_cadena(texto)
        self.errores_sintaxis = errores

        if en_tiempo_real:
            self.cargar_json_tiempo_real(pasos, interval_ms=interval_ms)
        else:
            self.cargar_json(pasos)

        has_err = len(errores) > 0
        self.analisis_completado.emit(has_err, errores)

    def cargar_json(self, datos):
        self.limpiar()
        filas = self._normalizar_datos(datos)
        self.cargar_transiciones(filas)

    def cargar_json_tiempo_real(self, datos, interval_ms: int = 60):
        """
        Muestra cada paso progresivamente en la tabla con un intervalo de tiempo.
        """
        self.limpiar()
        self._cola_pasos = self._normalizar_datos(datos)
        self._timer_tiempo_real.stop()
        self._timer_tiempo_real.setInterval(max(10, interval_ms))
        self._timer_tiempo_real.start()

    def _on_timer_paso(self):
        if not self._cola_pasos:
            self._timer_tiempo_real.stop()
            return
        paso = self._cola_pasos.pop(0)
        self.agregar_paso(paso)

    def _normalizar_datos(self, datos) -> list[dict]:
        if isinstance(datos, (str, Path)):
            texto = str(datos)
            ruta = Path(texto)
            if ruta.suffix.lower() == ".json" and ruta.exists():
                texto = ruta.read_text(encoding="utf-8")
            elif not (texto.strip().startswith("{") or texto.strip().startswith("[")):
                # Es texto plano para analizar con autómata
                pasos, errs = self.evaluador.analizar_cadena(texto)
                self.errores_sintaxis = errs
                return pasos

            try:
                datos = json.loads(texto)
            except json.JSONDecodeError:
                pasos, errs = self.evaluador.analizar_cadena(texto)
                self.errores_sintaxis = errs
                return pasos

        if isinstance(datos, dict):
            transiciones_raw = datos.get("transitions", [])
            filas = []
            for t in transiciones_raw:
                paso_num = t.get("no", t.get("paso", len(filas)))
                act = str(t.get("actual_state", t.get("estado_actual", "q0")))
                sig = str(t.get("new_state", t.get("nuevo_estado", "q0")))
                if act.isdigit(): act = f"q{act}"
                if sig.isdigit(): sig = f"q{sig}"
                ch = str(t.get("char", t.get("lee", "—")))
                desc = str(t.get("description", t.get("explicacion", "")))

                filas.append({
                    "paso": paso_num,
                    "estado_actual": act,
                    "lee": ch,
                    "transicion": f"δ({act}, '{ch}') = {sig}",
                    "nuevo_estado": sig,
                    "explicacion": desc,
                    "es_error": "error" in desc.lower() or "inválid" in desc.lower() or "invalider" in desc.lower()
                })

            err = datos.get("error")
            if err:
                msg = err if isinstance(err, str) else json.dumps(err)
                filas.append({
                    "paso": len(filas),
                    "estado_actual": "q_err",
                    "lee": "-",
                    "transicion": "ERROR",
                    "nuevo_estado": "ERR",
                    "explicacion": f"Sintaxis no válida: {msg}",
                    "es_error": True
                })
            return filas

        if isinstance(datos, (list, tuple)):
            resultado = []
            for idx, item in enumerate(datos):
                if isinstance(item, dict):
                    d = dict(item)
                    if "paso" not in d:
                        d["paso"] = idx
                    resultado.append(d)
            return resultado

        raise TypeError("Formato de datos del autómata no soportado (se esperaba lista, dict, str o Path).")

    # --------------------------------------------------------------------
    # API publica: carga la tabla a partir de una lista de dicts ya lista
    # --------------------------------------------------------------------
    def cargar_transiciones(self, filas: list[dict]):
        self.tabla_automata.setRowCount(len(filas))
        for fila_idx, dato in enumerate(filas):
            self._llenar_fila(fila_idx, dato)

    # --------------------------------------------------------------------
    # API publica: agrega un solo paso al final (útil para traza en vivo)
    # --------------------------------------------------------------------
    def agregar_paso(self, dato: dict):
        fila_idx = self.tabla_automata.rowCount()
        self.tabla_automata.insertRow(fila_idx)
        self._llenar_fila(fila_idx, dato)
        self.tabla_automata.scrollToBottom()

    def limpiar(self):
        self._timer_tiempo_real.stop()
        self.tabla_automata.setRowCount(0)
        self.errores_sintaxis.clear()

    def obtener_errores_sintaxis(self) -> list[dict]:
        return list(self.errores_sintaxis)

    def tiene_errores(self) -> bool:
        return len(self.errores_sintaxis) > 0

    # --------------------------------------------------------------------
    # Interno: coloca los valores de una fila y aplica estilos visuales
    # según el tipo de estado (inicio, error de sintaxis, aceptación).
    # --------------------------------------------------------------------
    def _llenar_fila(self, fila_idx: int, dato: dict):
        paso = dato.get("paso", fila_idx)
        estado_actual = str(dato.get("estado_actual", ""))
        lee = str(dato.get("lee", "—"))
        transicion = str(dato.get("transicion", "—"))
        nuevo_estado = str(dato.get("nuevo_estado", ""))
        explicacion = str(dato.get("explicacion", ""))

        es_error = dato.get("es_error", False) or \
                   "error" in explicacion.lower() or \
                   "inválid" in explicacion.lower() or \
                   "no válid" in explicacion.lower() or \
                   nuevo_estado in ("q_err", "ERR")

        marca_inicio = dato.get("inicio", (paso in (0, "0")) and not es_error)
        marca_aceptacion = dato.get("aceptacion", ("acept" in explicacion.lower() or nuevo_estado in ("q4", "q_acept")) and not es_error)

        if marca_inicio and not estado_actual.startswith("→"):
            estado_actual = f"→ {estado_actual}"
        if marca_aceptacion and not nuevo_estado.startswith("◎"):
            nuevo_estado = f"◎ {nuevo_estado}"
        if es_error and not nuevo_estado.startswith("❌"):
            nuevo_estado = f"❌ {nuevo_estado}"

        valores = (str(paso), estado_actual, lee, transicion, nuevo_estado, explicacion)

        # Colores según tipo de fila
        if es_error:
            color_fondo = QColor("#4a1414")
            color_texto = QColor("#ff8888")
        elif marca_aceptacion:
            color_fondo = QColor("#143a1a")
            color_texto = QColor("#66ff88")
        else:
            color_fondo = None
            color_texto = None

        for columna, valor in enumerate(valores):
            item = QTableWidgetItem(valor)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if color_fondo:
                item.setBackground(QBrush(color_fondo))
            if color_texto:
                item.setForeground(QBrush(color_texto))
                if es_error or marca_aceptacion:
                    fuente = item.font()
                    fuente.setBold(True)
                    item.setFont(fuente)

            self.tabla_automata.setItem(fila_idx, columna, item)

        # Si es error y contiene información de línea/columna, emitir señal
        if es_error:
            linea = dato.get("linea", 1)
            col = dato.get("columna", 1)
            self.sintaxis_no_valida_detectada.emit(linea, col, explicacion)

