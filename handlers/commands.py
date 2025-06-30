from telegram.ext import CommandHandler
from .callbacks import start_callback, onboard_callback, recipe_callback

COMMANDS = [
    CommandHandler('start', start_callback),
    CommandHandler('onboard', onboard_callback),
    CommandHandler('recipe', recipe_callback),
    # add more commands here
]