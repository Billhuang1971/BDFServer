from PyQt5.QtCore import QThread
import time


class runThread(QThread):
    def __init__(self, optimize, build, saveData):
        super(runThread, self).__init__()
        self.optimize = optimize
        self.build = build
        self.saveData = saveData

    def run(self):
        self.optimize()
        self.build()
        self.saveData()
