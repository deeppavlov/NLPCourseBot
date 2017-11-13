# -*- coding: utf-8 -*-
import telebot
from telebot import types
import config
from Sqlighter import SQLighter
from collections import defaultdict
import os
from flask import Flask, request


token = os.environ['TOKEN']
bot = telebot.TeleBot(token)

markup_cleared = types.ReplyKeyboardRemove()

markup_ask_again = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_ask_again.row('Задать еще один вопрос')
markup_ask_again.row('Вернуться назад')

markup_back = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_back.row('Вернуться назад')

markup_course = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_course.row('🐟 RL 🐟')
markup_course.row('🐸 NLP 🐸')

markup_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
for button in config.STATES_DICT['MAIN_MENU']:
    markup_menu.row(button)

markup_hw_pass = types.ReplyKeyboardMarkup(resize_keyboard=True)
for name in config.available_to_pass:
    markup_hw_pass.row(name)
markup_hw_pass.row('Вернуться назад')

markup_hw_check = types.ReplyKeyboardMarkup(resize_keyboard=True)
for name in config.available_to_check:
    markup_hw_check.row(name)
markup_hw_check.row('Вернуться назад')

states = defaultdict(dict)


@bot.message_handler(content_types=['text', 'document', 'photo'])
def handler(message):
    global states
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if message.chat.username is None:
        username_error(message)
        return
# ---------------------------------------------------------------------------

    elif message.chat.id not in states:
        clear_state(message, states)
        default_callback(message, states)

# ---------------------------------------------------------------------------

    elif states[chat_id]['currentState'] == 'WAIT_USER_INTERACTION':
        default_callback(message, states)

#---------------------------------------------------------------------------

    elif (states[chat_id]['currentState'] == 'MAIN_MENU') and \
            (message.text in config.STATES_DICT['MAIN_MENU']):
        if message.text == '🦉 Задать вопрос к семинару 🦉':
            question_handler(message)
            states[chat_id]['currentState'] = 'IN_QUESTION'

        elif message.text == '🐌 Сдать домашку 🐌':
            hw_handler(message)
            states[chat_id]['currentState'] = 'PASS_HW_NUM_SELECTION'

        elif message.text == 'Проверить домашку':
            hw_check_num_selection_handler(message)
            states[chat_id]['currentState'] = 'CHECK_HW_NUM_SELECTION'

        elif message.text == 'Узнать свою оценку':
            know_mark_handler(message)
            states[chat_id]['currentState'] = 'KNOW_MARK'
#----------------------------------------------------------------------------

    elif (states[chat_id]['currentState'] == 'IN_QUESTION') and \
            (message.text != 'Вернуться в начало') and (message.content_type == 'text'):
        if message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'MAIN_MENU'
            choose_menu_item(message)
        elif message.text == 'Задать еще один вопрос':
            question_handler(message)
        else:
            question_saver(message, course=states[chat_id]['course'])
# ----------------------------------------------------------------------------

    elif (states[chat_id]['currentState'] == 'PASS_HW_NUM_SELECTION') and \
            ((message.text in config.available_to_pass) or (message.text == 'Вернуться назад')):
        if message.text in config.available_to_pass:
            states[chat_id]['currentState'] = 'IN_HW_UPLOAD'
            states[chat_id]['check_hw_num_selection'] = message.text
            hw_waiter(message)
        elif message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'MAIN_MENU'
            choose_menu_item(message)
# ----------------------------------------------------------------------------

    elif (states[chat_id]['currentState'] == 'IN_HW_UPLOAD') and \
            ((message.content_type in ['document', 'photo']) or message.text == 'Вернуться назад'):
        if message.text == 'Вернуться назад':
            states[chat_id]['currentState'] = 'PASS_HW_NUM_SELECTION'
            hw_handler(message)
        else:
            hw_saver(message, states)
# ----------------------------------------------------------------------------
    else:
        print('DEFAULT')
        default_callback(message, states)

    print(states)


