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

            self.cursor.execute("CREATE TABLE quizzes ( "
                                "user_id	TEXT, "
                                "question_name	TEXT, "
                                "quiz_name	TEXT, "
                                "question_text TEXT, "
                                "true_ans TEXT, "
                                "is_right	INTEGER, "
                                "usr_answer	TEXT, "
                                "date_added INTEGER, "
                                "id INTEGER PRIMARY KEY AUTOINCREMENT );")
            self.cursor.execute("CREATE TABLE quizzes_checking ( "
                                "checker_user_id TEXT, "
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

    def make_fake_db_record_quiz(self, q_id, user_id):
        """ Make empty record for this quiz_name & user_id"""
        self.cursor.execute("INSERT INTO quizzes_checking (checker_user_id, id_quizzes, date_started)"
                            " VALUES (?, ?, strftime('%s','now'))", (user_id, q_id))

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

    def get_latest_quiz_name(self, user_id):
        result = self.cursor.execute("SELECT quizzes.quiz_name "
                                     "FROM quizzes LEFT OUTER JOIN quizzes_checking "
                                     "ON quizzes.id = quizzes_checking.id_quizzes "
                                     "WHERE quizzes_checking.checker_user_id = ? "
                                     "AND quizzes_checking.is_right IS NOT NULL "
                                     "GROUP BY quizzes.quiz_name "
                                     "ORDER BY quizzes_checking.date_checked DESC LIMIT 1", (user_id,)).fetchall()
        if len(result) > 0:
            return result[0][0]

    def get_number_checked_quizzes(self, user_id, quiz_name):
        result = self.cursor.execute("SELECT count(quizzes_checking.id_quizzes) "
                                     "FROM quizzes_checking JOIN quizzes ON quizzes.id=quizzes_checking.id_quizzes "
                                     "WHERE checker_user_id = ? AND quizzes.quiz_name = ?"
                                     "AND quizzes_checking.is_right IS NOT NULL", (user_id, quiz_name)).fetchall()
        if len(result) > 0:
            return result[0][0]
        return 0

    def get_quiz_question_to_check(self, quiz_name, user_id):
        # TODO: fix processing of '' user answers;
        array = self.cursor.execute(
            "SELECT quizzes.id, quizzes.question_name, quizzes.question_text, quizzes.usr_answer, "
            "count(quizzes_checking.id_quizzes) checks "
            "FROM quizzes LEFT OUTER JOIN quizzes_checking "
            "ON quizzes.id = quizzes_checking.id_quizzes "
            "WHERE quizzes.user_id != ? "
            "AND quizzes.quiz_name = ? "
            "AND quizzes.usr_answer IS NOT NULL "
            # "AND quizzes.usr_answer IS NOT '' "
            "AND quizzes.true_ans IS NULL "
            # "AND quizzes_checking.checker_user_id != ?"
            "GROUP BY quizzes.id ORDER BY checks ASC LIMIT 1", (user_id, quiz_name,)).fetchall()
        if len(array) > 0:
            return array[0]
        return array

    def save_mark(self, user_id, mark):
        return self.cursor.execute("UPDATE hw_checking SET mark = ?, date_checked=strftime('%s','now') "
                                   "WHERE user_id = ? AND file_id = "
                                   "(SELECT file_id FROM hw_checking "
                                   "WHERE user_id = ? ORDER BY date_started DESC LIMIT 1)", (mark, user_id, user_id))

    def save_mark_quiz(self, user_id, mark):
        self.cursor.execute("UPDATE quizzes_checking SET is_right = ?, date_checked=strftime('%s','now') "
                            "WHERE checker_user_id = ? AND id_quizzes = "
                            "(SELECT id_quizzes FROM quizzes_checking "
                            "WHERE checker_user_id = ? ORDER BY date_started DESC LIMIT 1)",
                            (mark, user_id, user_id))
        self.connection.commit()

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

    def get_marks_quiz(self, user_id):
        automarks = self.cursor.execute(
            "SELECT quiz_name, "
            "question_name, "
            "quizzes.question_text, "
            "usr_answer, "
            "is_right "
            # "datetime(quizzes.date_added, 'unixepoch', 'localtime') "
            "FROM quizzes WHERE user_id = ? AND true_ans IS NOT NULL", (user_id,)).fetchall()
        cross_marks = self.cursor.execute(
            "SELECT quizzes.quiz_name, "
            "quizzes.question_name,"
            "quizzes.question_text, "
            "quizzes.usr_answer, "
            "round(avg(quizzes_checking.is_right),0), "
            "count(quizzes_checking.is_right) "
            # " datetime(quizzes.date_added, 'unixepoch', 'localtime') "
            "FROM quizzes LEFT JOIN quizzes_checking ON quizzes.id = quizzes_checking.id_quizzes "
            "WHERE quizzes.user_id = ? "
            "AND quizzes.true_ans IS NULL "
            "AND quizzes_checking.is_right IS NOT NULL "
            "GROUP BY quizzes.id ORDER BY quizzes.quiz_name", (user_id,)).fetchall()

        if len(cross_marks) < 1:
            # in case of nothing checked:
            return pd.DataFrame()

        automarks.extend(cross_marks)
        marks = pd.DataFrame(automarks, columns=['Quiz', 'Question', 'QuestionText',
                                                 'YourAnswer', 'Score', 'NumChecks'])
        marks.sort_values(by=['Quiz', 'Question'], inplace=True)
        marks['Question'] = marks['Question'].apply(lambda x: x[-1:])
        return marks

    def get_quizzes_stat(self, quiz_name):
        unique_people_passed = self.cursor.execute("SELECT count(quizzes.user_id) "
                                                   "FROM quizzes WHERE quiz_name = ?", (quiz_name,)).fetchall()
        unique_people_passed = unique_people_passed[0][0] if len(unique_people_passed) > 0 else 0

        quizzes_more3_checked = self.cursor.execute("SELECT quizzes.user_id, "
                                                    "avg(B.check_nums), count(B.check_nums) "
                                                    "FROM quizzes INNER JOIN "
                                                    "(SELECT quizzes_checking.id_quizzes, "
                                                    "count(quizzes_checking.date_checked) check_nums "
                                                    "FROM quizzes_checking "
                                                    "GROUP BY quizzes_checking.id_quizzes) B "
                                                    "ON quizzes.id = B.id_quizzes "
                                                    "WHERE quizzes.quiz_name = ? "
                                                    "AND B.check_nums >= 3 GROUP BY quizzes.user_id",
                                                    (quiz_name,)).fetchall()

        quizzes_checked_all = self.cursor.execute("SELECT quizzes.user_id, "
                                                  "avg(B.check_nums), count(B.check_nums) "
                                                  "FROM quizzes INNER JOIN "
                                                  "(SELECT quizzes_checking.id_quizzes, "
                                                  "count(quizzes_checking.date_checked) check_nums "
                                                  "FROM quizzes_checking "
                                                  "GROUP BY quizzes_checking.id_quizzes) B "
                                                  "ON quizzes.id = B.id_quizzes "
                                                  "WHERE quizzes.quiz_name = ? "
                                                  "AND B.check_nums >= 1 GROUP BY quizzes.user_id",
                                                  (quiz_name,)).fetchall()

        num_people_checked_one_question = self.cursor.execute("SELECT count(DISTINCT quizzes_checking.checker_user_id) "
                                                              "FROM quizzes_checking LEFT JOIN quizzes "
                                                              "ON quizzes.id = quizzes_checking.id_quizzes "
                                                              "WHERE quizzes.quiz_name = ? "
                                                              "AND quizzes_checking.is_right IS NOT NULL",
                                                              (quiz_name,)).fetchall()
        num_people_checked_one_question = num_people_checked_one_question[0][0] if len(
            num_people_checked_one_question) > 0 else 0

        return {'num_unique_people': unique_people_passed,
                'num_truly_checked_quizzes': len(quizzes_more3_checked),
                'num_all_checked_quizzes': len(quizzes_checked_all),
                'num_people_checkers': num_people_checked_one_question}

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
        # check existence:
        record = self.cursor.execute("SELECT * FROM quizzes "
                                     "WHERE quiz_name = ? AND question_name = ? AND user_id = ?",
                                     (quiz_name, question_name, user_id)).fetchall()
        # update if exists:
        if len(record) > 0:
            return self.cursor.execute("UPDATE quizzes SET is_right=?, usr_answer=?, "
                                       "date_added=strftime('%s','now')"
                                       " WHERE user_id=? AND quiz_name = ? AND question_name = ?",
                                       (is_right, usr_ans, user_id, quiz_name, question_name))
        else:
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
    # lol = sql.get_quizzes_stat(' 1')
    # print(lol)
