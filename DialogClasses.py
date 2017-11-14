from typing import List, Dict, Callable
import universal_reply
from telebot import types
from collections import defaultdict


class State:
    def __init__(self, name: str,
                 triggers_out: Dict,
                 hidden_states: List = None,
                 welcome_msg: str = None,
                 handler_welcome: Callable = None):
        """
        :param name: name of state object;
        :param triggers_out: dict like {state_out1_name:{'phrases':['some_string1', 'str2', etc],
                                                         'content_type':'text'}};
        :param handler_out: None or func(message, usr_states) which update usr_state and return next dialog state name;

        """
        self.name = name
        self.hidden_states = hidden_states
        self.welcome_msg = welcome_msg
        self.triggers_out = triggers_out
        self.handler_welcome = handler_welcome
        self.reply_markup = self.make_reply_markup()

    def make_reply_markup(self):

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        is_markup_filled = False
        for state_name, attrib in self.triggers_out.items():
            hidden_flag = ((self.hidden_states is not None) and (state_name not in self.hidden_states)) \
                          or (self.hidden_states is None)
            if len(attrib['phrases']) > 0 and hidden_flag:
                for txt in attrib['phrases']:
                    markup.add(txt)
                is_markup_filled = True

        if not is_markup_filled:
            markup = types.ReplyKeyboardRemove()
        return markup

    def welcome_handler(self, bot, message):
        if self.handler_welcome is not None:
            self.handler_welcome(bot, message)
        bot.send_message(message.chat.id, self.welcome_msg, reply_markup=self.reply_markup, parse_mode='Markdown')

    def default_out_handler(self, bot, message):

        # TODO: implement handler for bla-bla detection
        if message.text == '/start':
            return 'MAIN_MENU'

        bot.send_message(message.chat.id, 'Я вас не понимаю.\n'
                                          'Нажмите /start чтобы начать жизнь с чистого листа ☘️', )
        return None

    def out_handler(self, bot, message):
        """
        Default handler manage text messages and couldn't handle any photo/documents;
        It just apply special handler if it is not None;
        If message couldn't be handled None is returned;
        :param message:
        :param bot:
        :return: name of the new state;

        """
        # TODO: do smth to react on [] triggers after all the others;
        for state_name, attribs in self.triggers_out.items():
            if message.content_type != 'text':
                if message.content_type == attribs['content_type']:
                    return state_name

            elif message.text in attribs['phrases']:
                return state_name

            # the case when any text message should route to state_name
            elif len(attribs['phrases']) == 0:
                return state_name

        return self.default_out_handler(bot, message)


class DialogGraph:
    def __init__(self, bot, root_state: str, nodes: List[State]):
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

    def make_nodes_dict(self, nodes):
        return {state.name: state for state in nodes}

    def run(self, message):
        if message.chat.username is None:
            self.bot.send_message(message.chat.id, universal_reply.NO_USERNAME_WARNING)
            return

        if message.chat.id not in self.usr_states:
            self.usr_states[message.chat.id]['current_state'] = self.root_state

        print("msg: ", message.text)
        curr_state_name = self.usr_states[message.chat.id]['current_state']
        print('curr_state_name: ', curr_state_name)
        new_state_name = self.nodes[curr_state_name].out_handler(self.bot, message)
        print('new_state_name: ', new_state_name)

        if new_state_name is not None:
            self.usr_states[message.chat.id]['current_state'] = new_state_name
            self.nodes[new_state_name].welcome_handler(self.bot, message)
