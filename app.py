import os
import logging
import telebot
from bs4 import BeautifulSoup

# Get credentials from environment variables
API_ID = os.getenv("API_ID", "ac24e438ff9a0f600cf3283e6d60b1aa")
API_HASH = os.getenv("API_HASH", "25579552")
TOKEN = os.getenv("BOT_TOKEN", "7385301627:AAHK0x8Lg1AoYdh6mechKu6LJOjaHKuYX50")

bot = telebot.TeleBot(TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name

    if not file_name.endswith('.html'):
        bot.send_message(message.chat.id, "Please upload a .html file.")
        return

    downloaded_file = bot.download_file(file_info.file_path)
    html_path = f"/tmp/{file_name}"

    with open(html_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Convert HTML to Text
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        text = soup.get_text()

    txt_path = html_path.replace('.html', '.txt')
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)

    # Send the converted file
    with open(txt_path, 'rb') as txt_file:
        bot.send_document(message.chat.id, txt_file, caption="Here is your converted .txt file.")

    # Cleanup
    os.remove(html_path)
    os.remove(txt_path)

bot.polling()
