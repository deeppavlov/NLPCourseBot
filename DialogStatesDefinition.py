from DialogClasses import *
from Sqlighter import SQLighter
import universal_reply
import config
import random
import pandas as pd
from quizzes.QuizClasses import Quiz
from tabulate import tabulate
from collections import OrderedDict
from telebot import util
import dill

wait_usr_interaction = State(name='WAIT_USR_INTERACTION',
                             triggers_out=OrderedDict(MAIN_MENU={'phrases': [' / start'], 'content_type': 'text'}))
# ----------------------------------------------------------------------------

main_menu = State(name='MAIN_MENU',
                  row_width=2,
                  triggers_out=OrderedDict(
                      TAKE_QUIZ={'phrases': [universal_reply.quiz_enter], 'content_type': 'text'},
                      PASS_HW_NUM_SELECT={'phrases': [universal_reply.hw_enter], 'content_type': 'text'},
                      CHECK_QUIZ={'phrases': [universal_reply.quiz_check], 'content_type': 'text'},
                      CHECK_HW_NUM_SELECT={'phrases': [universal_reply.hw_check], 'content_type': 'text'},
                      GET_QUIZ_MARK={'phrases': [universal_reply.quiz_estimates], 'content_type': 'text'},
                      GET_MARK={'phrases': [universal_reply.hw_estimates], 'content_type': 'text'},
                      ASK_QUESTION_START={'phrases': [universal_reply.ask_question], 'content_type': 'text'},
                      ADMIN_MENU={'phrases': [universal_reply.ADMIN_KEY_PHRASE], 'content_type': 'text'}),
                  hidden_states={'state_name': 'ADMIN_MENU', 'users_file': config.admins},
                  welcome_msg='Выберите доступное действие, пожалуйста')


# ----------------------------------------------------------------------------


class QuizState(State):
    def additional_init(self):
        self.quiz = Quiz(config.current_quiz_name, quiz_json_path=config.quiz_path,
                         next_global_state_name='MAIN_MENU')
        # TODO: do smth to provide arguments in the right way
        self.dump_path = config.dump_quiz_path

    def dump_current_states(self):
        with open(self.dump_path, 'wb') as fout:
            dill.dump({'usersteps': self.quiz.usersteps,
                       'submitted': self.quiz.usr_submitted,
                       'paused': self.quiz.paused,
                       'usr_buttons': {q.name: q.usr_buttons for q in self.quiz.questions},
                       'usr_answers': {q.name: q.usr_answers for q in self.quiz.questions}
                       }, fout)
            print('---- QUIZ dumped')

    def load_current_states(self):
        try:
            with open(self.dump_path, 'rb') as fin:
                unpickled = dill.load(fin)
                self.quiz.usersteps = unpickled['usersteps']
                self.quiz.usr_submitted = unpickled['submitted']
                self.quiz.paused = unpickled['paused']
                for q in self.quiz.questions:
                    q.usr_answers = unpickled['usr_answers'][q.name]
                    q.usr_buttons = unpickled['usr_buttons'][q.name]
        except FileNotFoundError:
            print('Quiz Load: FileNotFoundError')
            pass

    def make_reply_markup(self):
        pass

    def welcome_handler(self, bot, message, sqldb: SQLighter):
        result = self.quiz.run(bot, message, sqldb)
        if result == self.quiz.next_global_state_name:
            if not hasattr(self, 'back_keyboard'):
                self.back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                self.back_keyboard.add(types.KeyboardButton('Назад'))
            if config.quiz_closed:
                bot.send_message(text='Quiz closed', chat_id=message.chat.id, reply_markup=self.back_keyboard)
            else:
                bot.send_message(chat_id=message.chat.id,
                                 text="Sorry, you have already submitted {} ~_~\"".format(self.quiz.name),
                                 reply_markup=self.back_keyboard)

    def out_handler(self, bot, message, sqldb: SQLighter):
        if message.content_type != 'text':
            return None
        if message.text == 'Назад':
            return self.quiz.next_global_state_name
        new_state = self.quiz.run(bot, message, sqldb)
        return new_state


take_quiz = QuizState(name='TAKE_QUIZ')

# ----------------------------------------------------------------------------

