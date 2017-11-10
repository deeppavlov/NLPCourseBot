from DialogClasses import *
import universal_reply
import config

wait_usr_interaction = State(name='wain_usr_interaction',
                             triggers_out={'main_menu': {'phrase': ['\start']}},
                             welcome_msg=None)

main_menu = State(name='main_menu',
                  triggers_out={'pass_hw': {'phrase': ['Сдать дз']},
                                'ask_question': {'phrase': 'Задать вопрос к семинару'},
                                'get_mark': {'phrase': 'Узнать оценки за дз'},
                                'check_hw_send_file': {'phrase': 'Проверить дз'},
                                'admin_menu': {'phrase': universal_reply.ADMIN_KEY_PHRASE}},
                  welcome_msg='Выберите доступное действие, пожалуйста')

# TODO: add handler_out make loop with `ask again possibility`
in_question = State(name='in_question',
                    triggers_out={'main_menu': {'phrase': 'Назад'}},
                    welcome_msg='Сформулируйте вопрос к семинаристу и отправьте его одним сообщением')

# TODO: add handler_welcome to extract marks from bd and simultaneously show them to usr;
get_mark = State(name='get_mark',
                 triggers_out={'main_menu': {'phrase': ['Назад']}}, handler_welcome=None)

# TODO: add handler_out to extract hw file from bd and send it to usr for checking;
# return check_hw_wait_mark state after that;

check_hw_send_file = State(name='check_hw_send_file',
                           welcome_msg='Выберите, пожалуйста, номер задания для проверки',
                           triggers_out={'check_hw_send_file': {'phrase': config.hw_possible_to_pass}})

# TODO: add handler_out to insert mark in bd and offer a user new checking opportunity;
check_hw_wait_mark = State(name='check_hw_wait_mark',
                           welcome_msg='Пожалуйста, оцените работу',
                           triggers_out={'check_hw_wait_mark': {'phrase': config.marks}})


