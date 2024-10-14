import sys
import serverMain

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from util.curUser import curUser
from util.appUtil import appUtil
from util.dbUtil import dbUtil
from service.server import server


class serverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.dbUtil = dbUtil()
        self.appUtil = appUtil(self.dbUtil)
        self.curUser = curUser(self.appUtil, self.dbUtil)
        s_ip, s_port = self.appUtil.GetSocketIpFile()
        self.server = server(s_ip, s_port, self.dbUtil, self.appUtil, self.curUser)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    a = serverApp()

    mainWindow = QMainWindow()

    ui = serverMain.Ui_MainWindow(sys, app, a)

    ui.setupUi(mainWindow)

    mainWindow.show()

    sys.exit(app.exec_())
