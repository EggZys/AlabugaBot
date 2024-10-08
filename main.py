import discord
from discord.ext import commands
import logging
import os
from data import load_data, save_data_on_exit, load_banned_words
from commands import setup_commands
from events import setup_events
from ais import initialize_api_clients
from config import TOKEN
import atexit


if __name__ == '__main__':
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)

    # Инициализация данных
    level_data = load_data()
    forbidden_words = load_banned_words()

    # Инициализация бота
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='.', intents=intents)
    bot.remove_command('help')

    # Настройка API клиентов
    initialize_api_clients()

    # Регистрация команд
    setup_commands(bot, level_data, forbidden_words)

    # Регистрация событий
    setup_events(bot, level_data, forbidden_words)

    # Сохранение данных при выходе
    atexit.register(save_data_on_exit)

    # Запуск бота
    bot.run(TOKEN)