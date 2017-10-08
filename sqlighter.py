# -*- coding: utf-8 -*-

import sqlite3
import config


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def is_registered(self, user_id):
        """ Check if user registered """
        with self.connection:
            return len(self.cursor.execute("SELECT * FROM Registration WHERE user_id = ?", (user_id,)).fetchall()) > 0

    def add_homework(self, user_id, hw_num):
        """ Register user in bd """
        with self.connection:
            return self.cursor.execute("INSERT INTO hw (user_id, {})"
                                       " VALUES (?, 1)".format(hw_num), (user_id,))

    def get_user_name(self, user_id):
        """ Get user name """
        with self.connection:
            return \
            self.cursor.execute("SELECT user_name FROM Registration WHERE user_id = ?", (user_id,)).fetchall()[0][0]

    def register(self, user_id, user_name):
        """ Register user in bd """
        with self.connection:
            return self.cursor.execute("INSERT INTO Registration (user_id, user_name)"
                                       " VALUES (?, ?)", (user_id, user_name))

    def select_all_for_this_week(self):
        """ Get all questions for the current week """
        with self.connection:
            return self.cursor.execute("SELECT * FROM Questions WHERE date_added >= date('now','-5 day')").fetchall()

    def select_all_for_users(self, user_id):
        """ Get all questions from that user """
        with self.connection:
            return self.cursor.execute('SELECT * FROM Questions WHERE user_id = ?', (user_id,)).fetchall()

    def select_last_n_days(self, user_id, n):
        """ Get only fresh questions from last n days """
        with self.connection:
            return self.cursor.execute("SELECT * FROM Questions WHERE (user_id = ?) AND "
                                       "(date_added >= date('now','-{} day'))".format(n), (user_id,)).fetchall()

    def count_users_questions(self, user_id):
        """ Get number of user's questions """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM Questions WHERE user_id = ?', (user_id,)).fetchall()
            return len(result)

    def write_question(self, user_id, question):
        """ Insert question into BD """
        with self.connection:
            return self.cursor.execute("INSERT INTO Questions (user_id, question, date_added)"
                                       " VALUES (?, ?, date('now'))", (user_id, question))

    def close(self):
        """ Close current connection with DB """
        self.connection.close()


if __name__ == '__main__':
    sql = SQLighter(config.bd_name)
    # sql.write_question(12, "Lolol")
    # sql.write_question(13, "Lolorel")
    # sql.write_question(14, "Lololdfg")
    # sql.write_question(12, "Lolol43")
    # print(sql.count_rows(12))
    # print(sql.select_all(12))
    # print(sql.select_last_n_days(13, 3))
    print(sql.is_registered(61023330))
    print(sql.get_user_name(61023330))
