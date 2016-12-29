#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import threading

import time

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QHBoxLayout, QPushButton, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
import pyexcel
from coral import Coral
from selenium import webdriver
import pickle
import os


# 用来存储关键数据，实时写入本地，防止程序意外退出数据丢失
# !!!!!!!!!!!!!!如果修改内部变量的结构，换成不会更新，会造成不存在变量的问题!!!!!!!!!!!!!!!!
class Storage:
    def __init__(self):
        self.lastComments = []  # 存储导入的数据
        self.lastTimes = [] # 存储时间
        self.lastOpenFilePath = '/'  # 上一次打开的文件路径
        self.lastOpenFile = '' # 上一次打开的文件


# 发表评论的线程
class WorldThread(QThread):
    # 结束信号
    finishSignal = pyqtSignal(list)
    # 发送消息信号
    statusBarSignal = pyqtSignal(str)
    # 弹出框的消息
    messageBoxSignal = pyqtSignal(str)

    def __init__(self, comments, wait_time):
        super().__init__()
        self.comments = comments
        self.wait_time = int(wait_time)

    def run(self):
        try:
            self.statusBarSignal.emit('正在启动浏览器(时间较长请耐心等待)......')
            # 创建一个浏览器实例
            profileDir = r"C:\Users\zero\AppData\Roaming\Mozilla\Firefox\Profiles\qx6b4mkb.selenium"
            driver = webdriver.Firefox(profileDir)

            self.statusBarSignal.emit('启动成功')
            lastQQ = 0  # 记录上一次的QQ号
            sendTime = []  # 发送时间
            for data in self.comments:
                if not 'url' in data:
                    break
                # 检查是否更换QQ号，若更换的话重新登录
                if lastQQ == 0:
                    lastQQ = data['QQ号码']
                elif lastQQ != data['QQ号码']:
                    coral.logout()
                    lastQQ = data['QQ号码']
                coral = Coral(driver, data['url'])
                coral.open_brower()
                if not coral.check_login():
                    if not coral.login(username=data['QQ号码']):
                        '''
                        这里处理登录失败的情况存在问题，后期处理
                        '''
                        self.messageBoxSignal.emit('登录失败，请重新开始!')
                # 发送评论
                coral.send_comment(data['引导内容'])
                # 记录时间
                sendTime.append(time.strftime('%Y-%m-%d %H:%M'))
                # 发送提示
                self.statusBarSignal.emit('【' + data['QQ号码'] + '】---【' + data['视频标题'] + '】评论成功！')
                # 等待一段时间再进行下一个
                time.sleep(self.wait_time)
            driver.quit()
            # 运行完发送一个信号告诉主线程窗口
            self.finishSignal.emit(sendTime)
        except Exception as e:
            print('报错啦', e)
            print(data)
            driver.quit()

# 导入文件的线程
class ImportThread(QThread):
    def __init__(self):
        pass

    def run(self):
        pass