check_quiz = State(name='CHECK_QUIZ',
                   triggers_out=OrderedDict(
                       SEND_QQUESTION_TO_CHECK={'phrases': config.quizzes_possible_to_check, 'content_type': 'text'},
                       MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'}),
                   welcome_msg='Пожалуйста, выберите номер квиза для проверки:')


# ----------------------------------------------------------------------------

def send_qquestion(bot, message, sqldb):
    if message.text not in config.quizzes_possible_to_check:
        quiz_name = sqldb.get_latest_quiz_name(message.chat.username)
    else:
        quiz_name = message.text
    if quiz_name is None:
        bot.send_message("SMTH WENT WRONG..")
        return

    num_checked = sqldb.get_number_checked_for_one_quiz(user_id=message.chat.username,
                                                        quiz_name=quiz_name)
    arr = sqldb.get_quiz_question_to_check(quiz_name=quiz_name,
                                           user_id=message.chat.username)
    if len(arr) > 0:
        q_id, q_name, q_text, q_user_ans, _ = arr
        sqldb.make_fake_db_record_quiz(q_id, message.chat.username)
        text = 'You have checked: {}/{}\n'.format(num_checked, config.quizzes_need_to_check) \
               + q_text + '\n' + 'USER_ANSWER:\n' + q_user_ans
        bot.send_message(chat_id=message.chat.id,
                         text=text, )
    else:
        # TODO: do smth with empty db;
        bot.send_message(text='К сожалению проверить пока нечего. Нажмите, пожалуйста, кнопку "Назад".',
                         chat_id=message.chat.id)


send_quiz_question_to_check = State(name='SEND_QQUESTION_TO_CHECK',
                                    row_width=2,
                                    triggers_out=OrderedDict(SAVE_MARK={'phrases': ['Верю', 'Не верю']},
                                                             MAIN_MENU={'phrases': ['Назад'],
                                                                        'content_type': 'text'}),
                                    handler_welcome=send_qquestion,
                                    welcome_msg='🌻 Правильно или нет ответил пользователь?\n'
                                                'Нажмите кнопку, чтобы оценить ответ.')


# ----------------------------------------------------------------------------

def mark_saving_quiz(bot, message, sqldb):
    is_right = int(message.text == 'Верю')
    sqldb.save_mark_quiz(message.chat.username, is_right)
    bot.send_message(text='Оценка сохранена. Спасибо.', chat_id=message.chat.id)


save_mark_quiz = State(name='SAVE_MARK',
                       row_width=2,
                       triggers_out=OrderedDict(SEND_QQUESTION_TO_CHECK={'phrases': ['Продолжить проверку']},
                                                CHECK_QUIZ={'phrases': ['Назад']}),
                       handler_welcome=mark_saving_quiz,
                       welcome_msg='🌻 Желаете ли еще проверить ответы из того же квиза?')

# ----------------------------------------------------------------------------

ask_question_start = State(name='ASK_QUESTION_START',
                           triggers_out=OrderedDict(MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'},
                                                    SAVE_QUESTION={'phrases': [], 'content_type': 'text'}),
                           welcome_msg='Сформулируйте вопрос к семинаристу и отправьте его одним сообщением 🐠.')


# ----------------------------------------------------------------------------

def save_question_handler(bot, message, sqldb):
    sqldb.write_question(message.chat.username, message.text)


save_question = State(name='SAVE_QUESTION',
                      triggers_out=OrderedDict(MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'},
                                               SAVE_QUESTION={'phrases': [], 'content_type': 'text'}),
                      handler_welcome=save_question_handler,
                      welcome_msg='Спасибо за вопрос. Хорошего дня 🐯 :)\n'
                                  'Если желаете задать еще вопрос, напишите его сразу следующим сообщением.'
                                  'Если у вас нет такого желания, воспользуйтесь кнопкой "Назад".')

# ----------------------------------------------------------------------------

welcome_to_pass_msg = 'Пожалуйста, выберите номер задания для сдачи.'
welcome_to_return_msg = 'Доступные для сдачи задания отсутствуют.'
pass_hw_num_selection = State(name='PASS_HW_NUM_SELECT',
                              row_width=2,
                              triggers_out=OrderedDict(PASS_HW_CHOSEN_NUM={'phrases': config.hw_possible_to_pass,
                                                                           'content_type': 'text'},
                                                       MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'}),
                              welcome_msg=welcome_to_pass_msg if len(config.hw_possible_to_pass) > 0
                              else welcome_to_return_msg)


# ----------------------------------------------------------------------------

def make_fake_db_record(bot, message, sqldb):
    sqldb.make_fake_db_record(message.chat.username, message.text)


pass_hw_chosen_num = State(name='PASS_HW_CHOSEN_NUM',
                           triggers_out=OrderedDict(PASS_HW_UPLOAD={'phrases': [], 'content_type': 'document'},
                                                    PASS_HW_NUM_SELECT={'phrases': ['Назад'], 'content_type': 'text'}),
                           handler_welcome=make_fake_db_record,
                           welcome_msg='Пришлите файл **(один архив или один Jupyter notebook)** весом не более 20 Мб.')


# ----------------------------------------------------------------------------

class HwUploadState(State):
    def welcome_handler(self, bot, message, sqldb: SQLighter):
        username = message.chat.username
        if not message.document.file_name.endswith(config.available_hw_resolutions):
            tmp_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            tmp_markup.add(types.KeyboardButton('Меню'))
            bot.send_message(message.chat.id, "🚫 {}, очень жаль но файлик не сдается в нашу систему...\n"
                                              "Возможны следующие расширения файлов: {}.\n"
                                              "Напоминаю, что дз сдается в виде одного файла архива"
                                              " или одного Jupyter ноутбука."
                             .format(username.title(), str(config.available_hw_resolutions)), reply_markup=tmp_markup)
        else:
            sqldb.upd_homework(user_id=username, file_id=message.document.file_id)
            bot.send_message(message.chat.id,
                             'Уважаемый *{}*, ваш файлик был заботливо сохранен 🐾\n'
                             .format(username.title()),
                             reply_markup=self.reply_markup, parse_mode='Markdown')

    def out_handler(self, bot, message, sqldb: SQLighter):
        for state_name, attribs in self.triggers_out.items():
            if message.content_type == 'document':
                return self.welcome_handler(bot, message, sqldb)

            elif (message.content_type == 'text') and (message.text in attribs['phrases']):
                return state_name
        return self.default_out_handler(bot, message)


pass_hw_upload = HwUploadState(name='PASS_HW_UPLOAD',
                               triggers_out=OrderedDict(
                                   PASS_HW_NUM_SELECT={'phrases': ['Сдать еще одно дз'], 'content_type': 'text'},
                                   MAIN_MENU={'phrases': ['Меню'], 'content_type': 'text'}))


# ----------------------------------------------------------------------------


def show_marks_table(bot, message, sqldb):
    num_checked = sqldb.get_num_checked(message.chat.username)
    if len(num_checked) == 0:
        bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                          'вам нужно проверить как минимум 3 работы'
                                          ' из каждого сданного вами задания, '
                                          'чтобы узнать свою оценку по данному заданию. '
                                          'На текущий момент вы не проверили ни одно задание :(.'.format(
            message.chat.username.title()),
                         parse_mode='Markdown')
    else:
        may_be_shown = []
        for num, count in num_checked:
            if count < 3:
                bot.send_message(message.chat.id, '👻 Для того чтобы узнать оценку по заданию {}'
                                                  ' вам нужно проверить еще вот столько [{}]'
                                                  ' заданий этого семинара.'.format(num, 3 - count))
            else:
                may_be_shown.append(num)

        if len(may_be_shown) == 0:
            return

        marks = sqldb.get_marks(message.chat.username)
        if len(marks) < 1:
            bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                              'ваши работы еще не были проверены ни одним разумным существом.\n'
                                              'Остается надеяться и верить в лучшее 🐸'.format(
                message.chat.username.title()),
                             parse_mode='Markdown')
        else:
            count_what_show = 0
            ans = '_Ваши оценки следующие_\n'
            for hw_num, date, mark in marks:
                if hw_num in may_be_shown:
                    count_what_show += 1
                    ans += '🐛 Для работы *' + hw_num + '*, загруженной *' + date + '* оценка: *' + str(
                        round(mark, 2)) + '*\n'
            if count_what_show > 0:
                bot.send_message(message.chat.id, ans, parse_mode='Markdown')
                bot.send_message(message.chat.id, 'Если какой-то работы нет в списке, значит ее еще не проверяли.')
            else:
                bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                                  'ваши работы по проверенным вами заданиям еще не были проверены'
                                                  ' ни одним разумным существом.\n'
                                                  'Остается надеяться и верить в лучшее 🐸 '
                                                  '(_или написать оргам и заставить их проверить_)'.format(
                    message.chat.username.title()),
                                 parse_mode='Markdown')


