import os
import vk_api
import logging
import random
import redis
import telegram
import time
import json
from functools import partial
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from utils import get_questions, MyLogsHandler


logger = logging.getLogger(__name__)


def send_message(event, vk_api, text):
  vk_api.messages.send(
      user_id=event.user_id,
      message=text,
      keyboard=keyboard.get_keyboard(),
      random_id=get_random_id()
  )


def handle_new_question_request(event, vk_api, questions):
  question, answer = random.choice(list(questions.items()))
  encoded_qa = json.dumps({'question': question, 'answer': answer}, ensure_ascii=False)
  redis_db.set(f'vk-{event.user_id}', encoded_qa)
  send_message(event, vk_api, question)


def handle_solution_attempt(event, vk_api):
  decoded_qa = redis_db.get(f'vk-{event.user_id}').decode()
  answer = json.loads(decoded_qa)['answer']

  if event.text.lower() in answer.lower():
    send_message(event, vk_api, f'😎👍 Поздравляю! Правильный ответ - {answer}\nДля следующего вопроса нажми «Новый вопрос»')

  else:
    send_message(event, vk_api, '😦 Неправильно... Попробуешь ещё раз?')


def handle_give_up_attempt(event, vk_api, questions):
  decoded_qa = redis_db.get(f'vk-{event.user_id}').decode()
  answer = json.loads(decoded_qa)['answer']
  send_message(event, vk_api, f'🐸 Ну что ж, правильный ответ: {answer}\nДержи следующий вопрос.\n')
  handle_new_question_request(event, vk_api, questions)


if __name__ == "__main__":
  load_dotenv()
  TG_LOGGING_BOT_TOKEN = os.getenv('TG_LOGGING_BOT_TOKEN')
  CHAT_ID = os.getenv('TG_CHAT_ID')
  VK_COMMUNITY_TOKEN = os.getenv('VK_COMMUNITY_TOKEN')
  REDIS_HOST = os.getenv('REDIS_HOST')
  REDIS_PORT = os.getenv('REDIS_PORT')
  REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

  redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

  logging_bot = telegram.Bot(token=TG_LOGGING_BOT_TOKEN)
  logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
  logger.setLevel(logging.INFO)
  logger.addHandler(MyLogsHandler(logging_bot, CHAT_ID))
  logger.info('Бот vk-quiz запущен')

  questions = get_questions()

  vk_session = vk_api.VkApi(token=VK_COMMUNITY_TOKEN)
  vk_api = vk_session.get_api()
  longpoll = VkLongPoll(vk_session)

  keyboard = VkKeyboard(one_time=True)

  keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
  keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

  keyboard.add_line()
  keyboard.add_button('Мой счёт', color=VkKeyboardColor.POSITIVE)

  send_question = partial(handle_new_question_request, questions=questions)
  send_answer = partial(handle_give_up_attempt, questions=questions)

  while True:
    try:
      for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

          if event.text == 'Start':
            send_message(event, vk_api, '🤠 Привет! Начнем викторину?')

          elif event.text == 'Новый вопрос':
            send_question(event, vk_api)

          elif event.text == 'Сдаться':
            send_answer(event, vk_api)

          else:
            handle_solution_attempt(event, vk_api)

    except Exception:
      logger.exception('Бот vk-quiz упал с ошибкой: ')
      time.sleep(10)
