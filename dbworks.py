#!/usr/bin/python
# CinemaApp dbworks module.
# Модуль для работы с базой данных мест в зале.
"""
Этот модуль вмещает в себе все необходимые фунцкии для создания, тестирования
базы данных мест в зале кинотеатра, а также функции чтения, изменения состояния
мест в базе и вывод отчетов по проданным местам и по выручке.
Для приминения в приложении необходимо подключить базу данных:

    db = create_DB(файл базы данных)

а по окончанию работы - закрыть БД

    if db is not None:
            db.close()
"""

import sqlite3, os, datetime, random

file = "tmpdb.mdl"
MENU = "Choose menu item:\n" + \
       "1. Create / connect DB\n" + \
       "2. Check new day\n" + \
       "3. Report by places\n" + \
       "4. Report by sales\n" + \
       "5. Show all db\n" + \
       "6. Sell random tickets for today's sessions\n" + \
       "7. Quit\n\n"
SESSIONS = ("Session10", "Session12", "Session14", "Session16")


def connect_DB(filename):
    """
    Аргументы: БД
    Подключение базы данных, если указанный файл отсутствует,
    то создание пустой базы данных из двух таблиц.
    """
    create = not os.path.exists(filename)
    db = sqlite3.connect(filename)
    if create:
        # если файла БД не существует - создаем новый
        cursor = db.cursor()
        cursor.execute("CREATE TABLE Seats ( \
                       RecNo INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, \
                       SeatCode INTEGER NOT NULL, \
                       Session10 INTEGER DEFAULT 0, \
                       Session12 INTEGER DEFAULT 0, \
                       Session14 INTEGER DEFAULT 0, \
                       Session16 INTEGER DEFAULT 0, \
                       RecDate TEXT NOT NULL)")
        db.commit()
        cursor.execute("CREATE TABLE Sales ( \
                       RecNo INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, \
                       RecDate TEXT NOT NULL, \
                       SeatCode INTEGER NOT NULL, \
                       Session10 INTEGER DEFAULT 0, \
                       Session12 INTEGER DEFAULT 0, \
                       Session14 INTEGER DEFAULT 0, \
                       Session16 INTEGER DEFAULT 0)")
        db.commit()
    return db

def isVacancy(seatNo, session, date, db):
    """
    Аргументы: номер места, сеанс, дата, БД.
    Проверка занятости места, если свобовдно - возвращает True, занято - False
    """
    cursor = db.cursor()
    # проверяем наличие записей на указанную дату
    sql = "SELECT RecNo \
           FROM Seats \
           WHERE RecDate={0} AND SeatCode={1} AND {2}>0".format(date,
                                                                seatNo,
                                                                session)
    cursor.execute(sql)
    day_flag = False
    for record in cursor:
        day_flag = True
    return day_flag

def sell_seat(seatNo, session, date, price, db):
    """
    Аргументы: номер места, сеанс, дата, цена билета, БД.
    Процедура продажи места в зале.     
    """
    cursor = db.cursor()    
    # записываем флаг 1 в таблицу мест для указанного места в указанный сеанс и день
    sql = "UPDATE Seats \
           SET {1} = 1 \
           WHERE (SeatCode={0}) AND (RecDate={2})".format(seatNo,
                                                          session,
                                                          date)
    cursor.execute(sql)
    db.commit()
    # записываем цену билета в таблицу продаж для указанного места в указанный сеанс и день
    sql = "UPDATE Sales \
           SET {1} = {3} \
           WHERE (SeatCode={0}) AND (RecDate={2})".format(seatNo,
                                                          session,
                                                          date,
                                                          price)
    cursor.execute(sql)
    db.commit()

def return_seat(seatNo, session, date, db):
    """
    Аргументы: номер места, сеанс, дата, БД.
    Процедура возврата проданного места.     
    """
    cursor = db.cursor()    
    # записываем флаг 0 в таблицу мест для указанного места в указанный сеанс и день
    sql = "UPDATE Seats \
           SET {1} = 0 \
           WHERE (SeatCode={0}) AND (RecDate={2})".format(seatNo,
                                                          session,
                                                          date)
    cursor.execute(sql)
    db.commit()
    # обнуляем цену билета в таблицу продаж для указанного места в указанный сеанс и день
    sql = "UPDATE Sales \
           SET {1} = 0 \
           WHERE (SeatCode={0}) AND (RecDate={2})".format(seatNo,
                                                          session,
                                                          date)
    cursor.execute(sql)
    db.commit()

