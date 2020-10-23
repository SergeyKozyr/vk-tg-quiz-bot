import logging
import os
import random
import redis
import time
from dotenv import load_dotenv
from utils import get_questions, MyLogsHandler
from enum import Enum
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
  custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
  reply_markup = ReplyKeyboardMarkup(custom_keyboard)
  user = update.message.from_user
  update.message.reply_text(f'🤠 Привет {user.first_name}! Начнем викторину?', reply_markup=reply_markup)
  return State.QUESTION


def handle_new_question_request(bot, update):
  question, answer = random.choice(list(questions.items()))
  redis_db.set(update.message.from_user.id, question)
  update.message.reply_text(question)

  return State.SOLUTION


def handle_solution_attempt(bot, update):
  question = redis_db.get(update.message.from_user.id).decode()
  answer = questions[question].split('.')[0]

  if answer.lower() in update.message.text.lower():
    update.message.reply_text(f'😎👍 Поздравляю! Правильный ответ - {questions[question]}. Для следующего вопроса нажми «Новый вопрос»')

    return State.QUESTION

  else:
    update.message.reply_text('😦 Неправильно...Попробуешь ещё раз?')


def handle_give_up_attempt(bot, update):
  question = redis_db.get(update.message.from_user.id).decode()
  answer = questions[question]
  update.message.reply_text(f'🐸 Ну что ж, правильный ответ: {answer}, держи следующий вопрос.\n')
  handle_new_question_request(bot, update)


def cancel(bot, update):
  user = update.message.from_user
  logger.info(f"User {user.first_name} {user.last_name} canceled the conversation.")
  update.message.reply_text('Давай, до скорого 👋😎', reply_markup=ReplyKeyboardRemove())

  return ConversationHandler.END


def error(bot, update, error):
  logger.error('Update "%s" caused error "%s"', update, error)


if __name__ == '__main__':
  load_dotenv()
  TRIVIA_BOT_TOKEN = os.getenv('TRIVIA_BOT_TOKEN')
  TG_LOGGING_BOT_TOKEN = os.getenv('TG_LOGGING_BOT_TOKEN')
  CHAT_ID = os.getenv('TG_CHAT_ID')
  REDIS_HOST = os.getenv('REDIS_HOST')
  REDIS_PORT = os.getenv('REDIS_PORT')
  REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

  State = Enum('State', 'QUESTION SOLUTION')

  redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=1)

  questions = get_questions()

  logging_bot = Bot(token=TG_LOGGING_BOT_TOKEN)
  logger.setLevel(logging.INFO)
  logger.addHandler(MyLogsHandler(logging_bot, CHAT_ID))
  logger.info('Бот tg-quiz запущен')

  updater = Updater(TRIVIA_BOT_TOKEN)
  dp = updater.dispatcher

  conv_handler = ConversationHandler(
      entry_points=[CommandHandler('start', start)],

      states={
          State.QUESTION: [RegexHandler('^(Новый вопрос)$', handle_new_question_request)],

          State.SOLUTION: [RegexHandler('^(Сдаться)$', handle_give_up_attempt),
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
