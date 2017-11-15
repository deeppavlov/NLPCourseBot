# -*- coding: utf-8 -*-

import sqlite3
import config

class SQLighter:
    def __init__(self, database_file_path):
        self.connection = sqlite3.connect(database_file_path)
        self.cursor = self.connection.cursor()

    # def check_hw_date(self, user_id, hw_num, course):
    #     """ Check if that hw_num is exists for user_id """
    #     with self.connection:
    #         return self.cursor.execute("SELECT datetime(date, 'unixepoch') FROM hw WHERE (user_id = ?) AND (hw_num = ?) AND (course = ?)",
    #                                    (user_id, hw_num, course)).fetchall()
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
                                "WHERE user_id = ? AND hw_num = "
                                "(SELECT hw_num FROM hw WHERE user_id = ? ORDER BY date DESC LIMIT 1)",
                                (file_id, user_id, user_id))

    def write_check_hw_ids(self, user_id, file_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO hw_checking (file_id, user_id) "
                                       "VALUES (?, ?)", (file_id, user_id))

    def get_file_ids(self, hw_num, number_of_files):
        with self.connection:
            return self.cursor.execute("SELECT hw.file_id, count(hw_checking.file_id) checks_count "
                                       "FROM hw "
                                       "LEFT JOIN hw_checking ON hw.file_id = hw_checking.file_id "
                                       "WHERE hw.file_id IS NOT NULL "
                                       "AND hw.hw_num = :hw_num "
                                       "GROUP BY hw.file_id "
                                       "ORDER BY checks_count "
                                       "LIMIT 5",
                                       {'hw_num': hw_num,
                                        'num_files': number_of_files}).fetchall()


if __name__ == '__main__':
    sql = SQLighter(config.bd_name)

    # print(type(pd_df))
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.add_homework(232, 'sem2', 'dfgsdfe54df')
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.upd_homework(232, 'sem2', 'ersSDFgsresrEr34')
    # print(sql.is_exists_hw(232, 'sem2'))
    # sql.write_question(34, 'sdfgserge dfgs')
    # print(sql.select_questions_last_n_days(3))
