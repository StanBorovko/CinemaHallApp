#!/usr/bin/python
# CinemaApp

from PyQt5 import QtCore, QtWidgets, QtGui, QtPrintSupport 
import sys, os, datetime, sqlite3, time, random
import dbworks as dbw

DEF_WINDOW_WI = 1024 #Ширина окна по умолчанию
DEF_WINDOW_HI = 768  #Высота окна по умолчанию
DEF_DIAGRAM_WI = 800
DEF_DIAGRAM_HI = 500
DIAG_V_SPACING = 50
DIAG_H_SPACING = 100
DIAG_ELEMENT_MIN_WI = 10
DIAG_ELEMENT_MIN_HI = 1
MAX_SEATS_PER_DAY = 400
AXIS_Y_SPACING = 50
AXIS_Y_STEP = 100
WHITE = QtCore.Qt.white
BLACK = QtCore.Qt.black
RED = QtCore.Qt.red
BLUE = QtCore.Qt.blue
CYAN = QtCore.Qt.cyan
PARAMS = "OperatorName", "TicketPrice"
INIFILE = "CinemaApp.ini"
FILENAME = "CinemaDB.db"
TODAY = datetime.date.today()
ICONS = {"main": "./icons/film_reel.png",
         "ok": "./icons/ok.png",
         "cancel": "./icons/cancel.png",
         "setup": "./icons/adjustments_64px.png",
         "today": "./icons/alarmclock_64px.png",
         "about": "./icons/pencil_64px.png",
         "aboutQt": "./icons/toolbox_64px.png",
         "print": "./icons/printer_64px.png",
         "refresh": "./icons/refresh_64px.png",
         "exit": "./icons/caution_64px.png"}

