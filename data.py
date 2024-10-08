import os
import json
import atexit
from config import DATA_FILE, WORDS_FILE, PLUGINS, PAIRS

def load_pairs():
    if os.path.exists(PAIRS):
        with open(PAIRS, 'r') as f:
            return json.load(f)
    else:
        return {}

def load_plugins():
    if os.path.exists(PLUGINS):
        with open(PLUGINS, 'r') as f:
            return json.load(f)
    else:
        return {}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_level_data(level_data):
    with open(DATA_FILE, "w") as f:
        json.dump(level_data, f, indent=4)

def load_banned_words():
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    else:
        return []

def save_data_on_exit():
    save_level_data()

atexit.register(save_data_on_exit)

if __name__ == '__main__':
    print('Главный data')