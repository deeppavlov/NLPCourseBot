import DialogStatesDefinition
from DialogClasses import DialogGraph
import telebot
import config
from flask import Flask, request
from Sqlighter import SQLighter

bot = telebot.TeleBot(config.token, threaded=False)
nodes = [DialogStatesDefinition.wait_usr_interaction,
         DialogStatesDefinition.main_menu,

         DialogStatesDefinition.ask_question_start,
         DialogStatesDefinition.save_question,

         DialogStatesDefinition.admin_menu,
         DialogStatesDefinition.know_new_questions,
         DialogStatesDefinition.see_hw_stat,

         DialogStatesDefinition.pass_hw_num_selection,
         DialogStatesDefinition.pass_hw_chosen_num,
         DialogStatesDefinition.pass_hw_upload,

         DialogStatesDefinition.get_mark,

         DialogStatesDefinition.check_hw_num_selection,
         DialogStatesDefinition.check_hw_save_mark,
         DialogStatesDefinition.check_hw_send]

sqldb = SQLighter(config.bd_name)
dialogGraph = DialogGraph(bot, root_state='WAIT_USR_INTERACTION', nodes=nodes, sqldb=sqldb)


@bot.message_handler(content_types=['text', 'document', 'photo'])
def handler(message):
    dialogGraph.run(message=message)


if __name__ == '__main__':
    if config.WEBHOOKS_AVAIL:

        WEBHOOK_HOST = config.WEBHOOK_HOST
        PORT = config.PORT
        WEBHOOK_LISTEN = config.WEBHOOK_LISTEN

        server = Flask(__name__)


        @server.route("/webhook", methods=['POST'])
        def getMessage():
            bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
            return "!", 200


        server.run(host=WEBHOOK_LISTEN, port=PORT)

        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_HOST)
    else:
        bot.delete_webhook()
        bot.polling(none_stop=True)
