import json


class QuizQuestion:
    def __init__(self, name, question_dict, last = False):
        self.name = name
        self.text = question_dict['text']
        self.img = question_dict['img'] if len(question_dict['img']) > 0 else None
        self.variants_one = question_dict['variants'] if len(question_dict['variants']) > 0 else question_dict['grids']
        if len(self.variants_one) == 0:
            self.variants_one = None
        self.variants_multiple = question_dict['several_poss_vars'] if len(
            question_dict['several_poss_vars']) > 0 else None
        self.ask_written = False if (self.variants_one or self.variants_multiple) else True
        self.usr_dict = dict()
        self.is_last = last

    def show(self, bot, msg):
        """
        Send self.text + ans variants to chat with id = msg.chat.id
        :param bot:
        :param msg:
        :return:
        """
        pass

    # @bot.callback_query_handler(func=lambda x: True)
    def callback_handler(self, ans):
        """
        Handle callbacks data from all users
        and update self.usr_dict
        :return:
        """
        pass

    def get_ans(self, username):
        """
        Return ans for username
        :return:
        """
        pass


class Quiz:
    def __init__(self, name, bot, quiz_json_path, sqlighter):
        with open(quiz_json_path) as q:
            self.json_array = json.load(q)
        self.name = name
        self.bot = bot
        self.sqlighter = sqlighter
        self.questions = [QuizQuestion(name="Question {}".format(i), question_dict=d)
                          for i, d in enumerate(self.json_array)]

        # set q.callback_handler to bot for each q in self.questions
        for q in self.questions:
            # TODO: define func to manage
            q.callback_handler = bot.callback_query_handler(func=lambda x: self.get_usr_step(x.chat.id) == q.name)
        self.q_num = len(self.questions)
        self.usersteps = dict()

    def get_usr_step(self, chat_id):
        if chat_id not in self.usersteps:
            # set usr to the first step
            self.usersteps[chat_id] = 0
        return self.usersteps[chat_id]

    def start(self, msg):
        usr_step = self.get_usr_step(msg.chat.id)




    def write_to_db(self):
        pass
