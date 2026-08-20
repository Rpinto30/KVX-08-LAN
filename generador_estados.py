import json
import subprocess
import os

GRAFICOS_DIR = {
    1:"assing_variables.dot",
    2:"comments.dot",
    3:"conditions.dot",
    4:"loops.dot",
    5:"string_conditions.dot",
    6:"strings.dot",
    7:"variables.dot",
    8:"",
}

RUTA_JSON = "Automate/result/result_automate.json"
CARPETA_DIAGRAMAS = "Diagramas" 

CARPETA_SALIDA = r"Automate\result\diagramas"
CARPETA_ENTRADA = r"Diagramas"

def __read_json(ruta_json) -> dict:
   
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    if not os.path.exists(ruta_json):
        print("Error: No se encontro el JSON")
        return
        
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as e:
        print(f"Error leyendo el JSON: {e}")
        return
    return datos

def gen_all(ruta_json, carpeta_base_dot):
    datos = __read_json(ruta_json)
    if not datos: return
    
    diagramas_memoria = {}
    for j in range(1, 8):
        nombre_archivo = GRAFICOS_DIR[j]
        ruta = os.path.join(carpeta_base_dot, nombre_archivo)
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                diagramas_memoria[nombre_archivo] = f.read()
    
    for nombre_archivo, dot_base in diagramas_memoria.items():
        nombre_diagrama = nombre_archivo.replace('.dot', '')
        
        nombre_base_out = f"{nombre_diagrama}"
        ruta_dot_salida = os.path.join(CARPETA_ENTRADA, f"{nombre_base_out}.dot")
        ruta_png_out = os.path.join(CARPETA_SALIDA, f"{nombre_base_out}.png")
        try:
            subprocess.run(["dot", "-Tpng", ruta_dot_salida, "-o", ruta_png_out], check=True)
            print(f"")
            yield f"> Grafico {nombre_base_out}.png ha sido generado!"
            #os.remove(ruta_dot_salida)
        except subprocess.CalledProcessError as e:
            print(f"Error en {nombre_archivo}: {e}")
    
def generar_diagramas(ruta_json, carpeta_base_dot):
    datos = __read_json(ruta_json)
    if not datos: return
    
    transiciones = datos.get("transitions", [])
    if not transiciones and "actual_state" in datos:
        transiciones = [{"new_state": datos["actual_state"]}]

    diagramas_memoria = {}
    for j in range(1, 8):
        nombre_archivo = f"grafico{j}.dot"
        ruta = os.path.join(carpeta_base_dot, nombre_archivo)
        
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                diagramas_memoria[nombre_archivo] = f.read()

    mapeo_nodos = {
        100: "boolean", 
        101: "cadena"
    }
    
    for i, paso in enumerate(transiciones):
        estado_id = paso.get("new_state", 0)
        if estado_id == -1:
            print(f"Paso {i+1:}: Estado -1 (Error). Ignorado.")
            continue
        nombre_nodo = mapeo_nodos.get(estado_id, f"q{estado_id}")
        nodo_encontrado_global = False 
        for nombre_archivo, dot_base in diagramas_memoria.items():

            nodo_encontrado_en_este_archivo = False
            for linea in dot_base.splitlines():
                linea_limpia = linea.strip()
                if linea_limpia.startswith(f"{nombre_nodo} [") or linea_limpia.startswith(f"{nombre_nodo}["):
                    nodo_encontrado_en_este_archivo = True
                    break             
            if nodo_encontrado_en_este_archivo:
                nodo_encontrado_global = True
                nombre_diagrama = nombre_archivo.replace('.dot', '')
                
                nombre_base_out = f"{nombre_diagrama}"
                ruta_dot_salida = os.path.join(CARPETA_SALIDA, f"{nombre_base_out}.dot")
                ruta_png_out = os.path.join(CARPETA_SALIDA, f"{nombre_base_out}.png")
                
                insertar_color = f'\n    {nombre_nodo} [style="filled", fillcolor="#b3ffcc", color="#00C853", penwidth=3.5];\n}}'
                dot_modificado = dot_base.rpartition('}')[0] + insertar_color
                
                with open(ruta_dot_salida, "w", encoding="utf-8") as archivo:
                    archivo.write(dot_modificado)
                try:
                    subprocess.run(["dot", "-Tpng", ruta_dot_salida, "-o", ruta_png_out], check=True)
                    print(f"Paso {i+1}: {nombre_nodo} en {nombre_archivo}")
                    os.remove(ruta_dot_salida)
                except subprocess.CalledProcessError as e:
                    print(f"Error en {nombre_archivo}: {e}")
        if not nodo_encontrado_global:
            print(f"Paso {i+1}: Nodo {nombre_nodo} no existe en ningun diagrama.")


#if __name__ == "__main__":
#    
#    
#    gen_all(RUTA_JSON, CARPETA_DIAGRAMAS)