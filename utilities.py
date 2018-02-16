import requests
import os
# import config
import telebot


def download_file(bot, file_id, folder_name, filename):
    file_info = bot.get_file(file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, file_info.file_path),
                        stream=True)
    local_filename = os.path.join(folder_name, filename)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    with open(local_filename, 'wb') as f:
        for chunk in file.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

def download_picture(pic_url, pic_path):
    with open(pic_path, 'wb') as handle:
        response = requests.get(pic_url, stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)



if __name__ == '__main__':
    bot = telebot.TeleBot(config.token)
    file_id = "<test_token>"
    folder_name = '/home/fogside/tmp/'
    file_name = '<test_name>.ipynb'
    download_file(bot=bot, file_id=file_id, folder_name=folder_name, filename=file_name)
