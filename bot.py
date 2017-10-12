# -*- coding: utf-8 -*-
import telebot
from telebot import types
import config
from sqlighter import SQLighter
from collections import defaultdict

bot = telebot.TeleBot(config.token)

markup_cleared = types.ReplyKeyboardRemove()

markup_ask_again = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_ask_again.row('Задать еще один вопрос')
markup_ask_again.row('Вернуться назад')

markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_back.row('Вернуться назад')

markup_course = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_course.row('🐟 RL 🐟')
markup_course.row('🐸 NLP 🐸')

markup_hw_q = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_hw_q.row('🦉 Задать вопрос к семинару 🦉')
markup_hw_q.row('🐌 Сдать домашку 🐌')
markup_hw_q.row('Вернуться в начало')

states = defaultdict(dict)


@bot.message_handler(content_types=['text', 'document', 'photo'])
def handler(message):
    global states
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if message.chat.username is None:
        username_error(message)
        return

    elif message.chat.id not in states:
        clear_state(message, states)
        default_callback(message, states)

    elif states[chat_id]['currentState'] == 'WAIT_USER_INTERACTION':
        default_callback(message, states)

    elif (states[chat_id]['currentState'] == 'COURSE_SELECTION') and (message.text in ['🐟 RL 🐟', '🐸 NLP 🐸']):
        states[chat_id]['currentState'] = 'HW_OR_QUESTION_SELECTION'
        states[chat_id]['course'] = message.text.split()[1]
        choose_question_or_hw(message)

    elif (states[chat_id]['currentState'] == 'HW_OR_QUESTION_SELECTION') and \
            (message.text in ['🦉 Задать вопрос к семинару 🦉', '🐌 Сдать домашку 🐌']):
        if message.text == '🦉 Задать вопрос к семинару 🦉':
            question_handler(message)
            states[chat_id]['currentState'] = 'IN_QUESTION'

        elif message.text == '🐌 Сдать домашку 🐌':
            hw_handler(message)
            states[chat_id]['currentState'] = 'HW_NUM_SELECTION'

    elif (states[chat_id]['currentState'] == 'IN_QUESTION') and \
            (message.text != 'Вернуться в начало') and (message.content_type == 'text'):
        if message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'HW_OR_QUESTION_SELECTION'
            choose_question_or_hw(message)
        elif message.text == 'Задать еще один вопрос':
            question_handler(message)
        else:
            question_saver(message, course=states[chat_id]['course'])

    elif (states[chat_id]['currentState'] == 'HW_NUM_SELECTION') and (message.content_type == 'text') and \
            ((message.text in config.possible_to_pass[states[chat_id]['course']]) or (message.text == 'Вернуться назад')):
        if message.text in config.possible_to_pass[states[chat_id]['course']]:
            states[chat_id]['currentState'] = 'IN_HW_UPLOAD'
            states[chat_id]['hw_num'] = message.text
            hw_waiter(message)
        elif message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'HW_OR_QUESTION_SELECTION'
            choose_question_or_hw(message)

    elif (states[chat_id]['currentState'] == 'IN_HW_UPLOAD') and \
            ((message.content_type in ['document', 'photo']) or message.text == 'Вернуться назад'):
        if message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'HW_NUM_SELECTION'
            hw_handler(message)
        else:
            hw_saver(message, states)
    else:
        print('DEFAULT')
        default_callback(message, states)

    print(states)


# use this function as default handler
def default_callback(message, states):
    if message.text == '/start':
        bot.send_message(message.chat.id,
                         'WELCOME, *{}*!\nCHOOSE YOUR DESTINY!'.format(message.chat.username.upper()),
                         reply_markup=markup_course, parse_mode='Markdown')
        clear_state(message, states, set_state='COURSE_SELECTION')

    elif message.text == '/help':
        bot.send_message(message.chat.id,
                         'Привет, {}!\nЯ умею принимать вопросы к семинарам и файлы с дз по курсам NLP & RL.\n'
                         'Другие мои возможности находятся в разработке. Чтобы приступить к работе выберите курс.'
                         .format(message.chat.username.title()),
                         reply_markup=markup_course)

    elif message.text == 'Вернуться в начало':
        bot.send_message(message.chat.id,
                         'HERE AGAIN, *{}*!\nCHOOSE YOUR DESTINY!'.format(message.chat.username.upper()),
                         reply_markup=markup_course, parse_mode='Markdown')
        clear_state(message, states, set_state='COURSE_SELECTION')

    else:
        bla_bla_detected(message)
        clear_state(message, states)


