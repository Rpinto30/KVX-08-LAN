from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import subprocess
import os
import threading

class ProcessWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    cout = pyqtSignal(str, str)

    def __init__(self, exe_path: str = './Automate/output.exe'):
        super().__init__()
        self.exe_path = exe_path
        self.process: subprocess.Popen | None = None

    @pyqtSlot()
    def start_process(self):
        self.process = subprocess.Popen(
            [self.exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            cwd=os.getcwd()
        )
        self.started.emit()
        
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in iter(self.process.stdout.readline, ''):
            if line:
                if line.strip() != "":
                    print(f"COUT<< {line.strip()}")
        self.process.stdout.close()

    def _read_stderr(self):
        for line in iter(self.process.stderr.readline, ''):
            if line:
                if line.strip() != "":
                    print(f"CERR<< {line.strip()}")
        self.process.stderr.close()

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
        

