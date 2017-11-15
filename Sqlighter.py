# -*- coding: utf-8 -*-

import sqlite3
import config
import pandas as pd

class SQLighter:
    def __init__(self, database_file_path):
        self.connection = sqlite3.connect(database_file_path)
        self.cursor = self.connection.cursor()

    # def check_hw_date(self, user_id, hw_num, course):
    #     """ Check if that hw_num is exists for user_id """
    #     with self.connection:
    #         return self.cursor.execute("SELECT datetime(date, 'unixepoch') FROM hw WHERE (user_id = ?) AND (hw_num = ?) AND (course = ?)",
    #                                    (user_id, hw_num, course)).fetchall()

    # def is_exists_hw(self, user_id, hw_num):
    #     """ Check if that hw_num is exists for user_id """
    #     with self.connection:
    #         return len(self.cursor.execute("SELECT * FROM hw WHERE (user_id = ?) AND (hw_num = ?)",
    #                                        (user_id, hw_num)).fetchall()) > 0
    #
    # def upd_homework(self, user_id, hw_num, file_id):
    #     """ UPD hw """
    #     with self.connection:
    #         return self.cursor.execute(
    #             "UPDATE hw SET file_id = ?, date = strftime('%s','now') WHERE (user_id = ?) AND (hw_num = ?)",
    #             (file_id, user_id, hw_num))
    #
    # def add_homework(self, user_id, hw_num, file_id):
    #     """ ADD hw """
    #     with self.connection:
    #         return self.cursor.execute(
    #             "INSERT INTO hw (file_id, user_id, hw_num, date) VALUES (?, ?, ?, strftime('%s','now'))",
    #             (file_id, user_id, hw_num))
    #
    # def select_questions_last_n_days(self, n_days):
    #     """ Get only fresh questions from last n days """
    #     with self.connection:
    #         return self.cursor.execute("SELECT question FROM Questions WHERE "
    #                                    "(date_added >= strftime('%s','now','-{} day'))".format(n_days)).fetchall()

    def write_question(self, user_id, question):
        """ Insert question into BD """
        with self.connection:
            self.cursor.execute("INSERT INTO Questions (user_id, question, date_added)"
                                       " VALUES (?, ?, strftime('%s','now'))", (user_id, question))

    def make_fake_db_record(self, user_id, hw_number):
        """ Make empty record for this hw_number """
        with self.connection:
            self.cursor.execute("INSERT INTO hw (user_id, hw_num, date)"
                                " VALUES (?, ?, strftime('%s','now'))", (user_id, hw_number))

    def upd_homework(self, user_id, file_id):
        """ UPD the latest record of user_id with file_id """
        with self.connection:
            self.cursor.execute("UPDATE hw SET file_id = ?, date = strftime('%s','now') "
                                "WHERE (user_id = ?) AND (hw_num = "
                                "(SELECT hw_num FROM hw WHERE (user_id = ?) ORDER BY date DESC LIMIT 1))",
                (file_id, user_id, user_id))

    # def write_overall_mark(self, user_id):
    #     """  """
    #     pass
    #
    # def get_all_hw(self):
    #     with self.connection:
    #         df = pd.DataFrame(self.cursor.execute("SELECT * FROM hw").fetchall(),
    #                             columns=['user_id', 'hw_num', 'date',
    #                                      'course', 'file_id', 'mark1',
    #                                      'mark2', 'mark3', 'overall'])
    #     df['date'] = pd.to_datetime(df['date'], unit='s')
    #     return df


if __name__ == '__main__':
    sql = SQLighter(config.bd_name)
    pd_df = sql.get_all_hw()
    print(pd_df)

    # print(type(pd_df))
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.add_homework(232, 'sem2', 'dfgsdfe54df')
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.upd_homework(232, 'sem2', 'ersSDFgsresrEr34')
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.write_question(34, 'sdfgserge dfgs')
    # print(sql.select_questions_last_n_days(3))
