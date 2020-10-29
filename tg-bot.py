import logging
import os
import random
import redis
import time
import json
from functools import partial
from dotenv import load_dotenv
from utils import get_questions, MyLogsHandler
from enum import Enum
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)


logger = logging.getLogger(__name__)


def start(bot, update):
  custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
  reply_markup = ReplyKeyboardMarkup(custom_keyboard)
  user = update.message.from_user
  update.message.reply_text(f'🤠 Привет {user.first_name}! Начнем викторину?', reply_markup=reply_markup)
  return State.QUESTION


def handle_new_question_request(bot, update, questions):
  user = update.message.from_user
  question, answer = random.choice(list(questions.items()))
  encoded_qa = json.dumps({'question': question, 'answer': answer}, ensure_ascii=False)
  redis_db.set(f'tg-{user.id}', encoded_qa)
  update.message.reply_text(question)

  return State.SOLUTION


def handle_solution_attempt(bot, update):
  user = update.message.from_user
  decoded_qa = redis_db.get(f'tg-{user.id}').decode()
  answer = json.loads(decoded_qa)['answer']

  if update.message.text.lower() in answer.lower():
    update.message.reply_text(f'😎👍 Поздравляю! Правильный ответ - {answer}. Для следующего вопроса нажми «Новый вопрос»')

    return State.QUESTION

  else:
    update.message.reply_text('😦 Неправильно...Попробуешь ещё раз?')


def handle_give_up_attempt(bot, update, questions):
  user = update.message.from_user
  decoded_qa = redis_db.get(f'tg-{user.id}').decode()
  answer = json.loads(decoded_qa)['answer']
  update.message.reply_text(f'🐸 Ну что ж, правильный ответ: {answer}, держи следующий вопрос.\n')
  handle_new_question_request(bot, update, questions)


def cancel(bot, update):
  user = update.message.from_user
  logger.info(f"User {user.first_name} {user.last_name} canceled the conversation.")
  update.message.reply_text('Давай, до скорого 👋😎', reply_markup=ReplyKeyboardRemove())

  return ConversationHandler.END


def error(bot, update, error):
  logger.error('Update "%s" caused error "%s"', update, error)


if __name__ == '__main__':
  load_dotenv()
  TG_QUIZBOT_TOKEN = os.getenv('TG_QUIZBOT_TOKEN')
  TG_LOGGING_BOT_TOKEN = os.getenv('TG_LOGGING_BOT_TOKEN')
  CHAT_ID = os.getenv('TG_CHAT_ID')
  REDIS_HOST = os.getenv('REDIS_HOST')
  REDIS_PORT = os.getenv('REDIS_PORT')
  REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

  State = Enum('State', 'QUESTION SOLUTION')

  redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

  questions = get_questions()

  logging_bot = Bot(token=TG_LOGGING_BOT_TOKEN)
  logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
  logger.setLevel(logging.INFO)
  logger.addHandler(MyLogsHandler(logging_bot, CHAT_ID))
  logger.info('Бот tg-quiz запущен')

  updater = Updater(TG_QUIZBOT_TOKEN)
  dp = updater.dispatcher

  send_question = partial(handle_new_question_request, questions=questions)
  send_answer = partial(handle_give_up_attempt, questions=questions)

  conv_handler = ConversationHandler(
      entry_points=[CommandHandler('start', start)],

      states={
          State.QUESTION: [RegexHandler('^(Новый вопрос)$', send_question)],

          State.SOLUTION: [RegexHandler('^(Сдаться)$', send_answer),
                           MessageHandler(Filters.text, handle_solution_attempt)]
      },

      fallbacks=[CommandHandler('cancel', cancel)]
  )

  dp.add_handler(conv_handler)
  dp.add_error_handler(error)

  while True:
    try:
      updater.start_polling()
      updater.idle()

    except Exception:
      logger.exception('Бот tg-quiz упал с ошибкой: ')
      time.sleep(10)