def new_day(date, price, db):
    """
    Аргументы: дата, цена билета, БД.
    Если записи на указанную дату не существуют, то добавляем записи для каждого
    места на эту дату. Все занчения полей по умолчанию.
    """
    cursor = db.cursor()
    # проверяем наличие записей на указанную дату
    sql = "SELECT RecNo \
           FROM Seats \
           WHERE RecDate={0}".format(date)
    cursor.execute(sql)
    day_flag = False
    for record in cursor:
        day_flag = True
    if day_flag:
        # если записи присутствуют - выходим
        return 
    # если записи отсутствуют - добавляем их
    # генерируем перечень номеров мест
    hall = []
    for k in range(1,11):
        for i in range(1,11):
            seatno = k * 100 + i
            hall.append(seatno)
    # создаем записи для каждого места на указанную дату
    for seat in hall:
        sql = "INSERT INTO Seats(SeatCode, \
                                 Session10, \
                                 Session12, \
                                 Session14, \
                                 Session16, \
                                 RecDate)  \
               VALUES ({0}, 0, 0, 0, 0, {1})".format(seat, date)
        cursor.execute(sql)
        db.commit()
        sql = "INSERT INTO Sales(RecDate, \
                                 SeatCode, \
                                 Session10, \
                                 Session12, \
                                 Session14, \
                                 Session16)  \
               VALUES ({0}, {1}, 0, 0, 0, 0)".format(date, seat)
        cursor.execute(sql)
        db.commit()
        
               
def report_by_places(date, db):
    """
    Аргументы: дата, БД.
    Отчет по проданым местам, возвращает кортеж с кол-вом проданых билетов на
    каждый отдельный сеанс, кол-во проданных за день, процент проданых за день.
    """
    cursor = db.cursor()
    # считаем для каждого сеанса кол-во проданных билетов (флаг сеанса > 0),
    # кол-во проданных за день, процент проданых за день
##    sql = "SELECT DISTINCT \
##           (SELECT COUNT(Session10) FROM Seats WHERE (Session10>0) AND RecDate={0}) AS s10, \
##           (SELECT COUNT(Session12) FROM Seats WHERE (Session12>0) AND RecDate={0}) AS s12, \
##           (SELECT COUNT(Session14) FROM Seats WHERE (Session14>0) AND RecDate={0}) AS s14, \
##           (SELECT COUNT(Session16) FROM Seats WHERE (Session16>0) AND RecDate={0}) AS s16, \
##           (s10+s12+s14+s16) AS DailyTotal, \
##           (DailyTotal/400) AS DailyPercent   \
##           FROM Seats \
##           WHERE RecDate={0}".format(date)
    sql = "SELECT DISTINCT \
           (SELECT COUNT(Session10) FROM Seats WHERE (Session10>0) AND RecDate={0}) AS s10, \
           (SELECT COUNT(Session12) FROM Seats WHERE (Session12>0) AND RecDate={0}) AS s12, \
           (SELECT COUNT(Session14) FROM Seats WHERE (Session14>0) AND RecDate={0}) AS s14, \
           (SELECT COUNT(Session16) FROM Seats WHERE (Session16>0) AND RecDate={0}) AS s16  \
           FROM Seats \
           WHERE RecDate={0}".format(date)
    cursor.execute(sql)
    report = cursor.fetchall()
    if report:
        s10, s12, s14, s16 = report[0][0], report[0][1], report[0][2], report[0][3]
        dailytotal = s10 + s12 + s14 + s16
        dailypercent = dailytotal/400
        return s10, s12, s14, s16, dailytotal, dailypercent
    else:
        return None

