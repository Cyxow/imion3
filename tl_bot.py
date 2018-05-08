# -*- coding: utf-8 -*

import time
import eventlet
import requests
import logging
import telebot
from time import sleep

# Сылка на получение 2 послежних постов со стены в vk (access token изменён)
URL_VK = 'https://api.vk.com/method/wall.get?owner_id=-107349300&count=2&filter=owner&access_token=c208785ed9537f665780158746858e3236c834e2fbd2d1888dc0&v=5.60'
#Сохранение номера последнего поста
FILENAME_VK = 'last_known_id.txt'
#для составления ссылки на пост в группе с id 107349300
BASE_POST_URL = 'https://vk.com/wall-107349300_'

#id текущего или прошлого стрима
FILENAME_youtube = 'last_stream_id.txt'
#для составления ссылки на начавшийчя стрим
URL_STREAM = 'https://www.youtube.com/watch?v='
#Получение информации о последнем видео (key изменён)
URL_youtube = 'https://www.googleapis.com/youtube/v3/search?key=A3IzDko7EHu8NZAQ06qqR86vALjSY&channelId=UCNJ0iop1uEVhw-tOZUxKM5Q&part=snippet&order=date&maxResults=2&eventType=live&type=video'

#информация для бота в telegram (token изменён)
BOT_TOKEN = '515355689:AAE-1_2iUFpE2XR5Tokd_GU'
CHANNEL_NAME = '@notification_for_G1deon'

#инцилизация бота
bot = telebot.TeleBot(BOT_TOKEN)

def get_data():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL_VK)
        return feed.json()
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def get_data_youtube():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL_youtube)
        return feed.json()
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving youtube JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def send_new_posts(items, last_id):
    for item in items:
        if item['id'] <= last_id:
            break
        link = '{!s}{!s}'.format(BASE_POST_URL, item['id'])
	#поссылка сообщения
        bot.send_message(CHANNEL_NAME, link)
        # Спим секунду, чтобы избежать разного рода ошибок
        time.sleep(1)
    return


def check_new_posts_vk():
    # Пишем текущее время начала
    logging.info('[VK] Started scanning for new posts')
    #получение из файла номер последнего поста
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last ID (VK) = {!s}'.format(last_id))
    try:
        feed = get_data()
        # Если ранее случился таймаут, пропускаем итерацию
        if feed is not None:
            entries = feed['response']['items']
            try:
                # Если пост был закреплен, пропускаем его
                tmp = entries[0]['is_pinned']
                # Отправка сообщений
                send_new_posts(entries[1:], last_id)
            except KeyError:
                send_new_posts(entries, last_id)
            # Записываем новый last_id в файл.
            with open(FILENAME_VK, 'wt') as file:
                try:
                    tmp = entries[0]['is_pinned']
                    # Если первый пост - закрепленный, то сохраняем ID второго
                    file.write(str(entries[1]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    logging.info('[VK] Finished scanning')
    return


def check_new_stream_youtube():
    logging.info('[youtube] Started scanning for new stream')
    with open(FILENAME_youtube, 'rt') as file:
        last_id = file.read()
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last stream id = {!s}'.format(last_id))
    try:
	#получение информации с YuoTobe
        feed = get_data_youtube()
        # Если ранее случился таймаут, пропускаем итерацию
        if feed is not None:
            entries = feed['items']
            if last_id != entries[0]['id']['videoId']:
		#поссылаем ссылку на стрим
                bot.send_message(CHANNEL_NAME, 'G1deon start stream: ' + URL_STREAM + entries[0]['id']['videoId'])
            with open(FILENAME_youtube, 'wt') as file:
                file.write(str(entries[0]['id']['videoId']))
                logging.info('New last_id (youtube) is {!s}'.format((entries[0]['id']['videoId'])))
    except Exception as ex:
        logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    logging.info('[VK] Finished scanning')
    return


if __name__ == '__main__':
    # Избавляемся от спама в логах от библиотеки requests
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    # Настраиваем логгер
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO,
                        filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    while True:
	#проверка поста в vk
        check_new_posts_vk()
	#получение информации о последнем видео
        check_new_stream_youtube()
        # Пауза в 2 минуты перед повторной проверкой
        logging.info('[App] Script went to sleep.')
        time.sleep(60 * 2)
    logging.info('[App] Script exited.\n')
