# -*- coding: utf-8 -*-
import time
import telebot
import os
from telebot import types
import config
import requests
from sqlighter import SQLighter

bot = telebot.TeleBot(config.token)
markup_main = types.ReplyKeyboardMarkup()
markup_main.row('🦉 Задать вопрос к семинару 🦉')
markup_main.row('🐌 Сдать домашку 🐌')
markup_main.row('🐸 Зарегаться 🐸')

markup_hw = types.ReplyKeyboardMarkup()
for name in config.possible_to_pass:
    markup_hw.row(name)
markup_hw.row('Вернуться в начало')

FLAGS = {'question': False, 'hw': None, 'register': False}

def drop_flags(current):
    for k, val in FLAGS.items():
        if (k != current):
            if val is bool:
                FLAGS[k] = False
            else:
                FLAGS[k] = None
# start
@bot.message_handler(commands=['start'])
def handle_start_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Доброе время суток! Чего изволите?", reply_markup=markup_main)
    drop_flags('all')


# Вернуться в начало'
@bot.message_handler(func=lambda msg: msg.text == 'Вернуться в начало', content_types=['text'])
def handle_start_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Чего еще изволите?", reply_markup=markup_main)
    drop_flags('all')

# Задать вопрос к семинару
@bot.message_handler(func=lambda msg: msg.text == '🦉 Задать вопрос к семинару 🦉', content_types=['text'])
def question_handler(message):
    FLAGS['question'] = True
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Спрашивайте, пожалуйста 🦊"
                                      "\nВаш вопрос будет обсужден на семинаре.\n"
                                      "Внимание: все нижесказанное cообщение (одно) будет воспринято как вопрос к семинаристу.")
    drop_flags('question')

# Сдать домашку
@bot.message_handler(func=lambda msg: msg.text == '🐌 Сдать домашку 🐌', content_types=['text'])
def hw_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    drop_flags('all')
    sqlbd = SQLighter(config.bd_name)
    if not sqlbd.is_registered(message.from_user.id):
        sqlbd.close()
        bot.send_message(message.chat.id, "Прежде чем сдавать домашку, зарегайтесь, пожалуйста.\n"
                                          "Для этого достаточно нажать на кнопочку '🐸 Зарегаться 🐸'", reply_markup=markup_main)
        return
    bot.send_message(message.chat.id, "Пожалуйста выберите из списка доступных для сдачи заданий:",
                     reply_markup=markup_hw)


# Зарегаться
@bot.message_handler(func=lambda msg: msg.text == '🐸 Зарегаться 🐸', content_types=['text'])
def register_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')

    sqlbd = SQLighter(config.bd_name)
    if sqlbd.is_registered(message.from_user.id):
        drop_flags('all')
        name = sqlbd.get_user_name(message.from_user.id)
        sqlbd.close()
        bot.send_message(message.chat.id, "Кажется вы уже зарегестрированы в системе под именем {} 🌵\n"
                                          "К сожалению ничего изменить уже нельзя. Сдавайте домашки. 🌚".format(name))
        return

    FLAGS['register'] = True
    drop_flags('register')
    bot.send_message(message.chat.id, "В следующем сообщении напишите как вас называть. 🐝\n"
                                      "Это имя будет использовано для дальнейшей идентификации вас при проверке дз.\n"
                                      "Оно также будет привязано к вашему телеграм-аккаунту 🌚\n"
                                      "Внимание! В дальнейшем изменить ваше имя будет невозможно 🐙")
# hw -- выбор домашки
@bot.message_handler(func=lambda msg: msg.text in config.possible_to_pass, content_types=['text'])
def hw_saver(message):
    sqlbd = SQLighter(config.bd_name)
    if not sqlbd.is_registered(message.from_user.id):
        sqlbd.close()
        bot.send_message(message.chat.id, "Прежде чем сдавать домашку, зарегайтесь, пожалуйста.\n"
                                          "Для этого достаточно нажать на кнопочку '🐸 Зарегаться 🐸'", reply_markup=markup_main)
        return
    FLAGS['hw'] = message.text
    drop_flags('hw')
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Пришлите файл (один архив или один Jupyter notebook) весом не более 20 Мб 🦋",
                     reply_markup=markup_hw)

# hw -- сохранение файла домашки
@bot.message_handler(func=lambda msg: FLAGS['hw'] is not None, content_types=['document'])
def handle_docs(message):
    bot.send_chat_action(message.chat.id, 'typing')

    file_id = message.document.file_id
    sqlbd = SQLighter(config.bd_name)
    sqlbd.add_homework(message.from_user.id, FLAGS['hw'], file_id=file_id)
    folder_name = os.path.join(config.SAVE_PATH, str(message.from_user.id))
    # saving to folder:
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    file_info = bot.get_file(file_id)
    print(file_info.file_path)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, file_info.file_path), stream=True)
    local_filename = os.path.join(folder_name, FLAGS['hw']+'_'+message.document.file_name)
    with open(local_filename, 'wb') as f:
        for chunk in file.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    bot.send_message(message.chat.id, "Ваш файлик был заботливо сохранен как задание {} 🐾".format(FLAGS['hw']),
                     reply_markup=markup_hw)
    drop_flags('all')

# register -- ловим имя пользователя
@bot.message_handler(func=lambda msg: FLAGS['register'], content_types=['text'])
def register_saver(message):
    bot.send_chat_action(message.chat.id, 'typing')
    drop_flags('all')
    sqlbd = SQLighter(config.bd_name)
    user_id = message.from_user.id
    sqlbd.register(user_id=user_id, user_name=message.text)
    sqlbd.close()
    bot.send_message(message.chat.id, "Спасибо! Теперь вы зарегистрированы в системе как {}".format(message.text),
                     reply_markup=markup_main)


# Сохранение вопроса к семинару
@bot.message_handler(func=lambda msg: FLAGS['question'], content_types=['text'])
def question_saver(message):
    drop_flags('all')
    bot.send_chat_action(message.chat.id, 'typing')
    sqlbd = SQLighter(config.bd_name)
    user_id = message.from_user.id
    sqlbd.write_question(user_id=user_id, question=message.text)
    sqlbd.close()
    bot.send_message(message.chat.id, "Спасибо за вопрос. Хорошего дня 🐯 :)")

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def question_saver(message):
    bot.send_message(message.chat.id, "Кажется вы мне говорите какую-то дичь :)")

if __name__ == '__main__':
    bot.polling(none_stop=True)
