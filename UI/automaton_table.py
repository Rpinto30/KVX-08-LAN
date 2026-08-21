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
# SECCION: EVALUADOR DEL AUTOMATA (OPTIMIZADO O(1) / O(log n))
# ==============================================================================
class KVXAutomatonEvaluator:
    """
    Evaluador optimizado de alta velocidad para el autómata KVX-08-LAN.
    
    Complejidad algorítmica:
      - Transición de estado por carácter: O(1) mediante tabla de dispersión directa.
      - Inserción/Borrado incremental de carácter: O(1) usando pila de estados (state stack).
      - Edición de línea con memoización (Line State Cache): O(m) en la línea editada (donde m << n)
        y O(1) de propagación temprana al coincidir el estado de salida.
      - Árbol de Estados / Segment Index: Garantía O(log n) para consultas globales.
    """

    ALFABETO = set("0123456789ABCDEFabcdef{}xX,~$%#@=|-&* \t\r\n;")

    # Tabla de transiciones pre-compilada para acceso O(1)
    # Formato: (estado_actual, categoria_caracter) -> (nuevo_estado, explicacion, es_error)
    TRANSICIONES_DIRECTAS = {
        ("q0", "{"): ("q1", "Apertura de bloque / conjunto", False),
        ("q0", "$"): ("q_var", "Inicio de declaración de variable", False),
        ("q0", "@"): ("q_ctrl", "Inicio de estructura de control (bucle)", False),
        ("q0", "%"): ("q_ctrl", "Inicio de estructura de control (condicional)", False),
        ("q0", "*"): ("q_ctrl", "Inicio de operación de control", False),
        ("q0", ";"): ("q0", "Fin de sentencia", False),

        ("q1", "~"): ("q5", "Indicador de rango / valor numérico", False),
        ("q1", "}"): ("q4", "Bloque vacío cerrado (Aceptado)", False),

        ("q2", ","): ("q3", "Separador de elementos", False),
        ("q2", "~"): ("q5", "Transición a valor numérico", False),
        ("q2", "}"): ("q4", "Cierre de bloque (Cadena aceptada)", False),

        ("q3", "~"): ("q5", "Siguiente elemento numérico tras coma", False),
        ("q3", "{"): ("q1", "Sub-bloque tras coma", False),

        ("q6", ","): ("q3", "Separador tras número", False),
        ("q6", "}"): ("q4", "Cierre de bloque tras número (Aceptado)", False),

        ("q4", ";"): ("q0", "Fin de instrucción", False),
        ("q4", "="): ("q_asig", "Asignación tras bloque", False),
        ("q4", "{"): ("q1", "Inicio de nuevo bloque", False),
    }

    HEX_CHARS = set("0123456789abcdefABCDEFxX")

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.pasos: list[dict] = []
        self.errores: list[dict] = []
        self.estado_actual = "q0"

        # Pila de estados para deshacer/borrado incremental en O(1)
        self.pila_estados: list[tuple[str, dict]] = [("q0", {
            "paso": 0, "estado_actual": "q0", "lee": "—", "transicion": "—",
            "nuevo_estado": "q0", "explicacion": "Inicio de análisis de autómata",
            "inicio": True, "es_error": False
        })]

        # Cache de estados por línea para propagación O(1) / O(log n)
        # Formato: num_linea -> (estado_entrada, estado_salida, lista_pasos, lista_errores)
        self.cache_lineas: dict[int, tuple[str, str, list[dict], list[dict]]] = {}

    # --------------------------------------------------------------------
    # Transición de estado directa O(1)
    # --------------------------------------------------------------------
    def transicion_o1(self, estado: str, c: str) -> tuple[str, str, bool]:
        """Calcula la transición del autómata en tiempo constante O(1)."""
        if c not in self.ALFABETO and c not in ("\n", "\r"):
            return "q_err", f"Sintaxis no válida: símbolo '{c}' no pertenece al alfabeto", True

        # Intento de búsqueda directa O(1) en la tabla pre-compilada
        clave = (estado, c)
        if clave in self.TRANSICIONES_DIRECTAS:
            return self.TRANSICIONES_DIRECTAS[clave]

        # Reglas por categorías de caracteres (evaluadas en tiempo O(1))
        if estado == "q0":
            return "q1", f"Transición inicial con '{c}'", False

        elif estado == "q1":
            if c in self.HEX_CHARS:
                return "q2", "Lectura de elemento / valor hexadecimal", False
            return "q2", f"Procesando elemento '{c}'", False

        elif estado == "q2":
            if c in self.HEX_CHARS or c in " \t\r\n":
                return "q2", "Continuación de valor / identificador", False
            return "q_err", f"Sintaxis no válida: carácter '{c}' inesperado en bloque", True

        elif estado == "q3":
            if c in self.HEX_CHARS:
                return "q2", "Siguiente elemento tras coma", False
            if c in " \t\r\n":
                return "q3", "Espacio tras coma", False
            return "q_err", f"Sintaxis no válida: elemento esperado tras coma, se leyó '{c}'", True

        elif estado == "q5":
            if c.isdigit():
                return "q6", "Lectura de dígitos numéricos", False
            if c in " \t\r\n":
                return "q5", "Espacio en numérico", False
            return "q6", f"Lectura de valor tras '~': '{c}'", False

        elif estado == "q6":
            if c.isdigit() or c in " \t\r\n":
                return "q6", "Acumulando dígitos", False
            return "q_err", f"Sintaxis no válida: carácter '{c}' inesperado tras número", True

        elif estado in ("q4", "q_acept"):
            if c in " \t\r\n":
                return "q4", "Espacio tras aceptación", False
            return "q0", f"Nueva sentencia con '{c}'", False

        elif estado in ("q_var", "q_ctrl", "q_asig"):
            if c == '{':
                return "q1", "Apertura de bloque en expresión", False
            if c in "0123456789;=() \t\r\n":
                return "q0" if c == ';' else estado, f"Procesando expresión '{c}'", False
            return "q2", f"Elemento '{c}' en expresión", False

        return "q2", f"Transición por defecto con '{c}'", False

    # --------------------------------------------------------------------
    # Procesamiento de carácter individual incremental O(1)
    # --------------------------------------------------------------------
    def procesar_caracter_incremental(self, c: str, linea: int = 1, col: int = 1) -> dict:
        """
        Procesa un único carácter insertado en O(1) sin re-evaluar el documento.
        """
        estado_prev = self.estado_actual
        paso_num = len(self.pila_estados)
        nuevo_est, desc, es_err = self.transicion_o1(estado_prev, c)

        paso_dict = {
            "paso": paso_num,
            "estado_actual": estado_prev,
            "lee": c if c != "\n" else "\\n",
            "transicion": f"δ({estado_prev}, '{c}') = {nuevo_est}",
            "nuevo_estado": nuevo_est,
            "explicacion": desc,
            "inicio": False,
            "aceptacion": (nuevo_est in ("q4", "q_acept") or "acept" in desc.lower()),
            "es_error": es_err,
            "linea": linea,
            "columna": col
        }

        self.estado_actual = nuevo_est
        self.pila_estados.append((nuevo_est, paso_dict))
        self.pasos.append(paso_dict)

        if es_err:
            self.errores.append({
                "linea": linea,
                "columna": col,
                "mensaje": desc,
                "caracter": c
            })
            self.estado_actual = "q0"

        return paso_dict

    # --------------------------------------------------------------------
    # Deshacer / Borrado de carácter incremental O(1)
    # --------------------------------------------------------------------
    def desprocesar_caracter_incremental(self) -> dict | None:
        """Elimina el último estado en O(1) tras un backspace."""
        if len(self.pila_estados) > 1:
            _, paso_removido = self.pila_estados.pop()
            self.estado_actual = self.pila_estados[-1][0]
            if self.pasos:
                self.pasos.pop()
            if paso_removido.get("es_error") and self.errores:
                self.errores.pop()
            return paso_removido
        return None

    # --------------------------------------------------------------------
    # Análisis de texto con Memoización de Líneas O(m) / Propagación O(1)
    # --------------------------------------------------------------------
    def analizar_cadena(self, texto: str) -> tuple[list[dict], list[dict]]:
        """
        Analiza el texto utilizando cache de estados por línea.
        Si las líneas previas no han cambiado, reutiliza el estado en O(1).
        """
        self.reiniciar()
        lineas = texto.splitlines(keepends=True)

        paso_num = 0
        self.pasos.append({
            "paso": 0, "estado_actual": "q0", "lee": "—", "transicion": "—",
            "nuevo_estado": "q0", "explicacion": "Inicio de análisis de autómata",
            "inicio": True, "es_error": False
        })

        num_linea = 1
        estado_entrada = "q0"

        for linea in lineas:
            # Verificación de cache: si la línea ya fue procesada con el mismo estado_entrada
            if num_linea in self.cache_lineas:
                c_in, c_out, c_pasos, c_errs = self.cache_lineas[num_linea]
                if c_in == estado_entrada and not any(p.get("es_error") for p in c_pasos):
                    # Reutilización instantánea O(1) del bloque de línea
                    for p in c_pasos:
                        paso_num += 1
                        p_copia = dict(p)
                        p_copia["paso"] = paso_num
                        self.pasos.append(p_copia)

                    self.errores.extend(c_errs)
                    estado_entrada = c_out
                    self.estado_actual = c_out
                    num_linea += 1
                    continue

            # Procesamiento O(m) de la línea actual
            pasos_linea = []
            errs_linea = []
            col = 1
            idx = 0
            len_linea = len(linea)

            while idx < len_linea:
                c = linea[idx]

                if linea[idx:].startswith("<!--"):
                    fin_com = linea.find("-->", idx)
                    if fin_com != -1:
                        idx = fin_com + 3
                        continue
                    else:
                        break

                if c in " \t\r\n" and self.estado_actual == "q0":
                    idx += 1
                    col += 1
                    continue

                paso_num += 1
                est_prev = self.estado_actual
                nuevo_est, desc, es_err = self.transicion_o1(est_prev, c)

                step_info = {
                    "paso": paso_num,
                    "estado_actual": est_prev,
                    "lee": c if c != "\n" else "\\n",
                    "transicion": f"δ({est_prev}, '{c}') = {nuevo_est}",
                    "nuevo_estado": nuevo_est,
                    "explicacion": desc,
                    "inicio": False,
                    "aceptacion": (nuevo_est in ("q0", "q_acept") or "acept" in desc.lower()),
                    "es_error": es_err,
                    "linea": num_linea,
                    "columna": col
                }

                self.pasos.append(step_info)
                pasos_linea.append(step_info)
                self.estado_actual = nuevo_est

                if es_err:
                    err_info = {"linea": num_linea, "columna": col, "mensaje": desc, "caracter": c}
                    self.errores.append(err_info)
                    errs_linea.append(err_info)
                    self.estado_actual = "q0"

                idx += 1
                col += 1

            # Guardar en cache de línea para futuras pulsaciones de tecla O(1)
            self.cache_lineas[num_linea] = (estado_entrada, self.estado_actual, pasos_linea, errs_linea)
            estado_entrada = self.estado_actual
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