def report_by_sales(date, db):
    """
    Аргументы: дата, БД.
    Отчет по выручке, возвращает кортеж с суммой проданых билетов на
    каждый отдельный сеанс, сумму за день.
    """
    cursor = db.cursor()
    # считаем для каждого сеанса сумму проданых билетов и сумму за весь день
    sql = "SELECT SUM(Session10) AS s10, \
                  SUM(Session12) AS s12, \
                  SUM(Session14) AS s14, \
                  SUM(Session16) AS s16  \
                  FROM Sales \
                  WHERE RecDate={0}".format(date)
    cursor.execute(sql)
    report = cursor.fetchall()
    if report:
        s10, s12, s14, s16 = report[0][0], report[0][1], report[0][2], report[0][3]
        dailytotal = s10 + s12 + s14 + s16
        return s10, s12, s14, s16, dailytotal
    else:
        return None

### test ###

def show_all_sales(db):
    """
    Аргументы: БД.
    Выводит в консоль содержимое всей таблицы с продажами.
    Осторожно, данных может быть оч много.
    """
    cursor = db.cursor()
    sql = "SELECT * FROM Sales"
    cursor.execute(sql)
    print("Sales :")
    print("{0:5}|{1:^15}|{2:^5}|{3:^7}|{4:^7}|{5:^7}|{6:^7}".format("RecNo",
                                                              "RDate",
                                                              "SCode",
                                                              "S10",
                                                              "S12",
                                                              "S14",
                                                              "S16"))
    for record in cursor:
        print("{0:5}|{1:^15}|{2:^5}|{3:^7}|{4:^7}|{5:^7}|{6:^7}".format(*record))
    
def show_all_seats(db):
    """
    Аргументы: БД.
    Выводит в консоль содержимое всей таблицы с местами.
    Осторожно, данных может быть оч много.
    """
    cursor = db.cursor()
    sql = "SELECT * FROM Seats"
    cursor.execute(sql)
    print("Seats :")
    print("{0:5}|{1:^5}|{2:^7}|{3:^7}|{4:^7}|{5:^7}|{6:^15}".format("RecNo",
                                                                    "SCode",
                                                                    "S10",
                                                                    "S12",
                                                                    "S14",
                                                                    "S16",
                                                                    "RDate"))
    for record in cursor:
        print("{0:5}|{1:^5}|{2:^7}|{3:^7}|{4:^7}|{5:^7}|{6:^15}".format(*record))

def randomize_base(date, price, db):
    """
    Аргументы: дата, цена билета, БД.
    Вводит в базу данных случайные значения проданых мест.
    Осторожно, данных может быть оч много.
    """
    new_day(date, price, db)
    # генерируем перечень номеров мест
    hall = []
    for k in range(1,11):
        for i in range(1,11):
            seatno = k * 100 + i
            hall.append(seatno)
    # для каждого места кидаем монетку 1/0, если 1 - продаем место
    for seat in hall:
        for session in SESSIONS:
            foo = random.randint(0,1)
            if foo:
                sell_seat(seat, session, date, price, db)
        
    
        
### test ###


if __name__ == "__main__":
    """
    Если модуль запускается не из другого приложения, а как самостоятельная
    программа - работаем в режиме администрирования через консоль.
    """
    print("__Administration mode ON__")
    db = None
    todaydate = str(datetime.date.today())
    print("__Today is: ", todaydate, "__")
    ticket = 30
    while True:
        try:
            r = int(input(MENU))
            if r == 1:
                db = connect_DB(file)
                print("DB was successefully connected")
            elif r == 2:
                new_day(todaydate, ticket, db)
            elif r == 3:
                report = report_by_places(todaydate, db)
                print(todaydate, " : ", *report)
            elif r == 4:
                report = report_by_sales(todaydate, db)
                print(todaydate, " : ", *report)
            elif r == 5:
                show_all_seats(db)
                show_all_sales(db)
            elif r == 6:
                randomize_base(todaydate, ticket, db)
                print("DB was successefully populated")
            elif r == 7:
                break
            else:
                raise ValueError
        except ValueError as err:
            print(err + ", it sould be number from 1 to 3")
    if db is not None:
            db.close()