class Main_Ui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        # 表示性的属性
        self.IMPORTED = False  # 是否导入
        self.START_CORAL = False  # 是否开始发表
        # 本地存储的数据
        self.preferencesFileName = 'preferences.data' #本地存储文件名称
        self.preferences = self.loadPreferences()

    def initUI(self):
        self.initMenu()
        self.initToolbar()
        self.statusBar()

        self.buttonStart = QPushButton('开始')
        self.buttonStart.clicked.connect(self.startWork)
        self.lableWait = QLabel(text='评论间隔:')
        self.lableSec = QLabel(text='秒')
        self.spinboxTime = QSpinBox(value=5)
        self.spinboxTime.setRange(0, 120)
        hbox = QHBoxLayout()
        hbox.addWidget(self.buttonStart)
        hbox.addWidget(self.lableWait)
        hbox.addWidget(self.spinboxTime)
        hbox.addWidget(self.lableSec)
        hbox.addStretch()

        self.tableComments = QTableWidget()
        self.tableComments.setColumnCount(5)
        self.tableComments.setRowCount(20)
        self.tableComments.setHorizontalHeaderLabels([
            'QQ号码', '视频标题', '评论内容', '引导时间', '状态'
        ])
        # 自适应宽度
        self.tableComments.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 禁止编辑
        self.tableComments.setEditTriggers(QAbstractItemView.NoEditTriggers)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tableComments)

        self.centerWidget = QWidget()
        self.centerWidget.setLayout(vbox)
        self.setCentralWidget(self.centerWidget)

        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        self.setGeometry(300, 100, 700, 450)
        self.setWindowTitle('极速评论')
        self.show()

    # 创建菜单栏
    def initMenu(self):
        self.accountMenu = self.menuBar().addMenu("&账号")
        self.accountAction = QAction(QIcon(), "&张玉腾", self, triggered=self.doAction)
        self.accountMenu.addAction(self.accountAction)
        self.quitAccountAction = QAction(QIcon(), "&退出", self, triggered=self.doAction)
        self.accountMenu.addAction(self.quitAccountAction)
        self.fileMenu = self.menuBar().addMenu("&文件")
        self.importAction = QAction(QIcon(), "&导入", self, triggered=self.importDialog)
        self.fileMenu.addAction(self.importAction)
        self.exportAction = QAction(QIcon(), "&导出", self, triggered=self.exportDialog)
        self.fileMenu.addAction(self.exportAction)
        self.settingMenu = self.menuBar().addMenu("&设置")
        self.manageQQAction = QAction(QIcon(), "&QQ号管理", self, triggered=self.doAction)
        self.settingMenu.addAction(self.manageQQAction)
        self.helpMenu = self.menuBar().addMenu("&帮助")
        self.checkUpdateAction = QAction(QIcon(), "&检查更新", self, triggered=self.doAction)
        self.helpMenu.addAction(self.checkUpdateAction)
        self.aboutAction = QAction(QIcon(), "&关于", self, triggered=self.doAction)
        self.helpMenu.addAction(self.aboutAction)

    # 创建工具栏
    def initToolbar(self):
        self.toolbar = self.addToolBar('often')
        self.toolbar.addAction(self.importAction)
        self.toolbar.addAction(self.exportAction)
        self.toolbar.addAction(self.manageQQAction)

    # 导入文件
    def importDialog(self):
        fname = QFileDialog.getOpenFileName(self, '选择作业(XLS)', self.preferences.lastOpenFilePath, '(*.xls *.xlsx)')
        if fname[0]:
            # 将本次的打开记录保存起来
            self.preferences.lastOpenFilePath, self.preferences.lastOpenFile = os.path.split(fname[0])
            # 获取表格中的数据
            datas = pyexcel.iget_records(file_name=fname[0])
            self.sheet = pyexcel.get_sheet(file_name=fname[0])
            # 跳过第一行的标题
            self.preferences.lastComments = []
            for i, record in enumerate(datas):
                self.preferences.lastComments.append(record)
                self.tableInsertRow(i, record)
            self.statusBar().showMessage('导入成功')
            # 设置为已经导入
            self.IMPORTED = True
            self.savePreferences()

    def startWork(self):
        if not self.IMPORTED:
            QMessageBox.information(self, '提示', '请先导入任务')
            return
        try:
            # 将按钮禁用
            self.buttonStart.setDisabled(True)
            # 创建工作对象，传入参数
            self.workThread = WorldThread(self.preferences.lastComments, self.spinboxTime.text())
            # 连接子线程的信号和槽函数
            self.workThread.statusBarSignal.connect(self.statusBar().showMessage)
            self.workThread.messageBoxSignal.connect(self.messageWarn)
            self.workThread.finishSignal.connect(self.endWork)
            # 开始执行子进程的run()函数的内容
            self.workThread.start()
        except Exception as e:
            print(e)

    def endWork(self, work_times):
        print('Work Thread end !', work_times)
        try:
            work_times.insert(0, self.sheet.column[3][0])
            self.sheet.column[3] = work_times
            self.sheet.save_as(self.preferences.lastOpenFilePath + '/成功_' + self.preferences.lastOpenFile)
        except Exception as e:
            print(e)
        # 恢复按钮
        self.buttonStart.setDisabled(False)

    def messageWarn(self, msg):
        QMessageBox.warning(self, '注意', msg)

    def exportDialog(self):
        QMessageBox.warning(self, '错误', '登录失败，请重新开始')
        print('xiayibu')

    # 将导入的数据更新到Table中
    def tableInsertRow(self, row, data):
        column = ['QQ号码', '视频标题', '引导内容', '引导时间']
        for i, name in enumerate(column):
            item = QTableWidgetItem(str(data[name]))  # 必须传str参数，否则报错
            item.setToolTip(item.text())
            self.tableComments.setItem(row, i, item)

    # 载入偏好输入
    def loadPreferences(self):
        # 判断文件是否存在
        if os.path.exists(self.preferencesFileName):
            with open(self.preferencesFileName, 'rb') as pfile:
                return pickle.load(pfile)
        else:
            return Storage()

    # 保存偏好数据
    def savePreferences(self):
        with open(self.preferencesFileName, 'wb') as p_file:
            pickle.dump(self.preferences, p_file)

    # 点击菜单后的空动作，用来占位的
    def doAction(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ui = Main_Ui()
    sys.exit(app.exec_())
