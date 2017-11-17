# -*- coding: utf-8 -*-
import os

token = os.environ['TOKEN']

hw_possible_to_pass = ["Sem4", "Sem5"]
hw_possible_to_check = ["Sem1", "Sem2", "Sem4", "Sem5"]
admins = ['fogside', 'madrugado']

marks = [str(i) for i in range(1, 6)]
available_hw_resolutions = ('zip', 'rar', '7z', 'tar', 'tar.bz2', 'tar.gz', 'tar.xz', 'ipynb')
bd_name = '/home/fogside/Projects/NLPCourseBot/questions.db'

WEBHOOKS_AVAIL = False
WEBHOOK_HOST = '<webhook addr here>'
PORT = 8444
WEBHOOK_LISTEN = '127.0.0.1'
