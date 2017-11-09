from typing import List, Dict, Callable
import universal_reply
from telebot import types
from collections import defaultdict


class State:
    def __init__(self, name: str, triggers_out: Dict,
                 welcome_msg: str = None,
                 parent_state: str = None,
                 handler_out: Callable = None,
                 handler_welcome: Callable = None,
                 return_back_button=False):
        """
        :param name: name of state object;
        :param triggers_out: dict like {state_out1_name:{'phrase':'some_string',
                    'content_type':'text', 'update_usr_state': ** one of ['hw_num', 'course'] or None **}};
        :param handler_out: None or func(message, usr_states) which update usr_state and return next dialog state name;

        """
        self.name = name
        self.welcome_msg = welcome_msg
        self.triggers_out = triggers_out
        self.parent_state = parent_state
        self.handler_out = handler_out
        self.handler_welcome = handler_welcome
        self.return_back_button = return_back_button
        self.reply_markup = self.make_reply_markup()

    def make_reply_markup(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        is_markup_filled = False

        for state_name, attribs in self.triggers_out.items():
            if attribs['phrase'] is not None:
                markup.add(attribs['phrase'])
                is_markup_filled = True

        if (not self.return_back_button) and (not is_markup_filled):
            markup = types.ReplyKeyboardRemove()
        return markup

    def welcome(self, bot, message, usr_states: Dict[Dict]):
        if self.handler_welcome is not None:
            self.handler_welcome(bot, message, usr_states)
        else:
            bot.send_message(message.chat.id, self.welcome_msg, reply_markup=self.reply_markup)

    def default_handler(self, bot, message, usr_states: Dict[Dict]):
        """
        Default handler manage text messages and couldn't handle any photo/documents;
        It just apply special handler if it is not None;
        If message couldn't be handled None is returned;
        :param message:
        :param usr_states:
        :return: name of the new state;

        """
        if self.handler_out is not None:
            return self.handler_out(bot, message, usr_states)
        elif message.content_type == 'text':
            chat_id = message.chat.id
            for state_name, attribs in self.triggers_out.items():
                if message.text == attribs['phrase']:
                    update_usr_state = attribs.get('update_usr_state', None)
                    if update_usr_state is not None:
                        usr_states[chat_id][update_usr_state] = message.text
                    usr_states[chat_id]['current_state'] = state_name
                    return state_name
        else:
            return None


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
            self.bot.send_message(message.chat.id,
                                  'Для продолжения работы с ботом, пожалуйста, запилите себе username в настройках телеграм!')
            return

        if message.chat.id not in self.usr_states:
            self.usr_states[message.chat.id]['currState'] = self.root_state

        curr_state_name = self.usr_states[message.chat.id]
        new_state_name = self.nodes[curr_state_name].default_handler(message, self.usr_states)
        self.nodes[new_state_name].welcome(self.bot, message, self.usr_states)
