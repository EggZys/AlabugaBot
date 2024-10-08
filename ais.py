import huggingface_hub
from gradio_client import Client

def initialize_api_clients():
    huggingface_hub.login(token='YOUR_HUGGING_FACE_TOKEN')
    gh = Client("Jadssss/AIbot")
    imagine = Client("mukaist/Midjourney")

if __name__ == '__main__':
    print('Главный ais')