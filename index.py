import os
import json
from http.server import BaseHTTPRequestHandler
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from movies_scraper import search_movies, get_movie

TOKEN = os.getenv("TOKEN")
bot = Bot(TOKEN)

def start(update, context):
    update.message.reply_text("Welcome! Send me a movie name to search.")

def search(update, context):
    query = update.message.text
    results = search_movies(query)
    if results:
        keyboard = [[InlineKeyboardButton(movie['title'], callback_data=movie['id'])] for movie in results]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Search Results:', reply_markup=reply_markup)
    else:
        update.message.reply_text('No results found.')

def movie_callback(update, context):
    query = update.callback_query
    movie_data = get_movie(query.data)
    if movie_data:
        message = f"Title: {movie_data['title']}\n\nDownload Links:\n"
        for quality, link in movie_data['links'].items():
            message += f"{quality}: {link}\n"
        query.message.reply_text(message)
    else:
        query.message.reply_text('Error fetching movie data.')

def setup_dispatcher(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search))
    dispatcher.add_handler(CallbackQueryHandler(movie_callback))
    return dispatcher

def handle_update(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher = setup_dispatcher(Dispatcher(bot, None, use_context=True))
    dispatcher.process_update(update)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        self.send_response(200)
        self.end_headers()
        update = json.loads(post_data)
        handle_update(update)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Hello, this is a Telegram bot server. Please use POST requests to interact with the bot.".encode())

# For local testing
if __name__ == "__main__":
    from telegram.ext import Updater
    updater = Updater(TOKEN, use_context=True)
    setup_dispatcher(updater.dispatcher)
    updater.start_polling()
    updater.idle()
