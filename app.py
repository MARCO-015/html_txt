import os
import telebot
from bs4 import BeautifulSoup

# Get credentials from environment variables
API_ID = os.getenv("API_ID", "ac24e438ff9a0f600cf3283e6d60b1aa")
API_HASH = os.getenv("API_HASH", "25579552")
TOKEN = os.getenv("BOT_TOKEN", "7385301627:AAHK0x8Lg1AoYdh6mechKu6LJOjaHKuYX50")

bot = telebot.TeleBot(TOKEN)

def html_to_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    text_content = []
    urls = []
    for tag in soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
        text = tag.get_text(strip=True)
        if tag.name == "a" and tag.get("href"):
            url = tag['href']
            urls.append(url)
            text += f" (Link: {url})"
        text_content.append(text)
    
    return "\n".join(text_content), urls

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name
    
    if not file_name.endswith(".html"):
        bot.reply_to(message, "Please upload an HTML file.")
        return
    
    html_path = f"downloads/{file_name}"
    txt_path = html_path.replace(".html", ".txt")
    urls_path = html_path.replace(".html", "_urls.txt")
    
    os.makedirs("downloads", exist_ok=True)
    with open(html_path, "wb") as f:
        f.write(downloaded_file)
    
    extracted_text, urls = html_to_txt(html_path)
    
    if not extracted_text.strip():  # Check if the extracted text is empty
        bot.reply_to(message, "The uploaded HTML file contains no valid text content.")
        os.remove(html_path)
        return
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    
    with open(urls_path, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")
    
    with open(txt_path, "rb") as f:
        bot.send_document(message.chat.id, f)
    
    with open(urls_path, "rb") as f:
        bot.send_document(message.chat.id, f)
    
    os.remove(html_path)
    os.remove(txt_path)
    os.remove(urls_path)

bot.polling()