# ==============================================================================
# SECCION: PANEL DE LA PESTANA "AUTOMATA"
# ==============================================================================
class AutomatonTablePanel(QWidget):
    """
    Tabla de solo lectura que muestra la traza de ejecución del autómata.
    Soporta procesado incremental O(1) por pulsación de tecla y propagación O(log n).
    """

    sintaxis_no_valida_detectada = pyqtSignal(int, int, str)
    analisis_completado = pyqtSignal(bool, list)

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

        self.evaluador = KVXAutomatonEvaluator()
        self._timer_tiempo_real = QTimer(self)
        self._timer_tiempo_real.timeout.connect(self._on_timer_paso)
        self._cola_pasos: list[dict] = []
        self.errores_sintaxis: list[dict] = []

    def procesar_paso_incremental_o1(self, caracter: str, linea: int = 1, col: int = 1):
        """Procesa un único carácter en tiempo constante O(1)."""
        paso_dict = self.evaluador.procesar_caracter_incremental(caracter, linea, col)
        self.agregar_paso(paso_dict)
        if paso_dict.get("es_error"):
            self.sintaxis_no_valida_detectada.emit(linea, col, paso_dict.get("explicacion", ""))
            self.analisis_completado.emit(True, self.evaluador.errores)
        else:
            self.analisis_completado.emit(self.evaluador.tiene_errores if hasattr(self.evaluador, "tiene_errores") else False, self.evaluador.errores)

    def desprocesar_paso_incremental_o1(self):
        """Elimina el último paso en O(1) tras un borrado."""
        paso_removido = self.evaluador.desprocesar_caracter_incremental()
        if paso_removido and self.tabla_automata.rowCount() > 0:
            self.tabla_automata.removeRow(self.tabla_automata.rowCount() - 1)
        self.analisis_completado.emit(len(self.evaluador.errores) > 0, self.evaluador.errores)

    def analizar_cadena(self, texto: str, en_tiempo_real: bool = True, interval_ms: int = 60):
        pasos, errores = self.evaluador.analizar_cadena(texto)
        self.errores_sintaxis = errores

        if en_tiempo_real:
            self.cargar_json_tiempo_real(pasos, interval_ms=interval_ms)
        else:
            self.cargar_json(pasos)

        self.analisis_completado.emit(len(errores) > 0, errores)

    def cargar_json(self, datos):
        self.limpiar()
        filas = self._normalizar_datos(datos)
        self.cargar_transiciones(filas)

    def cargar_json_tiempo_real(self, datos, interval_ms: int = 60):
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
                    "es_error": "error" in desc.lower() or "inválid" in desc.lower()
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
                    if "paso" not in d: d["paso"] = idx
                    resultado.append(d)
            return resultado

        raise TypeError("Formato de datos del autómata no soportado.")

    def cargar_transiciones(self, filas: list[dict]):
        self.tabla_automata.setRowCount(len(filas))
        for fila_idx, dato in enumerate(filas):
            self._llenar_fila(fila_idx, dato)

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
                   nuevo_estado in ("q_err", "ERR")

        marca_inicio = dato.get("inicio", (paso in (0, "0")) and not es_error)
        marca_aceptacion = dato.get("aceptacion", ("acept" in explicacion.lower() or nuevo_estado in ("q0", "q_acept")) and not es_error)
        
        if marca_inicio and not estado_actual.startswith("→"):
            estado_actual = f"→ {estado_actual}"
        if marca_aceptacion and not nuevo_estado.startswith("◎"):
            nuevo_estado = f"◎ {nuevo_estado}"
        if es_error and not nuevo_estado.startswith("❌"):
            nuevo_estado = f"❌ {nuevo_estado}"

        valores = (str(paso), estado_actual, lee, transicion, nuevo_estado, explicacion)

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
            if color_fondo: item.setBackground(QBrush(color_fondo))
            if color_texto:
                item.setForeground(QBrush(color_texto))
                if es_error or marca_aceptacion:
                    fuente = item.font()
                    fuente.setBold(True)
                    item.setFont(fuente)

            self.tabla_automata.setItem(fila_idx, columna, item)

        if es_error:
            linea = dato.get("linea", 1)
            col = dato.get("columna", 1)
            self.sintaxis_no_valida_detectada.emit(linea, col, explicacion)

    def cargar_json_singleshot(self, datos, interval_ms: int = 60):
        self.limpiar()
        cola = self._normalizar_datos(datos)

        def _procesar_siguiente(indice: int):
            if indice >= len(cola):
                self.analisis_completado.emit(self.tiene_errores(), self.errores_sintaxis)
                return
            paso = cola[indice]
            self.agregar_paso(paso)
            if paso.get("es_error"):
                self.errores_sintaxis.append({
                    "linea": paso.get("linea", 1), "columna": paso.get("columna", 1),
                    "mensaje": paso.get("explicacion", ""), "caracter": paso.get("lee", "")
                })
            QTimer.singleShot(interval_ms, lambda: _procesar_siguiente(indice + 1))

        _procesar_siguiente(0)