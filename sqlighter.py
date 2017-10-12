# -*- coding: utf-8 -*-

import sqlite3
import config


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    # def check_hw_date(self, user_id, hw_num, course):
    #     """ Check if that hw_num is exists for user_id """
    #     with self.connection:
    #         return self.cursor.execute("SELECT datetime(date, 'unixepoch') FROM hw WHERE (user_id = ?) AND (hw_num = ?) AND (course = ?)",
    #                                    (user_id, hw_num, course)).fetchall()

    def is_exists_hw(self, user_id, hw_num, course):
        """ Check if that hw_num is exists for user_id """
        with self.connection:
            return len(self.cursor.execute("SELECT * FROM hw WHERE (user_id = ?) AND (hw_num = ?) AND (course = ?)",
                                       (user_id, hw_num, course)).fetchall()) > 0

    def upd_homework(self, user_id, hw_num, course, file_id):
        """ UPD hw """
        with self.connection:
            return self.cursor.execute(
                "UPDATE hw SET file_id = ?, date = strftime('%s','now') WHERE (user_id = ?) AND (hw_num = ?) AND (course = ?)",
                (file_id, user_id, hw_num, course))

    def add_homework(self, user_id, hw_num, course, file_id):
        """ ADD hw """
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO hw (file_id, user_id, hw_num, course, date) VALUES (?, ?, ?, ?, strftime('%s','now'))",
                (file_id, user_id, hw_num, course))

    def select_questions_last_n_days(self, course, n_days):
        """ Get only fresh questions from last n days """
        with self.connection:
            return self.cursor.execute("SELECT question FROM Questions WHERE (course = ?) AND "
                                       "(date_added >= strftime('%s','now','-{} day'))".format(n_days),
                                       (course,)).fetchall()

    def write_question(self, user_id, question, course):
        """ Insert question into BD """
        with self.connection:
            return self.cursor.execute("INSERT INTO Questions (user_id, question, course, date_added)"
                                       " VALUES (?, ?, ?, strftime('%s','now'))", (user_id, question, course))

if __name__ == '__main__':
    sql = SQLighter(config.bd_name)
    print(sql.is_exists_hw(232, 'sem2', 'NLP'))
    sql.add_homework(232, 'sem2', 'NLP', 'dfgsdfe54df')
    print(sql.is_exists_hw(232, 'sem2', 'NLP'))
    sql.upd_homework(232, 'sem2', 'NLP', 'ersSDFgsresrEr34')
    print(sql.is_exists_hw(232, 'sem2', 'NLP'))
    sql.write_question(34, 'sdfgserge dfgs', 'NLP')
    print(sql.select_questions_last_n_days('NLP', 3))