get_mark = State(name='GET_MARK',
                 triggers_out=OrderedDict(MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'}),
                 handler_welcome=show_marks_table,
                 welcome_msg='Такие дела)')


# ----------------------------------------------------------------------------
def get_marks_table_quiz(bot, message, sqldb):
    num_checked = sqldb.get_number_checked_quizzes(message.chat.username)
    for quiz_name, num in num_checked:
        if num < config.quizzes_need_to_check and quiz_name in config.quizzes_possible_to_check:
            bot.send_message(chat_id=message.chat.id,
                             text='🌳🌻 Вы проверили {} квизов для {}. '
                                  'Необходимо проверить еще {} квизов,'
                                  ' чтобы узнать свою оценку по этому квизу.'.format(num, quiz_name,
                                                                            config.quizzes_need_to_check - num))
            return
        df = sqldb.get_marks_quiz(user_id=message.chat.username, quiz_name=quiz_name)
        if df.empty:
            bot.send_message(chat_id=message.chat.id,
                             text="Пока никто не проверил ваш квиз {} или вы его вообще не сдавали.\n"
                                  "Возвращайтесь позже.🌳🌻 ".format(quiz_name))
            return
        finals = defaultdict(list)
        for i, row in df.iterrows():
            text = '*' + quiz_name + '*\n' + '=' * 20 + '\n'
            text += row.QuestionText + '\n' + '=' * 20 + '\n' + '*Your Answer: *\n' \
                    + str(row.YourAnswer) + '\n*Score: *' + str(row.Score)
            if not pd.isna(row.NumChecks):
                text += '\n*Checked for [{}] times*'.format(row.NumChecks)
            bot.send_message(text=text, chat_id=message.chat.id, parse_mode='Markdown')
        final_score = int(sum(df.Score)) if (not pd.isna(sum(df.Score))) else 0
        mark = '{}/{}'.format(final_score, len(df))
        finals['quiz'].append(quiz_name)
        finals['mark'].append(mark)
        bot.send_message(text='<code>' + tabulate(finals, headers='keys', tablefmt="fancy_grid") + '</code>',
                         chat_id=message.chat.id, parse_mode='html')


get_quiz_mark = State(name='GET_QUIZ_MARK',
                      triggers_out=OrderedDict(MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'}),
                      handler_welcome=get_marks_table_quiz,
                      welcome_msg='Good Luck:)')

# ----------------------------------------------------------------------------

welcome_check_hw = 'Выберите номер задания для проверки' if len(config.hw_possible_to_check) > 0 \
    else 'Нет доступных для проверки заданий. Выпейте чаю, отдохните.'
check_hw_num_selection = State(name='CHECK_HW_NUM_SELECT', triggers_out=OrderedDict(
    CHECK_HW_SEND={'phrases': config.hw_possible_to_check, 'content_type': 'text'},
    MAIN_MENU={'phrases': ['Назад'], 'content_type': 'text'}),
                               welcome_msg=welcome_check_hw,
                               row_width=2)


# ----------------------------------------------------------------------------

def choose_file_and_send(bot, message, sqldb):
    # TODO: do smth to fix work with empty hw set;
    # TODO: OH MY GOD! people should check only work that they have done!!!!

    file_ids = sqldb.get_file_ids(hw_num=message.text,
                                  number_of_files=3,
                                  user_id=message.chat.username)
    if len(file_ids) > 0:
        chosen_file = random.choice(file_ids)[0]
        sqldb.write_check_hw_ids(message.chat.username, chosen_file)
        bot.send_document(message.chat.id, chosen_file)
    else:
        print("ERROR! empty sequence")
        pass


check_hw_send = State(name='CHECK_HW_SEND',
                      triggers_out=OrderedDict(CHECK_HW_SAVE_MARK={'phrases': config.marks,
                                                                   'content_type': 'text'},
                                               MAIN_MENU={'phrases': ['Меню'], 'content_type': 'text'}),
                      handler_welcome=choose_file_and_send,
                      row_width=3,
                      welcome_msg="Пожалуйста, оцените работу.")


# ----------------------------------------------------------------------------

def save_mark(bot, message, sqldb):
    sqldb.save_mark(message.chat.username, message.text)


check_hw_save_mark = State(name='CHECK_HW_SAVE_MARK',
                           triggers_out=OrderedDict(CHECK_HW_NUM_SELECT={'phrases': ['Проверить еще одну работу'],
                                                                         'content_type': 'text'},
                                                    MAIN_MENU={'phrases': ['Меню'], 'content_type': 'text'}),
                           welcome_msg='Спасибо за проверенную работу:)',
                           handler_welcome=save_mark)

# ----------------------------------------------------------------------------

admin_menu = State(name='ADMIN_MENU',
                   row_width=3,
                   triggers_out=OrderedDict(KNOW_NEW_QUESTIONS={'phrases': ['Questions'], 'content_type': 'text'},
                                            SEE_HW_STAT={'phrases': ['Homeworks'], 'content_type': 'text'},
                                            SEE_QUIZZES_STAT={'phrases': ['Quizzes'], 'content_type': 'text'},
                                            MAIN_MENU={'phrases': ['MainMenu'], 'content_type': 'text'},
                                            MAKE_BACKUP={'phrases': ['MakeBackup'], 'content_type': 'text'}),
                   welcome_msg='Добро пожаловать, о Великий Одмен!')


# ----------------------------------------------------------------------------

def make_backup_now(bot, message, sqldb):
    return 'BACKUP_NOW'


make_backup = State(name='MAKE_BACKUP',
                    triggers_out=OrderedDict(ADMIN_MENU={'phrases': ['Назад в админку'],
                                                         'content_type': 'text'}),
                    handler_welcome=make_backup_now,
                    welcome_msg='Working on pickling objects...')


# ----------------------------------------------------------------------------

def get_quizzes_stat(bot, message, sqldb):
    for quiz_name in config.quizzes_possible_to_check:
        quizzes_stat = sqldb.get_quizzes_stat(quiz_name)
        bot.send_message(text="*FOR {}*".format(quiz_name),
                         chat_id=message.chat.id,
                         parse_mode='Markdown')
        bot.send_message(
            text='<code>' + tabulate(pd.DataFrame(quizzes_stat, index=[0]).T, tablefmt="fancy_grid") + '</code>',
            chat_id=message.chat.id, parse_mode='html')


see_quizzes_stat = State(name='SEE_QUIZZES_STAT',
                         triggers_out=OrderedDict(ADMIN_MENU={'phrases': ['Назад в админку'],
                                                              'content_type': 'text'}),
                         handler_welcome=get_quizzes_stat,
                         welcome_msg='Это все 👽')


# ----------------------------------------------------------------------------

def get_questions(bot, message, sqldb):
    questions = sqldb.get_questions_last_week()
    if len(questions) > 0:
        res = '*Questions for the last week*\n'
        for user_id, question, date in questions:
            res += '👽 User: *' + user_id + '* asked at *' + date + '*:\n' + question + '\n\n'
        # Split the text each 3000 characters.
        # split_string returns a list with the splitted text.
        splitted_text = util.split_string(res, 3000)
        for text in splitted_text:
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, '_Нет ничего новенького за последние 7 дней, к сожалению_:(',
                         parse_mode='Markdown')


know_new_questions = State(name='KNOW_NEW_QUESTIONS',
                           triggers_out=OrderedDict(ADMIN_MENU={'phrases': ['Назад в админку'],
                                                                'content_type': 'text'}),
                           handler_welcome=get_questions,
                           welcome_msg='Это все 👽')


# ----------------------------------------------------------------------------

def get_hw_stat(bot, message, sqldb):
    hw_stat = sqldb.get_checked_works_stat()
    if len(hw_stat) == 0:
        bot.send_message(message.chat.id, "Нет проверенных домашек совсем:( Грусть печаль.")
    else:
        ans = '_Количество проверенных работ на каждое задание_\n'
        for sem, count in hw_stat:
            ans += sem + '\t' + str(count) + '\n'
        bot.send_message(message.chat.id, ans, parse_mode='Markdown')


see_hw_stat = State(name='SEE_HW_STAT',
                    triggers_out=OrderedDict(ADMIN_MENU={'phrases': ['Назад в админку'], 'content_type': 'text'}),
                    handler_welcome=get_hw_stat,
                    welcome_msg='Это все что есть проверенного.\nЕсли какого номера тут нет, значит его не проверили.')

# ----------------------------------------------------------------------------
