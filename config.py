# -*- coding: utf-8 -*-

STATES_ENUM = ['WAIT_USER_INTERACTION', 'COURSE_SELECTION',
               'HW_OR_QUESTION_SELECTION', 'HW_NUM_SELECTION',
               'IN_QUESTION', 'IN_HW_UPLOAD']

possible_to_pass = {'NLP': ["Sem1", "Sem2", "Sem3"], 'RL': ['Sem1', 'Sem2']}
available_hw_resolutions = ('zip', 'rar', '7z', 'tar', 'tar.bz2', 'tar.gz', 'tar.xz', 'ipynb')
bd_name = 'questions.db'

WEBHOOKS_AVAIL = False
WEBHOOK_HOST = ''
WEBHOOK_PORT = 2323
WEBHOOK_LISTEN = ''
WEBHOOK_SSL_CERT = ''
WEBHOOK_SSL_PRIV = ''
