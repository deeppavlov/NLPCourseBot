import json
from telebot import types
import telebot
from collections import defaultdict


class QuizQuestion:
    def __init__(self, name, question_dict, last=False, first=False):
        self.name = name
        self.question_text = question_dict['text']
        self.img_path = question_dict['img'] if len(question_dict['img']) > 0 else None
        self.img_sent_dict = defaultdict(bool)

        self.grids = question_dict['grids']
        self.variants_one = question_dict['variants'] if len(question_dict['variants']) > 0 else None
        self.variants_multiple = question_dict['several_poss_vars'] if len(
            question_dict['several_poss_vars']) > 0 else None
        self.ask_written = False if (self.variants_one or self.variants_multiple or self.grids) else True
        self.usr_dict = dict() if self.variants_one else defaultdict(list)
        self.is_last = last
        self.is_first = first
        self.create_text_and_buttons()

    def create_text_and_buttons(self):
        self.text = self.name + '\n' + self.question_text + '\n\n'
        if self.ask_written:
            self.text += 'Please, write an answer by yourself.' + '\n\n'
            self.buttons_text = None

        elif self.variants_one:
            self.text += 'Please, choose only one right answer.' + '\n\n'
            for i, v in enumerate(self.variants_one):
                self.text += str(i + 1) + ') ' + v + '\n'
            self.buttons_text = [str(i) for i in range(1, len(self.variants_one) + 1)]

        elif self.variants_multiple:
            self.text += 'Please, mark all correct statements.' + '\n\n'
            for i, v in enumerate(self.variants_multiple):
                self.text += str(i + 1) + ') ' + v + '\n'
            self.buttons_text = [str(i) for i in range(1, len(self.variants_multiple) + 1)]

        elif self.grids:
            self.text += 'Please, choose only one right answer.' + '\n\n'
            self.buttons_text = [str(i) for i in self.grids]

        if self.buttons_text:
            self.keyboard = self.create_inline_kb(self.buttons_text)
        else:
            self.keyboard = self.create_inline_kb()

    def create_inline_kb(self, arr_text=None):
        if arr_text:
            kb = self._create_inline_kb(arr_text, [str(j) for j in range(len(arr_text))])
        else:
            kb = self._create_inline_kb()
        return kb

    def _create_inline_kb(self, arr_text=None, arr_callback_data=None, row_width=4):
        keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        if arr_text and arr_callback_data:
            keyboard.add(
                *[types.InlineKeyboardButton(text=n, callback_data=c) for n, c in zip(arr_text, arr_callback_data)])

        next_button = types.InlineKeyboardButton(text='➡️', callback_data='next')
        back_button = types.InlineKeyboardButton(text='⬅️', callback_data='back')

        if self.is_last:
            keyboard.add(types.InlineKeyboardButton(text='Submit quiz', callback_data='submit'))
            keyboard.add(types.InlineKeyboardButton(text='Show current answers', callback_data='show'))
            keyboard.add(back_button)
            return keyboard

        if self.is_first:
            keyboard.add(next_button)
            return keyboard

        keyboard.add(*[back_button, next_button])

        return keyboard

    def tick_ans_in_kb(self, ans, remove=False):
        """
        Add ✔️ to ans; Just change self.buttons_text
        :param multiple:
        :param ones:
        :return:
        """
        if not remove:
            self.buttons_text[int(ans)] += '✔️'
        else:
            self.buttons_text[int(ans)] = self.buttons_text[int(ans)].replace('✔️', '')

    def show_asking(self, bot, chat_id, message_id=None, edit=False):
        """
        Send self.text + ans variants to chat with id = msg.chat.id
        :param bot:
        :param msg:
        :return:
        """
        if not edit:
            bot.send_message(chat_id, self.text, reply_markup=self.keyboard)
            if (self.img_path) and (not self.img_sent_dict[chat_id]):
                with open(self.img_path, 'rb') as photo:
                    # TODO: insert in DB file id to send it quicker to others
                    self.img_sent_dict[chat_id] = True
                    bot.send_photo(chat_id, photo)
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=self.text,
                reply_markup=self.keyboard)

    def show_current(self, bot, chat_id):
        """
        Show current version of question answered by usr
        :param bot:
        :param msg:
        :return:
        """
        # TODO: KeyError !
        answers = self.text + '\n\n' + '🍭 Your ans:' + str(self.usr_dict[chat_id])
        bot.send_message(chat_id, answers)

    def callback_handler(self, bot, c):
        """
        Handle callbacks data from all users
        and update self.usr_dict
        :return:
        """
        # TODO: KeyError !
        ans = c.data
        chat_id = c.from_user.id
        if self.variants_one:
            if self.usr_dict.get(chat_id, ) != ans:
                self.tick_ans_in_kb(ans, remove=False)
                if self.usr_dict[chat_id] is not None:
                    self.tick_ans_in_kb(self.usr_dict[chat_id], remove=True)
                self.usr_dict[chat_id] = ans

        elif self.variants_multiple:
            if ans in self.usr_dict[chat_id]:
                self.usr_dict[chat_id].remove(ans)
                self.tick_ans_in_kb(ans, remove=True)
            else:
                self.usr_dict[chat_id].append(ans)
                self.tick_ans_in_kb(ans, remove=False)

        self.keyboard = self.create_inline_kb(self.buttons_text)
        bot.edit_message_reply_markup(chat_id=chat_id,
                                      message_id=c.message.message_id,
                                      reply_markup=self.keyboard)

    def get_ans(self, username):
        """
        Return ans of username
        :return:
        """
        pass


