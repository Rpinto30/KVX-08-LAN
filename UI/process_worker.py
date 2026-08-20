from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import subprocess
import os


class ProcessWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, exe_path: str = './Automate/output.exe'):
        super().__init__()
        self.exe_path = exe_path
        self.process: subprocess.Popen | None = None

    @pyqtSlot()
    def start_process(self):
        self.process = subprocess.Popen(
            [self.exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            cwd=os.getcwd()
        )
        self.started.emit()

    @pyqtSlot(str)
    def write(self, command: str):
        if self.process is None or self.process.poll() is not None:
            return
        if not command.endswith('\n'):
            command += '\n'
        try:
            self.process.stdin.write(command)
            self.process.stdin.flush()
        except OSError:
            pass
        
        try:
            print(self.process.stdout.read())
        except:
            pass
    
    @pyqtSlot()
    def cout(self):
        try:
            print("COUT<< ",self.process.stdout.read())
        except:
            pass
        
        try:
            print("CERR<< ",self.process.stderr.read())
        except:
            pass
        

    @pyqtSlot()
    def stop_process(self):
        self.write('@')
        if self.process:
            self.process.stdin.close()
            self.process.wait()
        self.finished.emit()
        

from generador_estados import gen_all, generar_diagramas
class ProcessDrawer(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    on_draw = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.RUTA_JSON = "./Automate/result/result_automate.json"
        self.CARPETA_DIAGRAMAS = "./Diagramas"
        self.creating_image = False

    @pyqtSlot()
    def start_process(self):
        self.creating_image = True
        self.started.emit()
        
        try:
            
            for mensaje in gen_all(self.RUTA_JSON, self.CARPETA_DIAGRAMAS):
                print(mensaje)          
                self.on_draw.emit(mensaje)
        finally:
            self.stop_process()

    @pyqtSlot()
    def generate(self):
        self.creating_image = True
        try:
            generar_diagramas(self.RUTA_JSON, self.CARPETA_DIAGRAMAS)
        finally:
            self.stop_process()

    @pyqtSlot()
    def stop_process(self):
        self.creating_image = False
        self.finished.emit()