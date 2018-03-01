import json
from telebot import types
from collections import defaultdict
from utilities import download_picture
import config
import os
import universal_reply as ureply
from copy import deepcopy


class QuizQuestion:
    def __init__(self, name, question_dict, last=False, first=False, parse_mode='Markdown', tick_symbol='💎️'):
        self.name = name
        self.question_text = question_dict['text']
        self.true_ans = question_dict['true_ans']

        self.grids = question_dict['grids']
        self.variants_one = question_dict['variants'] if len(question_dict['variants']) > 0 else None
        self.variants_multiple = question_dict['several_poss_vars'] if len(
            question_dict['several_poss_vars']) > 0 else None
        self.ask_written = False if (self.variants_one or self.variants_multiple or self.grids) else True

        assert self.ask_written or (self.true_ans is not None), \
            "true_ans must be specified if not ask_written!"

        self.usr_answers = dict() if self.variants_one else defaultdict(list)
        self.is_last = last
        self.is_first = first

        self.img_path = question_dict['img'] if len(question_dict['img']) > 0 else None
        if self.img_path:
            self._check_img_url()

        self.parse_mode = parse_mode
        if self.parse_mode == 'Markdown':
            self._edit_markdown_ans()
        self.tick_symbol = tick_symbol
        self.create_text_and_buttons()
        self.usr_buttons = defaultdict(lambda: deepcopy(self.default_buttons))

    def _check_img_url(self):
        if 'https' in self.img_path:
            new_path = os.path.join(config.pics_path, './img_{}'.format(self.name))
            download_picture(self.img_path, new_path)
            self.img_path = new_path
        else:
            self.img_path = os.path.join('./quizzes/', self.img_path)

    def _edit_markdown_ans(self):
        if self.variants_multiple:
            for i in range(len(self.variants_multiple)):
                self.variants_multiple[i] = self.variants_multiple[i].replace('*', '×')
        elif self.variants_one:
            for i in range(len(self.variants_one)):
                self.variants_one[i] = self.variants_one[i].replace('*', '×')

    def create_text_and_buttons(self):
        self.text = '*' + self.name + '*' + '\n' + '_' + self.question_text + '_' + '\n\n'
        if self.ask_written:
            self.text += '*Please, write an answer by yourself.*' + '\n\n'
            self.default_buttons = None

        elif self.variants_one:
            self.text += '*Please, choose only one right answer.*' + '\n\n'
            for i, v in enumerate(self.variants_one):
                self.text += str(i) + ') ' + v + '\n'
            self.default_buttons = [str(i) for i in range(0, len(self.variants_one))]

        elif self.variants_multiple:
            self.text += '*Please, mark all correct statements.*' + '\n\n'
            for i, v in enumerate(self.variants_multiple):
                self.text += str(i) + ') ' + v + '\n'
            self.default_buttons = [str(i) for i in range(0, len(self.variants_multiple))]

        elif self.grids:
            self.text += '*Please, choose only one right answer.*' + '\n\n'
            self.default_buttons = [str(i) for i in self.grids]

        if self.img_path:
            self.text += 'See the picture below.\n'

        if self.is_last:
            self.text += '*Attention! After submitting nothing can be changed.*'

    def create_inline_kb(self, arr_text=None, row_width=5):

        keyboard = types.ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=True)
        if arr_text:
            keyboard.add(
                *[types.KeyboardButton(text=n) for n in arr_text])

        next_button = types.KeyboardButton(text=ureply.quiz_next_button)
        back_button = types.KeyboardButton(text=ureply.quiz_back_button)
        main_menu = types.KeyboardButton(text=ureply.quiz_main_menu_button)

        if self.is_last:
            keyboard.add(types.KeyboardButton(text=ureply.quiz_submit_button),
                         types.KeyboardButton(text=ureply.quiz_show_ans_button))
            keyboard.add(back_button)
            keyboard.add(main_menu)
            return keyboard

        if self.is_first:
            keyboard.add(next_button)
            keyboard.add(main_menu)
            return keyboard

        keyboard.add(*[back_button, next_button])
        keyboard.add(main_menu)
        return keyboard

    def tick_ans_in_kb(self, ans, chat_id, remove=False):
        """
        Add ✔️ to ans; Just change self.buttons_text
        :param multiple:
        :param ones:
        :return:
        """
        if not remove:
            self.usr_buttons[chat_id][int(ans)] += self.tick_symbol
        else:
            self.usr_buttons[chat_id][int(ans)] = self.usr_buttons[chat_id][int(ans)].replace(self.tick_symbol, '')

    def show_asking(self, bot, chat_id):
        """
        Send self.text + ans variants to chat with id = msg.chat.id
        :param bot:
        :param msg:
        :return:
        """
        if chat_id not in self.usr_answers:
            # add new user to dict with buttons...
            _ = self.usr_buttons[chat_id]  # ...just by adding element to defaultdict
            self.usr_answers[chat_id] = None
            if self.variants_multiple:
                self.usr_answers[chat_id] = []

        if self.ask_written and self.usr_answers[chat_id]:
            bot.send_message(chat_id,
                             self.text + '\n' + '-' * 20 + '\nYOUR CURRENT ANSWER:\n' + self.usr_answers[chat_id],
                             reply_markup=self.create_inline_kb(self.usr_buttons[chat_id]),
                             parse_mode=self.parse_mode)
        else:
            bot.send_message(chat_id, self.text,
                             reply_markup=self.create_inline_kb(self.usr_buttons[chat_id]),
                             parse_mode=self.parse_mode)

        if self.img_path:
            bot.send_message(chat_id=chat_id,
                             text='Picture for the _{}_'.format(self.name),
                             parse_mode=self.parse_mode)
            with open(self.img_path, 'rb') as photo:
                # TODO: insert in DB file id to send it quicker to others
                bot.send_photo(chat_id=chat_id, photo=photo)

    def show_current(self, bot, chat_id):
        """
        Show current version of question answered by usr
        :param bot:
        :param msg:
        :return:
        """
        add = str(self.usr_answers[chat_id]) if self.usr_answers[chat_id] else 'None'
        answers = self.text + '\n' + '🍭 Your answer: ' + add
        bot.send_message(chat_id, answers, parse_mode=self.parse_mode)

    def callback_handler(self, bot, message):
        """
        Handle callbacks data from all users
        and update self.usr_dict
        :return:
        """
        ans = message.text.replace(self.tick_symbol, '')
        chat_id = message.chat.id

        if self.variants_one or self.grids:
            if self.grids:
                ans = str(self.default_buttons.index(ans))
            if self.usr_answers[chat_id] != ans:
                if self.usr_answers[chat_id] is not None:
                    self.tick_ans_in_kb(self.usr_answers[chat_id], chat_id, remove=True)

                self.tick_ans_in_kb(ans, chat_id, remove=False)
                self.usr_answers[chat_id] = ans

        elif self.variants_multiple:
            if ans in self.usr_answers[chat_id]:
                self.usr_answers[chat_id].remove(ans)
                self.tick_ans_in_kb(ans, chat_id, remove=True)
            else:
                self.usr_answers[chat_id].append(ans)
                self.tick_ans_in_kb(ans, chat_id, remove=False)

        keyboard = self.create_inline_kb(self.usr_buttons[chat_id])
        bot.send_message(chat_id=chat_id, text='Your answer has been saved', reply_markup=keyboard)

    def save_written_answer(self, text, chat_id):
        self.usr_answers[chat_id] = text

    def get_ans(self, chat_id):
        """
        Return data for chat_id
        :return: question_name, is_right, usr_ans, question_text, true_ans
        """
        if chat_id not in self.usr_answers:
            true = str(self.true_ans) if self.true_ans else None
            return self.name, None, None, self.text, true

        ans = self.usr_answers[chat_id]
        is_right = None
        if self.ask_written:
            return self.name, is_right, ans, self.text, self.true_ans

        if self.variants_multiple:
            is_right = frozenset([int(a) for a in self.true_ans]) == frozenset([int(a) for a in ans]) if ans else False
        else:
            is_right = int(self.true_ans) == int(ans) if ans else False
        ans = str(ans) if ans else None
        return self.name, int(is_right), ans, self.text, str(self.true_ans)