class CinemaApp(QtWidgets.QMainWindow):
    """
    Класс главного окна приложения
    """
    def __init__(self, parent=None):
        """
        При создании нового экземпляра класса выполняется создание интерфейса
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.FIO, self.TICKET_PRICE = self.readParametersFromFile(INIFILE)
        self.filename = FILENAME
        self.db = dbw.connect_DB(self.filename)
        dbw.new_day(str(TODAY), self.TICKET_PRICE, self.db)
        self.initUI()        
        self.statusBar().showMessage("Добро пожаловать! Текущее время: " + \
                                     str(datetime.datetime.now().time()))
        
        
    def initUI(self):
        """
        Создание и настройка элементов графического интерфейса пользователя.
        """
        #Главное окно :
        self.setWindowTitle("Кинотеатр")
        self.resize(DEF_WINDOW_WI, DEF_WINDOW_HI)
        self.setMinimumSize(DEF_WINDOW_WI, DEF_WINDOW_HI)        #мин размер окна
        desktop = QtWidgets.QApplication.desktop()               #выводим в центр экрана
        wx = (desktop.width() - self.frameSize().width()) // 2   #
        wy = (desktop.height() - self.frameSize().height()) // 2 #
        self.move(wx, wy)
        
        #Действия в главном меню :
        exitAction = QtWidgets.QAction(QtGui.QIcon(ICONS["exit"]), "Выход", self)
        exitAction.setShortcut("Alt+F4")
        exitAction.setStatusTip("Выход из программы.")
        exitAction.triggered.connect(QtWidgets.qApp.quit)

        setupAction = QtWidgets.QAction(QtGui.QIcon(ICONS["setup"]), "Настройки...", self)
        setupAction.setShortcut("Alt+O")
        setupAction.setStatusTip("Настройки приложения.")
        setupAction.triggered.connect(self.openSetupWindow)

        aboutAction = QtWidgets.QAction(QtGui.QIcon(ICONS["about"]), "О программе...", self)
        aboutAction.setShortcut("Alt+F1")
        aboutAction.setStatusTip("Информация о приложении.")
        aboutAction.triggered.connect(self.openAboutWindow)

        aboutQtAction = QtWidgets.QAction(QtGui.QIcon(ICONS["aboutQt"]), "О Qt5...", self)
        aboutQtAction.setShortcut("Alt+F2")
        aboutQtAction.setStatusTip("Информация о Qt5.")
        aboutQtAction.triggered.connect(QtWidgets.QApplication.instance().aboutQt)

        #Главное меню приложения :
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("Файл")
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        servisMenu = mainMenu.addMenu("Сервис")
        servisMenu.addAction(setupAction)
        helpMenu = mainMenu.addMenu("Справка")
        helpMenu.addAction(aboutAction)
        helpMenu.addAction(aboutQtAction)

        #Виджеты для панели инструментов :
        sessionLabel = QtWidgets.QLabel("   Сеанс : ")
        dateLabel = QtWidgets.QLabel("   Дата : ")
        self.operatorLabel = QtWidgets.QLabel("{0:>25} {1:<25}".format("Фамилия оператора :", self.FIO))
        self.ticketLabel = QtWidgets.QLabel("{0:>25} {1:<5}".format("Цена билета :", self.TICKET_PRICE))
        
        self.sessionSelector = QtWidgets.QComboBox()
        self.sessionSelector.addItem("Сеанс 10ч", "Session10")
        self.sessionSelector.addItem("Сеанс 12ч", "Session12")
        self.sessionSelector.addItem("Сеанс 14ч", "Session14")
        self.sessionSelector.addItem("Сеанс 16ч", "Session16")
        self.sessionSelector.currentIndexChanged.connect(self.onSessionChange)

        self.dateSelector = QtWidgets.QDateEdit()
        self.dateSelector.setDate(TODAY)
        self.dateSelector.setCalendarPopup(True)
        self.dateSelector.setDisabled(True)

        self.todayBtn = QtWidgets.QPushButton("Сегодня")
        self.todayBtn.setDisabled(True)
        self.todayBtn.clicked.connect(self.onTodayBtnPressed)

        #Панель инструментов :
        mainBar = self.addToolBar("Стандартные")
        mainBar.setFloatable(False)
        mainBar.setMovable(False)
        mainBar.addWidget(sessionLabel)
        mainBar.addWidget(self.sessionSelector)
        mainBar.addWidget(dateLabel)
        mainBar.addWidget(self.dateSelector)
        mainBar.addWidget(self.todayBtn)
        mainBar.addWidget(self.operatorLabel)
        mainBar.addWidget(self.ticketLabel)

        #Панель с местами :
        frameHall = QtWidgets.QWidget()
        frameHall.layout = QtWidgets.QGridLayout()
        
        caption = QtWidgets.QLabel("<center><h1><b>Зал</b></h1></center>")  #Заголовок над кнопками
        caption.resize(500, 20)
        caption.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        frameHall.layout.addWidget(caption, 0, 5)
       
        labels = []
        for i in range(1,11):   #Генерация надписей-имен рядов
            labelText = "<center><b>{0} {1:>3}</b></center>".format("Ряд",str(i))
            label = QtWidgets.QLabel(labelText)
            labels.append(label)
            frameHall.layout.addWidget(label, i, 0)            

        self.buttons = []
        for i in range(1,11):   #Генерация кнопок
            for j in range(1,11):
                btnText = "{0}.{1:0>2}".format(i,j) #текст на кнопке в формате Р.ММ
                seatno = i * 100 + j 
                btn = SeatButton(btnText, seatNo=seatno, parent=self) 
                if self.checkVacancy(seatno):
                    btn.setStyleSheet("background-color:rgb(128,255,128)")
                else:
                    btn.setStyleSheet("background-color:rgb(255,128,128)")                
                btn.clicked.connect(self.onSeatBtnPressed)
                self.buttons.append(btn)
                frameHall.layout.addWidget(btn, i, j)                
                
        frameHall.setLayout(frameHall.layout)

        #Панель с проданными :
        frameSeats = QtWidgets.QWidget()
        

        refreshSeatsBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Обновить")  #Кнопка обновить
        refreshSeatsBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        refreshSeatsBtn.clicked.connect(self.onRefreshSeatsPressed)

        seatsDiagrBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Показать график")  #Кнопка показа графика проданных
        seatsDiagrBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        seatsDiagrBtn.clicked.connect(self.onSeatsDiagrPressed)

        reportSeatsLabel = QtWidgets.QLabel("<center><h1><b>Количество проданных мест:</b></h1></center>") #Заголовок отчета

        self.seatsTable = QtWidgets.QTableWidget(frameSeats) #Таблица в которую будут выводится данные
        self.seatsTable.setColumnCount(7)
        self.seatsTable.setRowCount(1)
        
        headers = ["Дата", "Сеанс 10", "Сеанс 12", "Сеанс 14",
                   "Сеанс 16", "Всего продано за день", "% проданых за день"]
        self.seatsTable.setHorizontalHeaderLabels(headers) 
        for i in range(self.seatsTable.columnCount()):  #Форматируем заголовки и подсказки, заполняем таблицу пустышками
            self.seatsTable.horizontalHeaderItem(i).setToolTip(headers[i])
            self.seatsTable.horizontalHeaderItem(i).setTextAlignment(QtCore.Qt.AlignHCenter)
            item = QtWidgets.QTableWidgetItem("{:^9}".format("---"))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.seatsTable.setItem(0, i, item)
   
        self.seatsTable.setVerticalHeaderLabels([" "]) #Убираем имя строки
        self.seatsTable.resizeColumnsToContents()        

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(refreshSeatsBtn, alignment=QtCore.Qt.AlignLeft)
        hbox.addWidget(seatsDiagrBtn, alignment=QtCore.Qt.AlignLeft)
        hbox.addStretch(frameSeats.width()-refreshSeatsBtn.width()-seatsDiagrBtn.width())
        frameSeats.layout = QtWidgets.QVBoxLayout(self)
        frameSeats.layout.addLayout(hbox)
        frameSeats.layout.addWidget(reportSeatsLabel)
        frameSeats.layout.addWidget(self.seatsTable)
        frameSeats.setLayout(frameSeats.layout)


        #Панель с выручкой :
        frameSells = QtWidgets.QWidget()
        frameSells.layout = QtWidgets.QGridLayout()

        refreshSellsBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Обновить")  #Кнопка обновить
        refreshSellsBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        refreshSellsBtn.clicked.connect(self.onRefreshSalesPressed)

        salesDiagrBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Показать график")  #Кнопка показа графика проданных
        salesDiagrBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        salesDiagrBtn.clicked.connect(self.onSalesDiagrPressed)

        reportSellsLabel = QtWidgets.QLabel("<center><h1><b>Выручка:</b></h1></center>") #Заголовок отчета

        self.sellsTable = QtWidgets.QTableWidget(frameSells) #Таблица в которую будут выводится данные
        self.sellsTable.setColumnCount(6)
        self.sellsTable.setRowCount(1)
        
        headers = ["Дата", "Сеанс 10", "Сеанс 12", "Сеанс 14",
                   "Сеанс 16", "Всего выручка за день"]
        self.sellsTable.setHorizontalHeaderLabels(headers) 
        for i in range(self.sellsTable.columnCount()):  #Форматируем заголовки и подсказки, заполняем таблицу пустышками
            self.sellsTable.horizontalHeaderItem(i).setToolTip(headers[i])
            self.sellsTable.horizontalHeaderItem(i).setTextAlignment(QtCore.Qt.AlignHCenter)
            item = QtWidgets.QTableWidgetItem("{:^9}".format("---"))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.sellsTable.setItem(0, i, item)
   
        self.sellsTable.setVerticalHeaderLabels([" "]) #Убираем имя строки
        self.sellsTable.resizeColumnsToContents()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(refreshSellsBtn, alignment=QtCore.Qt.AlignLeft)
        hbox.addWidget(salesDiagrBtn, alignment=QtCore.Qt.AlignLeft)
        hbox.addStretch(frameSells.width()-refreshSellsBtn.width()-salesDiagrBtn.width())
        frameSells.layout = QtWidgets.QVBoxLayout(self)
        frameSells.layout.addLayout(hbox)
        frameSells.layout.addWidget(reportSellsLabel)
        frameSells.layout.addWidget(self.sellsTable)
        frameSells.setLayout(frameSells.layout)

        #Панель со вкладками : 
        tabNotebook = QtWidgets.QTabWidget(self)
        tabNotebook.addTab(frameHall, QtGui.QIcon(), "&Места в зале")
        tabNotebook.addTab(frameSeats, QtGui.QIcon(), "Отчет по &проданым")
        tabNotebook.addTab(frameSells, QtGui.QIcon(), "Отчет по &выручке")
        tabNotebook.setCurrentIndex(0)
        tabNotebook.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        tabNotebook.currentChanged.connect(self.onTabChanged)
        
        #Управление размещением элементов:
        self.setCentralWidget(QtWidgets.QWidget())
        self.layout = QtWidgets.QHBoxLayout(self.centralWidget())        
        self.layout.addWidget(tabNotebook)

    def openSetupWindow(self):
        setupWindow = SetupWindow(parent=self)
        result = setupWindow.exec()
        if result == QtWidgets.QDialog.Accepted:
            self.writeParametersToFile(INIFILE,
                                       setupWindow.nameEdit.text(),
                                       setupWindow.ticketEdit.text())
            self.FIO, self.TICKET_PRICE = self.readParametersFromFile(INIFILE)
            self.operatorLabel.setText("{0:>25} {1:<25}".format("Фамилия оператора :", self.FIO))
            self.ticketLabel.setText("{0:>25} {1:<5}".format("Цена билета :", self.TICKET_PRICE))

            self.statusBar().showMessage("Настройки сохранены")
        else:
            self.statusBar().showMessage("Настройки не сохранены")

    def openAboutWindow(self):
        aboutMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                         "О приложении",
                                         "<center>КИНОТЕАТР</center>\n\n\
                                         <center>Управление местами в кинозале</center>\n\
                                         Приложение разработано как \
                                         дипломная работа по специальности 'Автоматизация \
                                         производственных процессов.'",
                                         buttons = QtWidgets.QMessageBox.Close,
                                         parent=self)
        aboutMsg.exec()

    def onTabChanged(self, i):
        """
        При переходне не вкладку отчета тушим выбор сеанса, зажигаем выбор даты.
        При переходне не вкладку зала тушим выбор даты, зажигаем выбор сеанса.
        """
        sender = self.sender()
        if i:
            self.sessionSelector.setDisabled(True)
            self.dateSelector.setEnabled(True)
            self.todayBtn.setEnabled(True)
        else:
            self.dateSelector.setDisabled(True)
            self.todayBtn.setDisabled(True)
            self.sessionSelector.setEnabled(True)

    def onTodayBtnPressed(self):
        """
        При нажатии на кнопку выставляется текущая дата в поле выбора даты.
        """
        currentDate = datetime.datetime.now().date()
        self.dateSelector.setDate(currentDate)

    def onSeatBtnPressed(self):
        """
        При нажатии на кнопку места показываем окошко с действиями над местом.
        """
        sender = self.sender()
        currentSession = self.sessionSelector.currentIndex()
        sessionName = self.sessionSelector.itemData(currentSession)
        seatEditWindow = SeatEditWindow(parent=sender,
                                        seatNo=sender.seatNo,
                                        session=sessionName,
                                        price=self.TICKET_PRICE,
                                        db=self.db)
        seatEditWindow.exec()

    def onRefreshSeatsPressed(self):
        """
        При нажатии на "Обновить" выводим информацию на выбранную дату.
        """
        sender = self.sender()
        date = self.dateSelector.date() #тут date - экземпляр класса QDate
        date = date.toPyDate() #преобразовываем в экземпляр класса datetime.date
        db = self.db
        report = dbw.report_by_places(date, db)
        if report is None:  #если отчет не содержит значений, показываем сообщение об этом
            nothingMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                               "Нечего показывать",
                                               "На выбранную дату отсутствует информация о билетах.",
                                               buttons = QtWidgets.QMessageBox.Close,
                                               parent=self)
            nothingMsg.exec()
            return
        item = QtWidgets.QTableWidgetItem(str(date))
        self.seatsTable.setItem(0, 0, item)        
        for i in range(len(report)):
            item = QtWidgets.QTableWidgetItem(str(report[i]))
            self.seatsTable.setItem(0, i+1, item)

    def onRefreshSalesPressed(self):
        sender = self.sender()
        date = self.dateSelector.date() #тут date - экземпляр класса QDate
        date = date.toPyDate() #преобразовываем в экземпляр класса datetime.date
        db = self.db
        report = dbw.report_by_sales(date, db)
        if report is None:  #если отчет не содержит значений, показываем сообщение об этом
            nothingMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                               "Нечего показывать",
                                               "На выбранную дату отсутствует информация о билетах.",
                                               buttons = QtWidgets.QMessageBox.Close,
                                               parent=self)
            nothingMsg.exec()
            return
        item = QtWidgets.QTableWidgetItem(str(date))
        self.sellsTable.setItem(0, 0, item)        
        for i in range(len(report)):
            item = QtWidgets.QTableWidgetItem(str(report[i]))
            self.sellsTable.setItem(0, i+1, item)

    def onSeatsDiagrPressed(self):
        seatsDiagr = SeatsGraph(db=self.db, parent=self)
        seatsDiagr.exec()

    def onSalesDiagrPressed(self):
        salesDiagr = SalesGraph(db=self.db, parent=self)
        salesDiagr.exec()

    def readParametersFromFile(self, filename):
        """
        Загружаем из файла значения параметров системы или создаем новый.
        Метод возвращает параметры в соответствии с перечнем имен параметров.
        Перечень имен параметров хранится в глобальной переменной PARAMS.
        """
        fileExists = os.path.exists(filename)   #проверяем наличие файла с параметрами
        if fileExists:                              #если файл есть - считываем содержимое
            try:
                fh = open(filename, encoding="utf8")
                params = []
                for lino, line in enumerate(fh, start=1):  #в каждой строчке файла
                    line = line.strip()
                    for param in PARAMS:                   #ищем каждый параметр
                        if line.startswith(param+"="):
                            params.append(line[len(param+"="):])
                return params
            except:
                errorMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                                 "Ошибка", "Ошибка при чтении файла "+filename,
                                                 buttons = QtWidgets.QMessageBox.Ok,
                                                 parent=self)
                errorMsg.exec()
            finally:
                if fh is not None:
                    fh.close()
        else:                      #если файл отсутствует, создаем новый и заполняем его
            self.makeNewParametersFile(filename)            
            return self.readParametersFromFile(filename)

    def writeParametersToFile(self, filename, *params):
        """
        Пишев в файл значения параметров системы.
        При вызове метода в коде новые параметры перечисляются в соответсвии с перечнем имен параметров,
        иначе можно записать неправильные значения.
        Перечень имен параметров хранится в глобальной переменной PARAMS.
        """
        try:            
            fh = open(filename, "w", encoding="utf8")
            i = 0
            for param in params:
                paramName = PARAMS[i]
                fh.write(paramName+"="+str(param)+"\n")
                i += 1
        except:
            errorMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                             "Ошибка", "Ошибка при записи в файл "+filename,
                                             buttons = QtWidgets.QMessageBox.Ok,
                                             parent=self)
            errorMsg.exec()
        finally:
            if fh is not None:
                fh.close()

    def makeNewParametersFile(self, filename):
        """
        Создание нового файла с параметрами приложения и заполнение значениями по умолчанию.
        Перечень имен параметров хранится в глобальной переменной PARAMS.
        """
        try:
            fh = open(filename, "w", encoding="utf8")
            for paramName in PARAMS:
                if paramName == "OperatorName":
                    fh.write(paramName+"="+"John Snow"+"\n")
                elif paramName == "TicketPrice":
                    fh.write(paramName+"="+"30"+"\n")
        except:
            errorMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                             "Ошибка", "Ошибка при создании файла "+filename,
                                             buttons = QtWidgets.QMessageBox.Ok,
                                             parent=self)
            errorMsg.exec()
        finally:
            if fh is not None:
                fh.close()

    def checkVacancy(self, seatNo):
        """
        Проверка занятости места
        """
        currentIndex = self.sessionSelector.currentIndex()
        session = self.sessionSelector.itemData(currentIndex)
        date = TODAY
        db = self.db
        if dbw.isVacancy(seatNo, session, date, db):
            return False
        return True

    def onSessionChange(self):
        """
        При смене сеанса в выпадающем списке, обновляем цвета кнопок.
        """
        for btn in self.buttons:
            if self.checkVacancy(btn.seatNo):
                btn.setStyleSheet("background-color:rgb(128,255,128)")
            else:
                btn.setStyleSheet("background-color:rgb(255,128,128)")

    def load_data(self, sp):
        """
        Имитация загрузки приложения
        """
        for i in range(1,11):
            time.sleep(2)
            sp.showMessage("Загрузка данных... {0}%".format(i*10),
                           QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom,
                           QtCore.Qt.black)
            QtWidgets.qApp.processEvents()


    def closeEvent(self, e):
        """
        Переопределяем событие выхода из приложения, добавляем сообщение выйти?да/нет и
        закрываем сеанс работы с базой данных
        """
        respond = QtWidgets.QMessageBox.question(self,
                                                 "Подтверждение выхода",
                                                 "Вы действительно хотите выйти из приложения?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if respond == QtWidgets.QMessageBox.Yes:
            if self.db is not None:
                self.db.close()
            e.accept()
            QtWidgets.QWidget.closeEvent(self,e)
        else:
            e.ignore()


class SetupWindow(QtWidgets.QDialog):
    """
    Класс окна настроек приложения 
    """
    def __init__(self, parent=None):
        """
        При создании нового экземпляра класса выполняется создание интерфейса окна настроек
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        """
        Создание и настройка элементов интерфейса окна настроек
        """
        #Окно настроек :
        self.setWindowTitle("Настройки")
        self.resize(300, 100)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.Window)
        desktop = QtWidgets.QApplication.desktop()               #выводим в центр экрана
        wx = (desktop.width() - self.frameSize().width()) // 2   #
        wy = (desktop.height() - self.frameSize().height()) // 2 #
        self.move(wx, wy)

        #Добавляем кнопки
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                               QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.buttons()[0].setIcon(QtGui.QIcon(ICONS["ok"]))
        buttonBox.buttons()[1].setIcon(QtGui.QIcon(ICONS["cancel"]))
                                       
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        #Добавляем элементы управления
        self.nameEdit = QtWidgets.QLineEdit("John Snow") #поле ввода ФИО оператора
        self.nameEdit.setMaxLength(50) #макс кол-во символов в поле ввода
        self.nameEdit.setClearButtonEnabled(True) #кнопка очистки строки
        self.nameEdit.editingFinished.connect(self.onNameEditingFinished)        
        
        self.ticketEdit = QtWidgets.QLineEdit("30")   #поле ввода цены билета
        self.ticketEdit.setMaxLength(50) #макс кол-во символов в поле ввода
        self.ticketEdit.setClearButtonEnabled(True) #кнопка очистки строки
        self.ticketEdit.setValidator(QtGui.QIntValidator(1, 999, parent=self))

        curOperator, curPrice = self.parent.readParametersFromFile(INIFILE)
        self.nameEdit.setText(curOperator)
        self.ticketEdit.setText(curPrice)
        

        #Управление размещением элементов:
        self.layout = QtWidgets.QFormLayout(self)        
        self.layout.addRow("&ФИО оператора:", self.nameEdit)
        self.layout.addRow("&Стоимость билета:", self.ticketEdit)
        self.layout.addRow(buttonBox)

    def onTicketEditingFinished(self):
        """
        Проверяем, если введены не только цифры, вызываем сообщение об ошибке,
        сбрасываем поле и возвращаем в него фокус.
        """
        sender = self.ticketEdit
        if sender.text is not None:
            if not str(sender.text).isdecimal():
                errorMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                                 "Ошибка", "В поле цены билета допускаются только цифры!",
                                                 buttons = QtWidgets.QMessageBox.Ok,
                                                 parent=self)
                errorMsg.exec()
                sender.setText("30")
                sender.setCursorPosition(0)

    def onNameEditingFinished(self):
        """
        Проверяем, если поле пустое, вызываем сообщение об ошибке,
        сбрасываем поле и возвращаем в него фокус.
        """
        if not len(self.nameEdit.text()):            
            errorMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                             "Ошибка", "Поле имени оператора должно быть непустое!",
                                             buttons = QtWidgets.QMessageBox.Ok,
                                             parent=self)
            errorMsg.exec()
            self.nameEdit.setText("John Snow")
            self.nameEdit.setCursorPosition(0)

