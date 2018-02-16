from typing import List, Dict, Callable
import universal_reply
from telebot import types
from collections import defaultdict
from Sqlighter import SQLighter
import logging


class State:
    def __init__(self, name: str,
                 triggers_out: Dict,
                 hidden_states: Dict = None,
                 welcome_msg: str = None,
                 row_width=1,
                 handler_welcome: Callable = None):
        """
        :param name: name of state object;
        :param triggers_out: dict like {state_out1_name:{'phrases':['some_string1', 'str2', etc],
                                                         'content_type':'text'}};
        :param hidden_states: list of state names that have to be reachable from this state
                              but they don't have to be shown on the keyboard;
        :param welcome_msg: what does the State have to say to usr after welcome_handler()
        :param handler_welcome: function that handle income message

        """
        self.name = name
        self.hidden_states = hidden_states
        self.welcome_msg = welcome_msg
        self.triggers_out = triggers_out
        self.handler_welcome = handler_welcome
        self.row_width = row_width
        self.reply_markup = self.make_reply_markup()
        print('STATE {} obj has been initialized\n'.format(self.name))

    def make_reply_markup(self):

        markup = types.ReplyKeyboardMarkup(row_width=self.row_width, resize_keyboard=True)
        is_markup_filled = False
        tmp_buttons = []
        for state_name, attrib in self.triggers_out.items():
            hidden_flag = ((self.hidden_states is not None) and (state_name != self.hidden_states['state_name'])) \
                          or (self.hidden_states is None)
            if len(attrib['phrases']) > 0 and hidden_flag:
                for txt in attrib['phrases']:
                    tmp_buttons.append(txt)
                is_markup_filled = True
        tmp_buttons = sorted(tmp_buttons)
        markup.add(*(types.KeyboardButton(button) for button in tmp_buttons))
        if not is_markup_filled:
            markup = types.ReplyKeyboardRemove()
        return markup

    def welcome_handler(self, bot, message, sqldb: SQLighter):
        if self.handler_welcome is not None:
            res = self.handler_welcome(bot, message, sqldb)
        else:
            res = None
        if self.welcome_msg:
            bot.send_message(message.chat.id, self.welcome_msg, reply_markup=self.reply_markup, parse_mode='Markdown')
        return res

    def default_out_handler(self, bot, message):
        if message.text == '/start':
            return 'MAIN_MENU'

        bot.send_message(message.chat.id, universal_reply.DEFAULT_ANS)
        return None

    def out_handler(self, bot, message, sqldb: SQLighter):
        """
        Default handler manage text messages and couldn't handle any photo/documents;
        It just apply special handler if it is not None;
        If message couldn't be handled None is returned;
        :param message:
        :param bot:
        :param sqldb:
        :return: name of the new state;

        """
        any_text_state = None
        for state_name, attribs in self.triggers_out.items():
            if message.content_type != 'text':
                if message.content_type == attribs['content_type']:
                    return state_name

            elif message.text in attribs['phrases']:
                if self.hidden_states is None:
                    return state_name
                elif state_name == self.hidden_states['state_name']:
                    if message.chat.username in self.hidden_states['users_file']:
                        return state_name
                else:
                    return state_name

            # the case when any text message should route to state_name
            elif (len(attribs['phrases']) == 0) and (attribs['content_type'] == 'text'):
                any_text_state = state_name

        if any_text_state is not None:
            return any_text_state

        return self.default_out_handler(bot, message)


class DialogGraph:
    def __init__(self, bot, root_state: str, nodes: List[State], sqldb: SQLighter, logger: logging):
        """
        Instance of this class manages all the dialog flow;
        :param bot: telebot.TeleBot(token);
        :param nodes: list of instances of State class;
        :param root_state: name of the root of dialog states.
                            when new user appeared he/she has this state;
                            root state doesn't have "welcome" method;
        """
        self.bot = bot
        self.root_state = root_state
        self.nodes = self.make_nodes_dict(nodes)
        self.usr_states = defaultdict(dict)
        self.sqldb = sqldb
        self.logger = logger

    def make_nodes_dict(self, nodes):
        return {state.name: state for state in nodes}

    def run(self, message):
        if isinstance(message, types.CallbackQuery):
            chat_id = message.from_user.id
            state_name = self.usr_states[chat_id]['current_state']
            res = self.nodes[state_name].welcome_handler(self.bot, message, self.sqldb)
            if res == 'end':
                print('It seems, the quiz submitted!')
                self.usr_states[chat_id]['current_state'] = self.root_state
                self.nodes[self.root_state].welcome_handler(self.bot, message, self.sqldb)
                return
            else:
                return

        if message.chat.username is None:
            self.bot.send_message(message.chat.id, universal_reply.NO_USERNAME_WARNING)
            self.logger.debug("NONAME USR JOINED TELEBOT!!!")
            return

        if message.text is not None:
            self.logger.debug("USR: " + message.chat.username + " SAID: " + message.text)
        else:
            self.logger.debug("USR: " + message.chat.username + " SEND: " + message.content_type)
        if message.chat.id not in self.usr_states:
            self.logger.debug("NEW USR: " + message.chat.username)
            self.usr_states[message.chat.id]['current_state'] = self.root_state

        curr_state_name = self.usr_states[message.chat.id]['current_state']
        new_state_name = self.nodes[curr_state_name].out_handler(self.bot, message, self.sqldb)

        if new_state_name is not None:
            self.logger.debug("USR: " + message.chat.username + " NEW STATE: " + new_state_name)
            self.usr_states[message.chat.id]['current_state'] = new_state_name
            self.nodes[new_state_name].welcome_handler(self.bot, message, self.sqldb)