def clear_state(message, states, set_state='WAIT_USER_INTERACTION'):
    states[message.chat.id]['currentState'] = set_state
    states[message.chat.id]['course'] = None
    states[message.chat.id]['hw_num'] = None


def username_error(message):
    bot.send_message(message.chat.id,
                     'Для продолжения работы с ботом, пожалуйста, запилите себе username в настройках телеграм!',
                     reply_markup=markup_cleared)


def choose_question_or_hw(message):
    bot.send_message(message.chat.id, 'Выберите доступное действие, пожалуйста 🦊', reply_markup=markup_hw_q)


# Задать вопрос к семинару
def question_handler(message):
    bot.send_message(message.chat.id, 'Сформулируйте вопрос к семинаристу и отправьте его одним сообщением 🦊.',
                     reply_markup=markup_back)


# Сдать домашку
def hw_handler(message):
    markup_hw = make_hw_keyboard(states[message.chat.id]['course'])
    bot.send_message(message.chat.id, 'Пожалуйста, выберите из списка доступных для сдачи заданий.',
                     reply_markup=markup_hw)


# hw -- выбор домашки
def hw_waiter(message):
    bot.send_message(message.chat.id, 'Пришлите файл **(один архив или один Jupyter notebook)** весом не более 20 Мб.',
                     reply_markup=markup_back, parse_mode='Markdown')


# hw -- сохранение файла домашки
def hw_saver(message, states):
    username = message.chat.username

    if message.content_type == 'photo':
        bot.send_message(message.chat.id, "{}, красивая картиночка, но она не похожа на домашку 🚫\n"
                                          "Наши преподаватели предпочитают следующие расширения: {}.\n"
                                          "Напоминаю, что дз сдается в виде одного файла архива или одного Jupyter ноутбука."
                         .format(username.title(), str(config.available_hw_resolutions)))
        return

    if not message.document.file_name.endswith(config.available_hw_resolutions):
        bot.send_message(message.chat.id, "🚫 {}, очень жаль но файлик не сдается в нашу систему...\n"
                                          "Наши преподаватели предпочитают следующие расширения: {}.\n"
                                          "Напоминаю, что дз сдается в виде одного файла архива или одного Jupyter ноутбука."
                         .format(username.title(), str(config.available_hw_resolutions)))
        return

    hw_num = states[message.chat.id]['hw_num']
    course = states[message.chat.id]['course']
    markup_hw = make_hw_keyboard(course)
    sqldb = SQLighter(config.bd_name)
    if sqldb.is_exists_hw(user_id=username, hw_num=hw_num, course=course):
        sqldb.upd_homework(user_id=username, hw_num=hw_num, course=course, file_id=message.document.file_id)
        bot.send_message(message.chat.id, 'Уважаемый *{}*, ваше задание {} было обновлено. Хорошего дня:) 🐾\n'
                         .format(username.title(), hw_num),
                         reply_markup=markup_hw, parse_mode='Markdown')
    else:
        sqldb.add_homework(user_id=username, hw_num=hw_num, course=course, file_id=message.document.file_id)
        bot.send_message(message.chat.id, 'Уважаемый *{}*, ваш файлик был заботливо сохранен как задание {} 🐾\n'
                     .format(username.title(), hw_num),
                     reply_markup=markup_hw, parse_mode='Markdown')
    states[message.chat.id]['currentState'] = 'HW_NUM_SELECTION'
    states[message.chat.id]['hw_num'] = None

# Сохранение вопроса к семинару
def question_saver(message, course):
    sqldb = SQLighter(config.bd_name)
    sqldb.write_question(user_id=message.chat.username, question=message.text, course=course)
    bot.send_message(message.chat.id, 'Спасибо за вопрос. Хорошего дня 🐯 :)\n'
                                      'Нажмите кнопку, если желаете задать еще один вопрос.',
                     reply_markup=markup_ask_again)


def bla_bla_detected(message):
    bot.send_message(message.chat.id, 'Я вас не понимаю.\n'
                                      'Нажмите /start чтобы начать жизнь с чистого листа ☘️',
                     reply_markup=markup_cleared)


def make_hw_keyboard(course):
    markup_hw = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in config.possible_to_pass[course]:
        markup_hw.row(name)
    markup_hw.row('Вернуться назад')
    return markup_hw


if __name__ == '__main__':
    bot.polling(none_stop=True)