class Quiz:
    def __init__(self, name, quiz_json_path, next_global_state_name, self_state_name=None):
        self.reinitialize(quiz_json_path)
        self.name = name
        self.next_global_state_name = next_global_state_name
        self.self_state_name = self_state_name

    def reinitialize(self, new_quiz_json_path):
        with open(new_quiz_json_path) as q:
            self.json_array = json.load(q)[1:]
        self.q_num = len(self.json_array)
        self.questions = [
            QuizQuestion(name="Question {}".format(i),
                         question_dict=d, first=(i == 0),
                         last=(i == self.q_num - 1))
            for i, d in enumerate(self.json_array)]
        self.usersteps = dict()
        self.usr_submitted = defaultdict(bool)
        self.paused = defaultdict(bool)

    def get_usr_step(self, chat_id):
        if chat_id not in self.usersteps:
            # set usr to the first step
            self.usersteps[chat_id] = 0
        return self.usersteps[chat_id]

    def set_usr_step(self, chat_id, num: int):
        self.usersteps[chat_id] = num

    def collect_to_db(self, user_id, chat_id, sqlighter):
        """
        collect all question answers for chat_id and write them to db
        :return: None
        """
        for q in self.questions:
            question_name, is_right, usr_ans, question_text, true_ans = q.get_ans(chat_id)
            if q.ask_written and ((usr_ans is None) or (usr_ans == '')):
                is_right = 0
                usr_ans = None
            sqlighter.write_quiz_ans(user_id=user_id,
                                     quiz_name=self.name,
                                     question_name=question_name,
                                     is_right=is_right,
                                     usr_ans=usr_ans,
                                     question_text=question_text,
                                     true_ans=true_ans)

    def run(self, bot, message, sqlighter):
        """
        Handle all messages including callbacks
        :param message: 
        :return: 'end' or 'continue'
        """

        if config.quiz_closed:
            return self.next_global_state_name

        chat_id = message.chat.id

        if self.usr_submitted[chat_id]:
            return self.next_global_state_name

        if (message.text == ureply.quiz_enter) and self.paused[chat_id]:
            self.questions[self.usersteps[chat_id]].show_asking(bot, chat_id)
            return self.self_state_name

        if chat_id not in self.usersteps:
            usr_step = self.get_usr_step(chat_id)
            bot.send_message(text='🌜 Welcome to *' + self.name + '* 🌛',
                             chat_id=message.chat.id,
                             parse_mode='Markdown')
            self.questions[usr_step].show_asking(bot, chat_id)
            return self.self_state_name
        else:
            usr_step = self.get_usr_step(chat_id)
            if message.text == ureply.quiz_main_menu_button:
                self.paused[chat_id] = True
                self.collect_to_db(user_id=message.chat.username,
                                   chat_id=message.chat.id,
                                   sqlighter=sqlighter)
                bot.send_message(text="You current state has been saved.",
                                 chat_id=chat_id)
                return self.next_global_state_name

            elif message.text == ureply.quiz_next_button:
                self.set_usr_step(chat_id, usr_step + 1)
                self.questions[usr_step + 1].show_asking(bot, chat_id)

            elif message.text == ureply.quiz_back_button:
                self.set_usr_step(chat_id, usr_step - 1)
                self.questions[usr_step - 1].show_asking(bot, chat_id)

            elif message.text == ureply.quiz_submit_button:
                self.collect_to_db(user_id=message.chat.username,
                                   chat_id=message.chat.id,
                                   sqlighter=sqlighter)
                self.usr_submitted[message.from_user.id] = True
                bot.send_message(chat_id=message.from_user.id,
                                 text='💫 Thank you! The quiz was successfully submitted! 🌝')
                return self.next_global_state_name

            elif message.text == ureply.quiz_show_ans_button:
                for q in self.questions:
                    q.show_current(bot, chat_id)

            elif self.questions[usr_step].ask_written:
                self.questions[usr_step].save_written_answer(message.text, chat_id)
                bot.send_message(chat_id=chat_id, text='Your answer has been saved! ✨')
            elif message.text.replace(self.questions[0].tick_symbol, '') in self.questions[usr_step].default_buttons:
                self.questions[usr_step].callback_handler(bot, message)
            return self.self_state_name
