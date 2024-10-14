from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QStandardItemModel


class Ui_MainWindow(object):
    def __init__(self, vsys, vapp, serverApp):
        self.sys0 = vsys
        self.app0 = vapp
        self.tab_cur_row = 1
        self.tab_model = serverApp.server.tabV_model
        self.server = serverApp.server

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(655, 450)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(0, 0, 241, 41))
        self.groupBox.setObjectName("groupBox")
        self.pB_start = QtWidgets.QPushButton(self.groupBox)
        self.pB_start.setGeometry(QtCore.QRect(80, 11, 61, 23))
        self.pB_start.setObjectName("pB_start")
        self.pB_close = QtWidgets.QPushButton(self.groupBox)
        self.pB_close.setGeometry(QtCore.QRect(157, 11, 71, 23))
        self.pB_close.setObjectName("pB_close")
        self.pB_exit = QtWidgets.QPushButton(self.centralwidget)
        self.pB_exit.setGeometry(QtCore.QRect(560, 10, 75, 23))
        self.pB_exit.setObjectName("pB_exit")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 50, 621, 351))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabV_tip = QtWidgets.QTableView(self.verticalLayoutWidget)
        self.tabV_tip.setObjectName("tabV_tip")
        self.verticalLayout.addWidget(self.tabV_tip)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 655, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # 设置数据层次结构，4行4列
        #self.tab_model = QStandardItemModel(0, 5)

        self.retranslateUi(MainWindow)
        self.pB_start.clicked.connect(self.pB_start_click) # type: ignore
        self.pB_close.clicked.connect(self.pB_close_click) # type: ignore
        self.pB_exit.clicked.connect(self.pB_exit_click) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.pB_close.setEnabled(False)


    def pB_start_click(self):
        self.tab_model.setHorizontalHeaderLabels(['时      间', '用户', '操作', '备注1', '备注2'])
        self.tabV_tip.setModel(self.tab_model)
        self.tabV_tip.setColumnWidth(0, 140)
        self.tabV_tip.setColumnWidth(1, 48)
        self.tabV_tip.setColumnWidth(2, 160)
        self.tabV_tip.setColumnWidth(3, 140)
        self.tabV_tip.setColumnWidth(4, 110)

        self.pB_close.setEnabled(True)
        self.pB_start.setEnabled(False)
        self.pB_exit.setEnabled(False)

        self.server.sockServerStart()

    def pB_close_click(self):
         self.tab_model.clear()
         self.tab_model.setHorizontalHeaderLabels(['时      间', '用户', '操作', '备注1', '备注2'])
         self.tab_model.removeRow(1)
         self.pB_start.setEnabled(True)
         self.pB_exit.setEnabled(True)
         self.pB_close.setEnabled(False)
         self.server.sockServerClose()

    def pB_exit_click(self):
        self.sys0.exit(self.app0.exec_())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "我的服务器"))
        self.groupBox.setTitle(_translate("MainWindow", "我的服务器"))
        self.pB_start.setText(_translate("MainWindow", "启  动"))
        self.pB_close.setText(_translate("MainWindow", "退 出"))
        self.pB_exit.setText(_translate("MainWindow", "关闭"))
        #self.pB_start_click()