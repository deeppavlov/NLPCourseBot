# -*- coding: utf-8 -*-
import time
import telebot
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

# start
@bot.message_handler(commands=['start'])
def handle_start_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Доброе время суток! Чего изволите?", reply_markup=markup_main)


# Вернуться в начало'
@bot.message_handler(func=lambda msg: msg.text == 'Вернуться в начало', content_types=['text'])
def handle_start_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Чего еще изволите?", reply_markup=markup_main)

# Задать вопрос к семинару
@bot.message_handler(func=lambda msg: msg.text == '🦉 Задать вопрос к семинару 🦉', content_types=['text'])
def question_handler(message):
    FLAGS['question'] = True
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Спрашивайте, пожалуйста 🦊"
                                      "\nВаш вопрос будет обсужден на семинаре.\n"
                                      "Внимание: все нижесказанное cообщение будет воспринято как вопрос к семинаристу.")
# Сдать домашку
@bot.message_handler(func=lambda msg: msg.text == '🐌 Сдать домашку 🐌', content_types=['text'])
def hw_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Пожалуйста выберите из списка доступных для сдачи заданий:",
                     reply_markup=markup_hw)

# Зарегаться
@bot.message_handler(func=lambda msg: msg.text == '🐸 Зарегаться 🐸', content_types=['text'])
def register_handler(message):
    bot.send_chat_action(message.chat.id, 'typing')

    sqlbd = SQLighter(config.bd_name)
    if sqlbd.is_registered(message.from_user.id):
        name = sqlbd.get_user_name(message.from_user.id)
        sqlbd.close()
        bot.send_message(message.chat.id, "Кажется вы уже зарегестрированы в системе под именем {} 🌵\n"
                                          "К сожалению ничего изменить уже нельзя. Сдавайте домашки. 🌚".format(name))
        return

    FLAGS['register'] = True
    bot.send_message(message.chat.id, "В следующем сообщении напишите как вас называть. 🐝\n"
                                      "Это имя будет использовано для дальнейшей идентификации вас при проверке дз.\n"
                                      "Оно также будет привязано к вашему телеграм-аккаунту 🌚\n"
                                      "__Внимание!__ В дальнейшем изменить ваше имя будет невозможно 🐙")
# hw -- выбор домашки
@bot.message_handler(func=lambda msg: msg.text in config.possible_to_pass, content_types=['text'])
def hw_saver(message):
    FLAGS['hw'] = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Пришлите файл (один архив или один Jupyter notebook) весом не более 20 Мб 🦋",
                     reply_markup=markup_hw)

# hw -- сохранение файла домашки
@bot.message_handler(func=lambda msg: FLAGS['hw'] is not None, content_types=['document'])
def handle_docs(message):
    bot.send_chat_action(message.chat.id, 'typing')
    sqlbd = SQLighter(config.bd_name)
    
    bot.send_message(message.chat.id, "Ваш файлик был заботливо сохранен как задание {} 🐾".format(FLAGS['hw']),
                     reply_markup=markup_hw)
    FLAGS['hw'] = None

# register -- ловим имя пользователя
@bot.message_handler(func=lambda msg: FLAGS['register'], content_types=['text'])
def register_saver(message):
    FLAGS['register'] = False
    bot.send_chat_action(message.chat.id, 'typing')

    sqlbd = SQLighter(config.bd_name)
    user_id = message.from_user.id
    sqlbd.register(user_id=user_id, user_name=message.text)
    sqlbd.close()
    bot.send_message(message.chat.id, "Спасибо! Теперь вы зарегистрированы в системе как {}".format(message.text),
                     reply_markup=markup_main)

# Сохранение вопроса к семинару
@bot.message_handler(func=lambda msg: FLAGS['question'], content_types=['text'])
def question_saver(message):
    FLAGS['question'] = False
    bot.send_chat_action(message.chat.id, 'typing')
    sqlbd = SQLighter(config.bd_name)
    user_id = message.from_user.id
    sqlbd.write_question(user_id=user_id, question=message.text)
    sqlbd.close()
    bot.send_message(message.chat.id, "Спасибо за вопрос. Хорошего дня 🐯 :)")

if __name__ == '__main__':
    bot.polling(none_stop=True)
