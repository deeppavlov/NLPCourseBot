import telebot
from telebot import types

TOKEN = ''

bot = telebot.TeleBot(TOKEN)
c1 = 0
c2 = 0

def make_kb(lst1, lst2):
	keyboard = types.InlineKeyboardMarkup(row_width=1)
	keyboard.add(*[types.InlineKeyboardButton(text=n, callback_data=c) for n,c in zip(lst1, lst2)])
	return keyboard

@bot.message_handler(commands=['start'])
def start(m):
	# keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	kb = make_kb(['Шерлок Холмс', 'Доктор Ватсон'], ['Шерлок Холмс', 'Доктор Ватсон'])
	keyboard = types.InlineKeyboardMarkup()
	url_button = types.InlineKeyboardButton(text="Перейти не на яндекс", url="https://t.me/fogside")
	keyboard.add(url_button)
	bot.send_message(m.chat.id, 'Lol', reply_markup=keyboard)
	bot.send_message(m.chat.id, 'Кого выбираешь?', reply_markup=kb)

@bot.callback_query_handler(func=lambda x:True)
def inline(c):
	global c1
	global c2
	if c.data == 'Шерлок Холмс':
		c1+=1
		bot.edit_message_reply_markup(
			chat_id=c.message.chat.id,
			message_id=c.message.message_id,
			# text='Kkek Sherlock!',
			reply_markup=make_kb(['Шерлок Холмс {}'.format(c1), 'Доктор Ватсон {}'.format(c2)],
			 ['Шерлок Холмс', 'Доктор Ватсон']))

	elif c.data == 'Доктор Ватсон':
		c2+=1
		bot.edit_message_reply_markup(
			chat_id=c.message.chat.id,
			message_id=c.message.message_id,
			# text='John Watson!',
			reply_markup=make_kb(['Шерлок Холмс любит есть\
			 орешки, Холмс любит есть орешки, Холмс любит есть орешки, Холмс любит есть орешки,{}'.format(c1), 'Доктор Ватсон {}'.format(c2)],
			 ['Шерлок Холмс', 'Доктор Ватсон']))

bot.polling()