from typing import List, Dict, Callable
import universal_reply
from telebot import types
from collections import defaultdict
from Sqlighter import SQLighter
import logging
from collections import OrderedDict
import dill
import config


class State:
    def __init__(self, name: str,
                 triggers_out: OrderedDict = None,
                 hidden_states: Dict = None,
                 welcome_msg: str = None,
                 row_width=1,
                 load=config.load_states,
                 handler_welcome: Callable = None,
                 *args):
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
        self.load = load
        self.reply_markup = self.make_reply_markup()
        self.additional_init(*args)
        if load:
            self.load_current_states()
        print('STATE {} obj has been initialized\n'.format(self.name))

    def dump_current_states(self):
        pass

    def load_current_states(self):
        pass

    def additional_init(self, *args):
        pass

    def make_reply_markup(self):

        markup = types.ReplyKeyboardMarkup(row_width=self.row_width, resize_keyboard=True)
        is_markup_filled = False
        tmp_buttons = []
        for state_name, attrib in self.triggers_out.items():
            hidden_flag = ((self.hidden_states is not None)
                           and (state_name != self.hidden_states['state_name'])) \
                          or (self.hidden_states is None)
            if len(attrib['phrases']) > 0 and hidden_flag:
                for txt in attrib['phrases']:
                    tmp_buttons.append(txt)
                is_markup_filled = True

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
            bot.send_message(message.chat.id, self.welcome_msg,
                             reply_markup=self.reply_markup, parse_mode='Markdown')
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
    def __init__(self, bot, root_state: str, nodes: List[State], sqldb: SQLighter, logger: logging,
                 dump_path: str = config.dump_graph_path, load_from_dump: bool = config.load_graph):
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
        self.dump_path = dump_path
        self.load = load_from_dump

    def make_nodes_dict(self, nodes):
        return {state.name: state for state in nodes}

    def dump_current_states(self):
        with open(self.dump_path, 'wb') as fout:
            dill.dump({'states': self.usr_states}, fout)

    def load_current_states(self):
        try:
            with open(self.dump_path, 'rb') as fin:
                unpickled = dill.load(fin)
                self.usr_states = unpickled['usr_states']
        except FileNotFoundError:
            pass

    def run(self, message):

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
            signal = self.nodes[new_state_name].welcome_handler(self.bot, message, self.sqldb)
            if signal == 'BACKUP_NOW':
                self.dump_current_states()
                for name_node, node in self.nodes.items():
                    try:
                        node.dump_current_states()
                        print(name_node + ' has been dumped')
                    except Exception as e:
                        print(
                            "-- ERROR DUMP: {} with exception {}:\n {}".format(name_node, e.__class__.__name__, str(e)))
                        continue

                self.bot.send_message(text="All_dumped", chat_id=message.chat.id)
