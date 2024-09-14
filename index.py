import os
import logging
from io import BytesIO
from queue import Queue
import requests
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
from movies_scraper import search_movies, get_movie

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment variables
try:
    TOKEN = os.environ["TOKEN"]
    URL = os.environ.get("VERCEL_URL", "https://your-vercel-url.vercel.app")  # Fallback to a default URL if not set
except KeyError as e:
    logger.error(f"Missing environment variable: {e}")
    raise

bot = Bot(TOKEN)

def welcome(update, context) -> None:
    logger.info(f"Welcome message sent to user {update.message.from_user.first_name}")
    update.message.reply_text(f"Hello {update.message.from_user.first_name}, Welcome to AI Movies.\n"
                              f"🔥 Download Your Favourite Movies For 💯 Free And 🍿 Enjoy it.")
    update.message.reply_text("👇 Enter Movie Name 👇")

def find_movie(update, context):
    query = update.message.text
    logger.info(f"Searching for movie: {query}")
    search_results = update.message.reply_text("Processing...")
    try:
        movies_list = search_movies(query)
        if movies_list:
            keyboards = []
            for movie in movies_list:
                keyboard = InlineKeyboardButton(movie["title"], callback_data=movie["id"])
                keyboards.append([keyboard])
            reply_markup = InlineKeyboardMarkup(keyboards)
            search_results.edit_text('Search Results...', reply_markup=reply_markup)
        else:
            search_results.edit_text('Sorry 🙏, No Result Found!\nCheck If You Have Misspelled The Movie Name.')
    except Exception as e:
        logger.error(f"Error in find_movie: {e}")
        search_results.edit_text('An error occurred while searching for the movie. Please try again later.')

def movie_result(update, context) -> None:
    query = update.callback_query
    logger.info(f"Fetching movie details for ID: {query.data}")
    try:
        s = get_movie(query.data)
        response = requests.get(s["img"], timeout=10)
        response.raise_for_status()
        img = BytesIO(response.content)
        query.message.reply_photo(photo=img, caption=f"🎥 {s['title']}")
        link = ""
        links = s["links"]
        for i in links:
            link += "🎬" + i + "\n" + links[i] + "\n\n"
        caption = f"⚡ Fast Download Links :-\n\n{link}"
        if len(caption) > 4095:
            for x in range(0, len(caption), 4095):
                query.message.reply_text(text=caption[x:x+4095])
        else:
            query.message.reply_text(text=caption)
    except Exception as e:
        logger.error(f"Error in movie_result: {e}")
        query.message.reply_text('An error occurred while fetching movie details. Please try again later.')

def setup():
    update_queue = Queue()
    dispatcher = Dispatcher(bot, update_queue, use_context=True)
    dispatcher.add_handler(CommandHandler('start', welcome))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, find_movie))
    dispatcher.add_handler(CallbackQueryHandler(movie_result))
    return dispatcher

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return respond()

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), bot)
    setup().process_update(update)
    return jsonify({"status": "ok"})

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = f"{URL}/{TOKEN}"
    if request.method == 'GET':
        return f"""
        To set the webhook manually, send a POST request to this URL with the following body:
        {{
            "url": "{webhook_url}"
        }}
        """
    elif request.method == 'POST':
        try:
            bot.delete_webhook()
            s = bot.set_webhook(webhook_url)
            if s:
                return jsonify({"status": "webhook setup ok"})
            else:
                return jsonify({"status": "webhook setup failed"})
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
