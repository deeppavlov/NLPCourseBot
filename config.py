# -*- coding: utf-8 -*-
import os

token = os.environ['TOKEN']

hw_possible_to_pass = []
hw_possible_to_check = []
quizzes_possible_to_check = ['quiz 2']
admins = ['fogside', 'madrugado']
quiz_name = 'quiz 2'
quiz_path = './quizzes/quiz2.json'
quizzes_need_to_check = 25
quiz_closed = False
pics_path = './quizzes/pics'
dump_all_path = './backup/'

marks = [str(i) for i in range(1, 6)]
available_hw_resolutions = ('zip', 'rar', '7z', 'tar', 'tar.bz2', 'tar.gz', 'tar.xz', 'ipynb')
bd_name = '/home/fogside/Projects/NLPCourseBot/questions.db'

WEBHOOKS_AVAIL = False
WEBHOOK_HOST = '<webhook addr here>'
PORT = 8444
WEBHOOK_LISTEN = '127.0.0.1'
