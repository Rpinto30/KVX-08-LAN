"""
==============================================================================
 PATCH: Panel de graficos (KVX-STATES) - generacion de animacion con Graphviz
 Integrar estas piezas en tu archivo principal del IDE.
==============================================================================
"""
import os
import json
import subprocess
 
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmapCache  # <-- faltaba este import
 
 
# ==============================================================================
# 1) CONSTANTES DE RUTAS (agregar a nivel de modulo, junto a los otros imports)
# ==============================================================================
CARPETA_DOT = "../Diagramas"
CARPETA_SALIDA = "../Automate/result/diagramas"
 
 
# ==============================================================================
# 2) WORKER EN SEGUNDO PLANO (agregar como clase nueva, junto a ProcessDrawer)
#    No bloquea la UI: cada paso corre en el hilo del worker, no en el hilo
#    principal.
# ==============================================================================
class DiagramAnimationWorker(QThread):
    # nombre_diagrama, ruta_png -> para refrescar el visor si aplica
    paso_generado = pyqtSignal(str, str)
    # numero_paso, mensaje de error
    paso_fallido = pyqtSignal(int, str)
    # texto para la consola KVX-LOG
    log = pyqtSignal(str)
    # se emite siempre al terminar (exito, error o detencion manual)
    terminado = pyqtSignal()
 
    def __init__(self, ruta_json, modulo_diagramas, mapeo_nodos,
                 carpeta_salida=CARPETA_SALIDA, delay_ms=800, parent=None):
        super().__init__(parent)
        self.ruta_json = ruta_json
        self.modulo_diagramas = modulo_diagramas  # dict idx -> (nombre, ruta_dot, ruta_png)
        self.mapeo_nodos = mapeo_nodos
        self.carpeta_salida = carpeta_salida
        self.delay_ms = delay_ms
        self._detener = False
 
    def solicitar_detener(self):
        self._detener = True
 
    # -- lectura segura de JSON (reemplaza al inexistente self.__read_json) --
    @staticmethod
    def _leer_json(ruta):
        if not ruta or not os.path.exists(ruta):
            return {}
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
 
    def run(self):
        datos = self._leer_json(self.ruta_json)
        if not datos:
            self.log.emit("> [Gen] No se encontraron datos en el JSON de traza.")
            self.terminado.emit()
            return
 
        transiciones = datos.get("transitions", [])
        if not transiciones and "actual_state" in datos:
            transiciones = [{"new_state": datos["actual_state"]}]
 
        if not transiciones:
            self.log.emit("> [Gen] La traza no contiene transiciones.")
            self.terminado.emit()
            return
 
        # Precargar el contenido de cada diagrama .dot una sola vez
        diagramas = {}
        for idx, (nombre, ruta_dot, ruta_png) in self.modulo_diagramas.items():
            if not os.path.exists(ruta_dot):
                self.log.emit(f"> [Gen] Aviso: no existe {ruta_dot}, se omite '{nombre}'.")
                continue
            with open(ruta_dot, "r", encoding="utf-8") as f:
                contenido = f.read()
            diagramas[idx] = {
                "nombre": nombre,
                "ruta_dot": ruta_dot,
                "ruta_png": ruta_png,
                "contenido": contenido,
                "lineas": [linea.strip() for linea in contenido.splitlines()],
            }
 
        os.makedirs(self.carpeta_salida, exist_ok=True)
 
        for i, paso in enumerate(transiciones):
            if self._detener:
                self.log.emit("> [Gen] Animacion detenida por el usuario.")
                break
 
            estado_id = paso.get("new_state", 0)
            caracter = paso.get("char", "")
            numero_paso = paso.get("no", i)
 
            if estado_id == -1:
                self.log.emit(f"> [Gen] Paso {numero_paso} ('{caracter}'): estado -1 (error), se omite.")
                continue
 
            nombre_nodo = self.mapeo_nodos.get(estado_id, f"q{estado_id}")
            encontrado = False
 
            for diag in diagramas.values():
                nodo_presente = any(
                    linea.startswith(f"{nombre_nodo} [") or linea.startswith(f"{nombre_nodo}[")
                    for linea in diag["lineas"]
                )
                if not nodo_presente:
                    continue
 
                encontrado = True
                ruta_dot_tmp = os.path.join(self.carpeta_salida, f"{diag['nombre']}_tmp.dot")
                ruta_png_out = diag["ruta_png"]  # se sobreescribe siempre -> efecto animacion
 
                # Asegura que la carpeta destino de ESTA imagen exista,
                # sin depender de que coincida con self.carpeta_salida.
                carpeta_destino = os.path.dirname(ruta_png_out) or "."
                try:
                    os.makedirs(carpeta_destino, exist_ok=True)
                except OSError as error:
                    self.paso_fallido.emit(
                        numero_paso, f"No se pudo crear la carpeta '{carpeta_destino}': {error}"
                    )
                    continue
 
                resaltado = (
                    f'\n    {nombre_nodo} [style="filled", fillcolor="#b3ffcc", '
                    f'color="#00C853", penwidth=3.5];\n}}'
                )
                dot_modificado = diag["contenido"].rpartition("}")[0] + resaltado
 
                try:
                    with open(ruta_dot_tmp, "w", encoding="utf-8") as f_out:
                        f_out.write(dot_modificado)
                    subprocess.run(
                        ["dot", "-Tpng", ruta_dot_tmp, "-o", ruta_png_out],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    self.log.emit(
                        f"> [Gen] Paso {numero_paso} ('{caracter}'): nodo '{nombre_nodo}' "
                        f"resaltado en {diag['nombre']}.png"
                    )
                    self.paso_generado.emit(diag["nombre"], ruta_png_out)
                except subprocess.CalledProcessError as error:
                    # error.stderr trae el mensaje real de Graphviz (ej. permission denied,
                    # carpeta inexistente, dot.exe no encontrado en PATH, etc.)
                    detalle = error.stderr.strip() if error.stderr else str(error)
                    self.paso_fallido.emit(numero_paso, f"{detalle} (ruta: {ruta_png_out})")
                except OSError as error:
                    self.paso_fallido.emit(numero_paso, f"{error} (ruta: {ruta_png_out})")
                finally:
                    if os.path.exists(ruta_dot_tmp):
                        os.remove(ruta_dot_tmp)
 
            if not encontrado:
                self.log.emit(
                    f"> [Gen] Paso {numero_paso} ('{caracter}'): nodo '{nombre_nodo}' "
                    f"no existe en ningun diagrama."
                )
 
            self.msleep(self.delay_ms)
 
        self.terminado.emit()
 

