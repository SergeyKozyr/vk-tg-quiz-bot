## Description

Simple quiz bots for Vkontakte and Telegram. Bot sends a random question from the `questions` directory, if the user answers correctly, bot congratulates the user and awaits for the next question, if the user is wrong, bot asks the user to try again. After the question is received, the user can press the give up button to get the right answer and the next question.

Each bot's logs are sent to Logging bot via telegram.

## Usage

Start the dialog with [Telegram bot](https://t.me/SimpleTrivia_bot) or [VK bot](https://vk.com/im?media=&sel=-199640313).

## Example

**Vkontakte:**

![Vkontakte bot]()

---

**Telegram:**

![Telegram bot]()

## How to install

1) **Running on a local machine**

Create .env file with the variables:

```
VK_COMMUNITY_TOKEN
TRIVIA_BOT_TOKEN
TG_LOGGING_BOT_TOKEN
TG_CHAT_ID
REDIS_HOST
REDIS_PASSWORD
REDIS_PORT 
```

Create [vk group](https://vk.com/groups), in your group click manage -> Api usage and generate an access token with community management and messages access settings.

Telegram bot tokens are available after creation in [@BotFather](https://telegram.me/botfather) chat. For your chat id send, a message to [@userinfobot](https://telegram.me/userinfobot).

Create [Redis database](https://redislabs.com/)

Install dependencies.

`pip install -r requirements.txt`

Extract all files from `quiz-questions.zip` into the `questions` directory.

Run the script, send a message to the bot.

`python vk-bot.py`

`python tg-bot.py`

---

2) **Deploying with Heroku**

Clone the repository, sign up or log in at [Heroku](https://www.heroku.com/).

Create a new Heroku app, click on Deploy tab and connect your Github account.

Type in the repository name and click Deploy Branch at the bottom of the page.

Set up environment variables at the Settings tab in Config Vars 

Turn on the `bot` process on Resources tab.

--- 

## Project Goals
The code is written for educational purposes at online-course for web-developers [dvmn.org](https://dvmn.org).
