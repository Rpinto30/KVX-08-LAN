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

    @pyqtSlot()
    def stop_process(self):
        self.write('@')
        if self.process:
            self.process.stdin.close()
            self.process.wait()
        self.finished.emit()