# -*- coding: utf-8 -*-

import sqlite3
from sqlite3 import Error
import pandas as pd
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

            self.cursor.execute("CREATE TABLE hw ( user_id TEXT, hw_num TEXT, "
                                "date_added INTEGER, file_id TEXT );")

            self.cursor.execute("CREATE TABLE hw_checking ( file_id TEXT, user_id TEXT, mark INTEGER, "
                                "date_checked INTEGER, date_started INTEGER );")

            self.cursor.execute("CREATE TABLE quizzes ( user_id	TEXT, "
                                "question_name	TEXT, "
                                "quiz_name	TEXT, "
                                "question_text TEXT, "
                                "true_ans TEXT, "
                                "is_right	INTEGER, "
                                "usr_answer	TEXT, "
                                "date_added INTEGER, "
                                "id INTEGER PRIMARY KEY AUTOINCREMENT );")
            self.cursor.execute("CREATE TABLE quizzes_checking ( checker_user_id TEXT, "
                                "id_quizzes INTEGER, "
                                "date_started INTEGER, "
                                "date_checked INTEGER, "
                                "is_right INTEGER);")
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
        self.cursor.execute("INSERT INTO hw (user_id, hw_num, date_added)"
                            " VALUES (?, ?, strftime('%s','now'))", (user_id, hw_number))

    def upd_homework(self, user_id, file_id):
        """ UPD the latest record of user_id with file_id """
        self.cursor.execute("UPDATE hw SET file_id = ?, date_added = strftime('%s','now') "
                            "WHERE user_id = ? AND hw_num = "
                            "(SELECT hw_num FROM hw WHERE user_id = ? ORDER BY date_added DESC LIMIT 1)",
                            (file_id, user_id, user_id))

    def write_check_hw_ids(self, user_id, file_id):
        return self.cursor.execute("INSERT INTO hw_checking (file_id, user_id, date_started) "
                                   "VALUES (?, ?, strftime('%s','now'))", (file_id, user_id))

    def get_file_ids(self, hw_num, number_of_files, user_id):
        return self.cursor.execute("SELECT hw.file_id, count(hw_checking.file_id) checks_count "
                                   "FROM hw "
                                   "LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL "
                                   "AND hw.hw_num = :hw_num AND hw.user_id != :usr_id "
                                   "GROUP BY hw.file_id "
                                   "ORDER BY checks_count "
                                   "LIMIT :num_files",
                                   {'hw_num': hw_num,
                                    'num_files': number_of_files,
                                    'usr_id': user_id}).fetchall()

    def save_mark(self, user_id, mark):
        return self.cursor.execute("UPDATE hw_checking SET mark = ?, date_checked=strftime('%s','now') "
                                   "WHERE user_id = ? AND file_id = "
                                   "(SELECT file_id FROM hw_checking "
                                   "WHERE user_id = ? ORDER BY date_started DESC LIMIT 1)", (mark, user_id, user_id))

    def get_num_checked(self, user_id):
        return self.cursor.execute("SELECT hw.hw_num, count(hw_checking.file_id) checks_count "
                                   "FROM hw LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL AND hw_checking.mark IS NOT NULL "
                                   "AND hw_checking.user_id = ?"
                                   "GROUP BY hw.hw_num ORDER BY checks_count ", (user_id,)).fetchall()

    def get_marks(self, user_id):
        return self.cursor.execute(
            "SELECT hw.hw_num, datetime(hw.date_added, 'unixepoch', 'localtime'), avg(hw_checking.mark) avg_mark "
            "FROM hw LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
            "WHERE hw.user_id = ? "
            "AND hw.file_id IS NOT NULL AND hw_checking.mark IS NOT NULL "
            "GROUP BY hw.date_added, hw.hw_num ORDER BY avg_mark", (user_id,)).fetchall()

    def get_checked_works_stat(self):
        return self.cursor.execute("SELECT hw.hw_num, count(hw_checking.file_id) checks_count "
                                   "FROM hw LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL AND hw_checking.mark IS NOT NULL "
                                   "GROUP BY hw.hw_num ORDER BY checks_count ").fetchall()

    def get_checks_for_every_work(self):
        return self.cursor.execute("SELECT hw.hw_num, hw.user_id, hw.file_id, "
                                   "count(hw_checking.file_id) checks, avg(hw_checking.mark) mark_avg "
                                   "FROM hw LEFT OUTER JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                   "WHERE hw.file_id IS NOT NULL "  # AND hw_checking.mark IS NOT NULL "
                                   "GROUP BY hw.file_id ORDER BY checks DESC ").fetchall()

    def write_quiz_ans(self, user_id: str,
                       quiz_name: str, question_name: str,
                       is_right: int, usr_ans: str,
                       question_text: str, true_ans: str):

        # TODO: check if username + quiz_num exists, then update existed
        return self.cursor.execute("INSERT INTO quizzes (user_id, quiz_name,"
                                   " question_name, is_right, usr_answer,"
                                   " question_text, true_ans, date_added) "
                                   "VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))",
                                   (user_id, quiz_name, question_name,
                                    is_right, usr_ans, question_text, true_ans))

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    sql = SQLighter(config.bd_name)
    # results = sql.get_checks_for_every_work()
    # df = pd.DataFrame(data=results, index=range(len(results)), columns=["hw_num", "usr", "file_id", "checks", "mark"])
    # df.to_csv("HW_STAT.csv")
    # print(df)