class Quiz:
    def __init__(self, name, bot, quiz_json_path, sqlighter):
        with open(quiz_json_path) as q:
            self.json_array = json.load(q)[1:]
        self.name = name
        self.bot = bot
        self.sqlighter = sqlighter
        self.q_num = len(self.json_array)
        self.questions = [
            QuizQuestion(name="Question {}".format(i), question_dict=d, first=(i == 0), last=(i == self.q_num - 1))
            for i, d in enumerate(self.json_array)]

        self.start = self.bot.callback_query_handler(func=lambda x: True)(self.start)
        self.usersteps = dict()

    def get_usr_step(self, chat_id):
        if chat_id not in self.usersteps:
            # set usr to the first step
            self.usersteps[chat_id] = 0
        return self.usersteps[chat_id]

    def set_usr_step(self, chat_id, num: int):
        self.usersteps[chat_id] = num

    def callback_query_handler(self, c):
        chat_id = c.from_user.id
        usr_step = self.get_usr_step(chat_id)
        message_id = c.message.message_id

        if c.data == 'next':
            self.set_usr_step(chat_id, usr_step + 1)
            self.questions[usr_step + 1].show_asking(self.bot, chat_id, message_id=message_id, edit=True)

        elif c.data == 'back':
            self.set_usr_step(chat_id, usr_step - 1)
            self.questions[usr_step - 1].show_asking(self.bot, chat_id, message_id=message_id, edit=True)

        elif c.data == 'submit':
            pass
        elif c.data == 'show':
            for q in self.questions:
                q.show_current(self.bot, chat_id)
        else:
            self.questions[usr_step].callback_handler(bot, c)

    def start(self, msg):
        if isinstance(msg, types.CallbackQuery):
            self.callback_query_handler(msg)
            return
        else:
            chat_id = msg.chat.id
            usr_step = self.get_usr_step(chat_id)
            if usr_step == 0:
                self.questions[usr_step].show_asking(self.bot, chat_id, edit=False)
                return

    def write_to_db(self):
        pass


if __name__ == '__main__':
    bot = telebot.TeleBot('', threaded=False)

    quiz = Quiz('kek', bot, "quiz6.json", "lpl")


    @bot.message_handler(content_types=['text'])
    def handler(message):
        quiz.start(message)


    bot.polling(none_stop=True)
