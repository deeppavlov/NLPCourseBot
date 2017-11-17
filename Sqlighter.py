# -*- coding: utf-8 -*-

import sqlite3
from sqlite3 import Error
import config
import os


class SQLighter:
    def __init__(self, database_file_path):
        if not os.path.exists(database_file_path):
            try:
                self.connection = sqlite3.connect(database_file_path)
            except Error as e:
                print(e)
            self.cursor = self.connection.cursor()
            self.cursor.execute("CREATE TABLE Questions ( user_id TEXT NOT NULL, "
                                "date_added INTEGER NOT NULL, question TEXT );")
            self.cursor.execute("CREATE TABLE hw ( user_id TEXT, hw_num TEXT, date INTEGER, file_id TEXT );")
            self.cursor.execute("CREATE TABLE hw_checking ( file_id TEXT, user_id TEXT, mark INTEGER, "
                                "date_checked INTEGER, date_started INTEGER );")
            self.connection.commit()
            self.connection.isolation_level = None
        else:
            self.connection = sqlite3.connect(database_file_path)
            self.connection.isolation_level = None
            self.cursor = self.connection.cursor()

    def get_questions_last_week(self):
        """ Get only fresh questions from last n days """
        return self.cursor.execute("SELECT user_id, question, datetime(q.date_added, 'unixepoch', 'localtime') "
                                   "FROM questions q "
                                   "WHERE (q.date_added >= strftime('%s','now','-7 day'))").fetchall()

    def write_question(self, user_id, question):
        """ Insert question into BD """
        self.cursor.execute("INSERT INTO Questions (user_id, question, date_added)"
                            " VALUES (?, ?, strftime('%s','now'))", (user_id, question))

    def make_fake_db_record(self, user_id, hw_number):
        """ Make empty record for this hw_number """
        self.cursor.execute("INSERT INTO hw (user_id, hw_num, date)"
                            " VALUES (?, ?, strftime('%s','now'))", (user_id, hw_number))

    def upd_homework(self, user_id, file_id):
        """ UPD the latest record of user_id with file_id """
        self.cursor.execute("UPDATE hw SET file_id = ?, date = strftime('%s','now') "
                            "WHERE user_id = ? AND hw_num = "
                            "(SELECT hw_num FROM hw WHERE user_id = ? ORDER BY date DESC LIMIT 1)",
                            (file_id, user_id, user_id))

    def write_check_hw_ids(self, user_id, file_id):
        return self.cursor.execute("INSERT INTO hw_checking (file_id, user_id, date_started) "
                                   "VALUES (?, ?, strftime('%s','now'))", (file_id, user_id))

    def get_file_ids(self, hw_num, number_of_files):
        return self.cursor.execute("SELECT hw.file_id, count(hw_checking.file_id) checks_count "
                                   "FROM hw "
                                   "LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL "
                                   "AND hw.hw_num = :hw_num "
                                   "GROUP BY hw.file_id "
                                   "ORDER BY checks_count "
                                   "LIMIT :num_files",
                                   {'hw_num': hw_num,
                                    'num_files': number_of_files}).fetchall()

    def save_mark(self, user_id, mark):
        return self.cursor.execute("UPDATE hw_checking SET mark = ?, date_checked=strftime('%s','now') "
                                   "WHERE user_id = ? AND file_id = "
                                   "(SELECT file_id FROM hw_checking "
                                   "WHERE user_id = ? ORDER BY date_started DESC LIMIT 1)", (mark, user_id, user_id))

    def get_marks(self, user_id):
        return self.cursor.execute("SELECT hw.hw_num, datetime(hw.date, 'unixepoch', 'localtime'), avg(hw_checking.mark) avg_mark "
                                   "FROM hw LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.user_id = ? "
                                   "AND hw.file_id IS NOT NULL AND hw_checking.mark IS NOT NULL "
                                   "GROUP BY hw.date, hw.hw_num ORDER BY avg_mark", (user_id,)).fetchall()

    def get_checked_works_stat(self):
        return self.cursor.execute("SELECT hw.hw_num, count(hw_checking.file_id) checks_count "
                                   "FROM hw LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL AND hw_checking.mark IS NOT NULL "
                                   "GROUP BY hw.hw_num ORDER BY checks_count ").fetchall()

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    sql = SQLighter(config.bd_name)
