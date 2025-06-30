import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