# use this function as default handler
def default_callback(message, states):
    if (message.text == '/start') or (message.text == 'Вернуться в начало'):
        choose_menu_item(message)
        clear_state(message, states, set_state='MAIN_MENU')

    elif message.text == '/help':
        clear_state(message, states, set_state='MAIN_MENU')
        bot.send_message(message.chat.id,
                         'Привет, {}!\nЯ умею принимать вопросы к семинарам и файлы с дз по курсу NLP.\n'
                         'Также я устраиваю кросс-проверку домашних работ между участниками курса.\n'
                         'С моей помощью вы можете узнать свою оценку за дз.\n'
                         'Другие мои возможности находятся в разработке.\n'
                         'Чтобы приступить к работе выберите интересующую опцию.'
                         .format(message.chat.username.title()),
                         reply_markup=markup_menu)

    else:
        bla_bla_detected(message)
        clear_state(message, states)

def know_mark_handler(message):
    sqldb = SQLighter(config.bd_name)



def hw_check_num_selection_handler(message):
    bot.send_message(message.chat.id, 'Выберите заданьице', reply_markup=markup_hw_check)

def clear_state(message, states, set_state='WAIT_USER_INTERACTION'):
    states[message.chat.id]['currentState'] = set_state
    states[message.chat.id]['course'] = 'NLP'
    states[message.chat.id]['check_hw_num_selection'] = None


def username_error(message):
    bot.send_message(message.chat.id,
                     'Для продолжения работы с ботом, пожалуйста, запилите себе username в настройках телеграм!',
                     reply_markup=markup_cleared)


def choose_menu_item(message):
    bot.send_message(message.chat.id, 'Выберите доступное действие, пожалуйста 🦊', reply_markup=markup_menu)


# Задать вопрос к семинару
def question_handler(message):
    bot.send_message(message.chat.id, 'Сформулируйте вопрос к семинаристу и отправьте его одним сообщением 🦊.',
                     reply_markup=markup_back)


# Сдать домашку
def hw_handler(message):
    bot.send_message(message.chat.id, 'Пожалуйста, выберите из списка доступных для сдачи заданий.',
                     reply_markup=markup_hw_pass)


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

    hw_num = states[message.chat.id]['check_hw_num_selection']
    course = 'NLP'
    sqldb = SQLighter(config.bd_name)
    if sqldb.is_exists_hw(user_id=username, hw_num=hw_num, course=course):
        sqldb.upd_homework(user_id=username, hw_num=hw_num, course=course, file_id=message.document.file_id)
        bot.send_message(message.chat.id, 'Уважаемый *{}*, ваше задание {} было обновлено. Хорошего дня:) 🐾\n'
                         .format(username.title(), hw_num),
                         reply_markup=markup_hw_pass, parse_mode='Markdown')
    else:
        sqldb.add_homework(user_id=username, hw_num=hw_num, course=course, file_id=message.document.file_id)
        bot.send_message(message.chat.id, 'Уважаемый *{}*, ваш файлик был заботливо сохранен как задание {} 🐾\n'
                         .format(username.title(), hw_num),
                         reply_markup=markup_hw_pass, parse_mode='Markdown')
    states[message.chat.id]['currentState'] = 'PASS_HW_NUM_SELECTION'
    states[message.chat.id]['check_hw_num_selection'] = None

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


if __name__ == '__main__':
    if config.WEBHOOKS_AVAIL:

        WEBHOOK_HOST = config.WEBHOOK_HOST
        PORT = config.PORT
        WEBHOOK_LISTEN = config.WEBHOOK_LISTEN

        server = Flask(__name__)


        @server.route("/webhook", methods=['POST'])
        def getMessage():
            bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
            return "!", 200

        server.run(host=WEBHOOK_LISTEN, port=PORT)

        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_HOST)
    else:
        bot.delete_webhook()
        bot.polling(none_stop=True)
