import os
import logging

class MyLogsHandler(logging.Handler):
    def __init__(self, logging_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.logging_bot = logging_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.logging_bot.send_message(chat_id=self.chat_id, text=log_entry)


def get_questions():
  questions = []
  answers = []
  
  path = 'questions'
  questions_files = [file for file in os.listdir(path)]

  for questions_file in questions_files:
    current_path = os.path.join(path, questions_file)
    
    with open(current_path, 'r', encoding='KOI8-R') as file:
      for line in file.read().split('\n\n'):
      
        if line.startswith('Вопрос'):
          question = ' '.join(line.split('\n')[1:])
          questions.append(question)
        
        elif line.startswith('Ответ'):
          answer = ' '.join(line.split('\n')[1:])
          answers.append(answer)

  return dict(zip(questions,answers))