class SeatEditWindow(QtWidgets.QDialog):
    """
    Класс окна продажи и возврата билета на указанное место 
    """
    def __init__(self, parent=None, seatNo=101, session="Session10", price="50", db=None):
        """
        При создании нового экземпляра класса выполняется создание интерфейса окна продажи
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.seatNo = self.parent.seatNo
        self.session = session        
        self.price = int(price)
        self.db = db
        self.initUI()
        

    def initUI(self):
        """
        Создание и настройка элементов интерфейса окна настроек
        """
        #Окно места :
        self.setWindowTitle("Продажа / возврат")
        self.resize(300, 100)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.Window)
        self.setStyleSheet("background-color: window")
        desktop = QtWidgets.QApplication.desktop()               #выводим в центр экрана
        wx = (desktop.width() - self.frameSize().width()) // 2   #
        wy = (desktop.height() - self.frameSize().height()) // 2 #
        self.move(wx, wy)
        
        #Заголовок :
        head = "<center><h1><b>Ряд {0} место {1}</b></h1></center>".format(self.seatNo // 100,
                                                                           self.seatNo % 100)
        headLabel = QtWidgets.QLabel(head)

        #Кнопки управления состоянием места :
        self.btnSell = QtWidgets.QPushButton("Продажа билета")
        self.btnSell.clicked.connect(self.onSellPressed)
        self.btnPrint = QtWidgets.QPushButton(QtGui.QIcon(ICONS["print"]), "Печать")
        self.btnPrint.clicked.connect(self.onPrintPressed)
        self.btnReturn = QtWidgets.QPushButton("Возврат билета")
        self.btnReturn.clicked.connect(self.onReturnPressed)
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.buttons()[0].setText("Закрыть")
        buttonBox.buttons()[0].setIcon(QtGui.QIcon(ICONS["cancel"]))
        buttonBox.rejected.connect(self.reject)

        if self.parent.parent.checkVacancy(self.seatNo):
            self.btnReturn.setDisabled(True)
            self.btnPrint.setDisabled(True)
            self.btnSell.setEnabled(True)
        else:
            self.btnSell.setDisabled(True)
            self.btnPrint.setEnabled(True)
            self.btnReturn.setEnabled(True)

        #Управление размещением элементов:
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.btnSell)
        hbox.addWidget(self.btnPrint)
        self.layout = QtWidgets.QVBoxLayout(self)        
        self.layout.addWidget(headLabel)
        self.layout.addLayout(hbox)
        self.layout.addWidget(self.btnReturn)
        self.layout.addWidget(buttonBox)        
        

    def onSellPressed(self):
        """
        Продажа билета
        """
        if self.checkTime():
            wrongTimeMSG = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                                 "Неверный сеанс",
                                                 "Время текущего сеанса истекло,\nВыберите более поздний сеанс.",
                                                 buttons = QtWidgets.QMessageBox.Ok,
                                                 parent=self)
            wrongTimeMSG.exec()
            return
        
        sender = self.sender        
        seatNo = self.seatNo
        session = self.session
        date = TODAY
        price = self.price
        db = self.db
        dbw.sell_seat(seatNo, session, date, price, db)
        sellMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                        "Продажа", "Билет успешно продан.",
                                        buttons = QtWidgets.QMessageBox.Ok,
                                        parent=self)
        sellMsg.exec()
        self.parent.setStyleSheet("background-color:rgb(255,128,128)")
        self.close()

    def onPrintPressed(self):
        """
        Печать билета.
        """
        if self.checkTime():
            wrongTimeMSG = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                                 "Неверный сеанс",
                                                 "Запрещена печать билетов на прошедшие сеансы.",
                                                 buttons = QtWidgets.QMessageBox.Ok,
                                                 parent=self)
            wrongTimeMSG.exec()
            return
        
        #Генерация текста билета :
        date = TODAY
        session = self.session[-2:]
        row = self.seatNo // 100
        seat = self.seatNo % 100
        fio = self.parent.parent.FIO        
        
        ticketPrint = "*" * 50 + "\n" + \
                      "Билет в кинотеатр.\n" + \
                      "Дата: {}\n".format(date) + \
                      "Сеанс {}:00\n".format(session) + \
                      "Ряд {}\n".format(row) + \
                      "Место {}\n".format(seat) + \
                      "Оператор: {}\n".format(fio) + \
                      "Данный документ является основанием для допуска\n" + \
                      "в кинозал на указанную дату, сеанс, ряд и место\n" + \
                      "для просмотра. Снимать камрипы строго запрещено\n" + \
                      "в соответствие с Законом Украины о камрипах.\n" + \
                      "*" * 50

                      
        
        #Печать текста :
        printer = QtPrintSupport.QPrinter()
        printer.setOutputFileName("output.pdf") #выводим билет в пдф
        painter = QtGui.QPainter()
        painter.begin(printer)
        color = QtGui.QColor(QtCore.Qt.black)
        painter.setPen(QtGui.QPen(color))
        painter.setBrush(QtGui.QBrush(color))
        font = QtGui.QFont("Verdana", pointSize = 14)
        painter.setFont(font)
        painter.drawText(10, 10,
                         printer.width(), 50,
                         QtCore.Qt.AlignLeft | QtCore.Qt.TextDontClip,
                         ticketPrint)
        painter.end()
        printMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                         "Печать", "Билет отправлен на печать",
                                         buttons = QtWidgets.QMessageBox.Ok,
                                         parent=self)
        printMsg.exec()
        self.close()


    def onReturnPressed(self):
        """
        Возврат купленного билета.
        """
        if self.checkTime():
            wrongTimeMSG = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                                 "Неверный сеанс",
                                                 "Запрещен возврат билетов на завершенные сеансы.",
                                                 buttons = QtWidgets.QMessageBox.Ok,
                                                 parent=self)
            wrongTimeMSG.exec()
            return
        
        sender = self.sender
        seatNo = self.seatNo
        session = self.session
        date = TODAY
        db = self.db
        dbw.return_seat(seatNo, session, date, db)
        returnMsg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                          "Возврат", "Билет успешно возвращен",
                                          buttons = QtWidgets.QMessageBox.Ok,
                                          parent=self)
        returnMsg.exec()
        self.parent.setStyleSheet("background-color:rgb(128,255,128)")
        self.close()

    def checkTime(self):
        """
        Проверяем, не опоздали ли на сеанс.
        """
        session = self.session
        allowedTime = datetime.time(int(session[-2:])+1, 50)
        currentTime = datetime.datetime.now().time()
        if currentTime > allowedTime:
            return True
        return False

    
class SeatsGraph(QtWidgets.QDialog):
    """
    Отображение графика кол-ва проданных мест
    """
    def __init__(self, db=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle("График проданных")
        # надпись-заголовок
        captionLabel = QtWidgets.QLabel("<center><h1>График количества проданных мест</h1></center>")


        # Выбор диапазона дат
        startDateLabel = QtWidgets.QLabel("Первый день")
        self.startDateSelector = QtWidgets.QDateEdit()  # первый день диапазона дат
        self.startDateSelector.setDate(TODAY - datetime.timedelta(7))
        self.startDateSelector.setCalendarPopup(True)
        self.startDateSelector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        finishDateLabel = QtWidgets.QLabel("Последний день")
        self.finishDateSelector = QtWidgets.QDateEdit()  # последний день диапазона дат
        self.finishDateSelector.setDate(TODAY)
        self.finishDateSelector.setCalendarPopup(True)
        self.finishDateSelector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.refreshSellsBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Обновить")  #Кнопка обновить
        self.refreshSellsBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.refreshSellsBtn.clicked.connect(self.onRefreshSalesPressed)

        #объект диаграмма
        self.diagram = SeatsDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком проданных по дням


        #Управление размещением элементов:
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(startDateLabel)
        self.hbox.addWidget(self.startDateSelector)
        self.hbox.addWidget(finishDateLabel)
        self.hbox.addWidget(self.finishDateSelector)
        self.hbox.addWidget(self.refreshSellsBtn, alignment=QtCore.Qt.AlignRight)

        self.diagram = SeatsDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком проданных по дням

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.buttons()[0].setText("Закрыть")
        self.buttonBox.buttons()[0].setIcon(QtGui.QIcon(ICONS["cancel"]))
        self.buttonBox.rejected.connect(self.reject)
        
        self.layout = QtWidgets.QVBoxLayout(self)        
        self.layout.addWidget(captionLabel)
        self.layout.addLayout(self.hbox)
        self.layout.addWidget(self.diagram)
        self.layout.addWidget(self.buttonBox)

    def onRefreshSalesPressed(self):
        self.layout.removeWidget(self.diagram)
        self.diagram = SeatsDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком проданных по дням
        self.layout.insertWidget(2, self.diagram)

class SalesGraph(QtWidgets.QDialog):
    """
    Отображение графика кол-ва проданных мест
    """
    def __init__(self, db=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle("График выручки")
        # надпись-заголовок
        captionLabel = QtWidgets.QLabel("<center><h1>График выручки</h1></center>")


        # Выбор диапазона дат
        startDateLabel = QtWidgets.QLabel("Первый день")
        self.startDateSelector = QtWidgets.QDateEdit()  # первый день диапазона дат
        self.startDateSelector.setDate(TODAY - datetime.timedelta(7))
        self.startDateSelector.setCalendarPopup(True)
        self.startDateSelector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        finishDateLabel = QtWidgets.QLabel("Последний день")
        self.finishDateSelector = QtWidgets.QDateEdit()  # последний день диапазона дат
        self.finishDateSelector.setDate(TODAY)
        self.finishDateSelector.setCalendarPopup(True)
        self.finishDateSelector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.refreshSellsBtn = QtWidgets.QPushButton(QtGui.QIcon(ICONS["refresh"]), "Обновить")  #Кнопка обновить
        self.refreshSellsBtn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.refreshSellsBtn.clicked.connect(self.onRefreshSalesPressed)

        #объект диаграмма
        self.diagram = SalesDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком выручки по дням


        #Управление размещением элементов:
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(startDateLabel)
        self.hbox.addWidget(self.startDateSelector)
        self.hbox.addWidget(finishDateLabel)
        self.hbox.addWidget(self.finishDateSelector)
        self.hbox.addWidget(self.refreshSellsBtn, alignment=QtCore.Qt.AlignRight)

        self.diagram = SeatsDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком выручки по дням

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.buttons()[0].setText("Закрыть")
        self.buttonBox.buttons()[0].setIcon(QtGui.QIcon(ICONS["cancel"]))
        self.buttonBox.rejected.connect(self.reject)
        
        self.layout = QtWidgets.QVBoxLayout(self)        
        self.layout.addWidget(captionLabel)
        self.layout.addLayout(self.hbox)
        self.layout.addWidget(self.diagram)
        self.layout.addWidget(self.buttonBox)

    def onRefreshSalesPressed(self):
        self.layout.removeWidget(self.diagram)
        self.diagram = SalesDiagram(db=self.db,
                                    start=self.startDateSelector.date().toPyDate(),
                                    finish=self.finishDateSelector.date().toPyDate())  #панель с графиком выручки
        self.layout.insertWidget(2, self.diagram)
        
class SeatButton(QtWidgets.QPushButton):
    """
    Обычная кнопка, но со свойством "Номер места"
    """
    def __init__(self, text="", seatNo=101, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.parent = parent
        self.setText(text)
        self.seatNo = seatNo

class SeatsDiagram(QtWidgets.QWidget):
    """
    Виджет с графиком проданных мест
    """
    def __init__(self, db=None, start=None, finish=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.db = db
        self.start = start
        self.finish = finish
        self.parent = parent
        self.timeDelta = self.getTimeDelta()
        #образмериваем виджет
        self.resize(DEF_DIAGRAM_WI, DEF_DIAGRAM_HI)
        self.setMinimumSize(DEF_DIAGRAM_WI, DEF_DIAGRAM_HI)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawGraph(qp)
        qp.end()

    def drawGraph(self, qp):
        """
        Рисуем: линии координат, засечки, подиписи, столбцы, подписи столбцов
        """
        #Кв-фактор для масштабирования по высоте
        Kv = (DEF_DIAGRAM_HI - DIAG_V_SPACING * 2 - AXIS_Y_SPACING) / MAX_SEATS_PER_DAY

        #Рисуем белый фон:
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(WHITE))
        qp.drawRect(0, 0, DEF_DIAGRAM_WI-1, DEF_DIAGRAM_HI-1)
        
        #рисуем ось У
        zeroPointX = DIAG_H_SPACING
        zeroPointY = DEF_DIAGRAM_HI - DIAG_V_SPACING
        endPointX = DIAG_H_SPACING
        endPointY = DIAG_V_SPACING
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(BLACK))
        qp.drawLine(zeroPointX, zeroPointY, endPointX, endPointY)

        #Засечки и надписи
        qp.drawText(0, endPointY,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignRight,
                    "Кол-во мест")
        qp.drawText(0, zeroPointY-10,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignRight,
                    "0")
        firstPointX = zeroPointX 
        firstPointY = zeroPointY
        lastPointX = firstPointX
        lastPointY = endPointY + DIAG_V_SPACING // 2
        Ky = (firstPointY - lastPointY) / (zeroPointY - endPointY)
        for i in range(AXIS_Y_STEP, MAX_SEATS_PER_DAY+AXIS_Y_STEP, AXIS_Y_STEP):
            startX = firstPointX - 5
            startY = firstPointY - i * Ky
            endX = lastPointX + 5
            endY = startY
            qp.setPen(QtGui.QColor(BLACK))
            qp.setBrush(QtGui.QColor(BLACK))
            qp.drawLine(startX, startY, endX, endY)
            qp.drawText(0, startY-10,
                        75, 25,
                        QtCore.Qt.AlignRight,
                        str(i))

        #рисуем ось X
        endPointX = DEF_DIAGRAM_WI - DIAG_H_SPACING
        endPointY = DEF_DIAGRAM_HI - DIAG_V_SPACING
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(BLACK))
        qp.drawLine(zeroPointX, zeroPointY, endPointX, endPointY)

        #Засечки, столбики и надписи
        qp.drawText(endPointX, endPointY,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignLeft,
                    "Дни")
        firstPointX = zeroPointX + DIAG_H_SPACING // 2
        firstPointY = zeroPointY
        lastPointX = endPointX - DIAG_H_SPACING // 2
        lastPointY = firstPointY
        Kx = (lastPointX - firstPointX) / self.timeDelta
        for i in range(self.timeDelta+1):            
            startX = firstPointX + i * Kx
            startY = firstPointY + 5
            endX = startX
            endY = lastPointY - 5
            qp.setPen(QtGui.QColor(BLACK))
            qp.setBrush(QtGui.QColor(BLACK))
            qp.drawLine(startX, startY, endX, endY)
            dateLabel = self.start + datetime.timedelta(i)
            qp.drawText(startX-50, startY+10+(i%2)*10,
                        100, 25,
                        QtCore.Qt.AlignCenter,
                        dateLabel.strftime('%d.%m'))
            #столбики диаграммы
            seatsNum = random.randint(0, 400)
            colWidth = Kx // 2 if Kx >= 20 else 10
            colHight = seatsNum * Ky            
            qp.setPen(QtGui.QColor(BLUE))
            qp.setBrush(QtGui.QColor(CYAN))
            qp.drawRect(startX-colWidth/2, firstPointY,
                        colWidth, -colHight)
            qp.drawText(startX-colWidth/2, startY-colHight-25,
                        colWidth, 25,
                        QtCore.Qt.AlignCenter,
                        str(seatsNum))
        

    def getTimeDelta(self):
        """
        Определяем разность дней и возвращаем его целым числом
        """
        timeDelta = self.finish - self.start
        return timeDelta.days


class SalesDiagram(QtWidgets.QWidget):
    """
    Виджет с графиком проданных мест
    """
    def __init__(self, db=None, start=None, finish=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.db = db
        self.start = start
        self.finish = finish
        self.parent = parent
        self.timeDelta = self.getTimeDelta()
        #образмериваем виджет
        self.resize(DEF_DIAGRAM_WI, DEF_DIAGRAM_HI)
        self.setMinimumSize(DEF_DIAGRAM_WI, DEF_DIAGRAM_HI)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawGraph(qp)
        qp.end()

    def drawGraph(self, qp):
        """
        Рисуем: линии координат, засечки, подиписи, столбцы, подписи столбцов
        """
        #Кв-фактор для масштабирования по высоте
        Kv = (DEF_DIAGRAM_HI - DIAG_V_SPACING * 2 - AXIS_Y_SPACING) / MAX_SEATS_PER_DAY

        #Рисуем белый фон:
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(WHITE))
        qp.drawRect(0, 0, DEF_DIAGRAM_WI-1, DEF_DIAGRAM_HI-1)
        
        #рисуем ось У
        zeroPointX = DIAG_H_SPACING
        zeroPointY = DEF_DIAGRAM_HI - DIAG_V_SPACING
        endPointX = DIAG_H_SPACING
        endPointY = DIAG_V_SPACING
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(BLACK))
        qp.drawLine(zeroPointX, zeroPointY, endPointX, endPointY)

        #Засечки и надписи
        qp.drawText(0, endPointY,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignRight,
                    "Выручка")
        qp.drawText(0, zeroPointY-10,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignRight,
                    "0")
        firstPointX = zeroPointX 
        firstPointY = zeroPointY
        lastPointX = firstPointX
        lastPointY = endPointY + DIAG_V_SPACING // 2
        Ky = (firstPointY - lastPointY) / (zeroPointY - endPointY)
        for i in range(AXIS_Y_STEP, MAX_SEATS_PER_DAY+AXIS_Y_STEP, AXIS_Y_STEP):
            startX = firstPointX - 5
            startY = firstPointY - i * Ky
            endX = lastPointX + 5
            endY = startY
            qp.setPen(QtGui.QColor(BLACK))
            qp.setBrush(QtGui.QColor(BLACK))
            qp.drawLine(startX, startY, endX, endY)
            qp.drawText(0, startY-10,
                        75, 25,
                        QtCore.Qt.AlignRight,
                        str(i))

        #рисуем ось X
        endPointX = DEF_DIAGRAM_WI - DIAG_H_SPACING
        endPointY = DEF_DIAGRAM_HI - DIAG_V_SPACING
        qp.setPen(QtGui.QColor(BLACK))
        qp.setBrush(QtGui.QColor(BLACK))
        qp.drawLine(zeroPointX, zeroPointY, endPointX, endPointY)

        #Засечки, столбики и надписи
        qp.drawText(endPointX, endPointY,
                    DIAG_H_SPACING-10, 25,
                    QtCore.Qt.AlignLeft,
                    "Дни")
        firstPointX = zeroPointX + DIAG_H_SPACING // 2
        firstPointY = zeroPointY
        lastPointX = endPointX - DIAG_H_SPACING // 2
        lastPointY = firstPointY
        Kx = (lastPointX - firstPointX) / self.timeDelta
        for i in range(self.timeDelta+1):            
            startX = firstPointX + i * Kx
            startY = firstPointY + 5
            endX = startX
            endY = lastPointY - 5
            qp.setPen(QtGui.QColor(BLACK))
            qp.setBrush(QtGui.QColor(BLACK))
            qp.drawLine(startX, startY, endX, endY)
            dateLabel = self.start + datetime.timedelta(i)
            qp.drawText(startX-50, startY+10+(i%2)*10,
                        100, 25,
                        QtCore.Qt.AlignCenter,
                        dateLabel.strftime('%d.%m'))
            #столбики диаграммы
            seatsNum = random.randint(0, 400)
            colWidth = Kx // 2 if Kx >= 20 else 10
            colHight = seatsNum * Ky            
            qp.setPen(QtGui.QColor(BLUE))
            qp.setBrush(QtGui.QColor(CYAN))
            qp.drawRect(startX-colWidth/2, firstPointY,
                        colWidth, -colHight)
            qp.drawText(startX-colWidth/2, startY-colHight-25,
                        colWidth, 25,
                        QtCore.Qt.AlignCenter,
                        str(seatsNum))
        

    def getTimeDelta(self):
        """
        Определяем разность дней и возвращаем его целым числом
        """
        timeDelta = self.finish - self.start
        return timeDelta.days
        
 

def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = CinemaApp()
    main_window.setWindowIcon(QtGui.QIcon(ICONS["main"]))
    app.setWindowIcon(QtGui.QIcon(ICONS["main"]))
    main_window.show()
    sys.exit(app.exec_())    

main()
        
