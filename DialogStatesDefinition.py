from DialogClasses import *
import universal_reply

wait_usr_interaction = State(name='wain_usr_interaction',
                             triggers_out={'main_menu': {'phrase': '\start', 'update_usr_state': None}},
                             welcome_msg=None)

main_menu = State(name='main_menu',
                  triggers_out={'pass_hw_num_selection': {'phrase': 'Сдать дз'},
                                'in_question': {'phrase': 'Задать вопрос к семинару'},
                                'get_mark': {'phrase': 'Узнать оценки за дз'},
                                'check_hw_send_file': {'phrase': 'Проверить дз'},
                                'admin_menu': {'phrase': universal_reply.ADMIN_KEY_PHRASE}},
                  welcome_msg='Выберите доступное действие, пожалуйста 🦊')

in_question = State(name='in_question',
                    triggers_out={'in_question': {'phrase': 'Задать еще один вопрос'},
                                  'main_menu': {'phrase': 'Назад'}},
                    welcome_msg='Сформулируйте вопрос к семинаристу и отправьте его одним сообщением 🦊')

get_mark = State(name='get_mark',
                 triggers_out={'main_menu': {'phrase': 'Назад'}}, handler_welcome=None) # add handler_welcome

