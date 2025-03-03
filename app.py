import os
import asyncio
import requests
import telebot
import zipfile
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message
from urllib.parse import urljoin

# Get credentials from environment variables
OWNER = 7548265642
API_ID = int(os.getenv("API_ID", "25579552"))
API_HASH = os.getenv("API_HASH", "ac24e438ff9a0f600cf3283e6d60b1aa")
TOKEN = os.getenv("BOT_TOKEN", "7385301627:AAHK0x8Lg1AoYdh6mechKu6LJOjaHKuYX50")

# Initialize bots
bot = telebot.TeleBot(TOKEN)
pyro_bot = Client("html_to_txt_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

# Function to extract text, URLs, and video links from an HTML file
def html_to_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    text_content, urls, videos = [], [], []
    
    for tag in soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
        text = tag.get_text(strip=True)
        if tag.name == "a" and tag.get("href"):
            url = tag['href']
            urls.append(url)
            text += f" (Link: {url})"
        text_content.append(text)
    
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 1 and cols[1].find('a'):
                name = cols[0].get_text().strip()
                link = cols[1].find('a')['href']
                videos.append(f'{name}: {link}')
    
    return "\n".join(text_content), urls, videos

# Function to download website source code (HTML, CSS, JS, Images)
def download_website(url, save_dir):
    response = requests.get(url)
    if response.status_code != 200:
        return "Failed to fetch the website."
    
    os.makedirs(save_dir, exist_ok=True)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Save HTML file
    with open(os.path.join(save_dir, "index.html"), "w", encoding="utf-8") as file:
        file.write(response.text)
    
    assets = []
    for tag in soup.find_all(["link", "script", "img"]):
        file_url = tag.get("href") or tag.get("src")
        if file_url:
            full_url = urljoin(url, file_url)
            assets.append(full_url)
    
    for asset in assets:
        asset_response = requests.get(asset)
        if asset_response.status_code == 200:
            parsed_url = urlparse(asset)
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, "wb") as file:
                file.write(asset_response.content)
    
    zip_path = save_dir + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(save_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, save_dir))
    
    return zip_path

# Pyrogram handler for /download
@pyro_bot.on_message(filters.command("download"))
async def download_command(client: Client, message: Message):
    url = message.text.split(" ", 1)[-1]
    if not url.startswith("http"):
        await message.reply_text("❌ Please provide a valid URL.")
        return
    
    save_path = f"downloads/{message.chat.id}"
    zip_file = download_website(url, save_path)
    
    if zip_file:
        await message.reply_document(zip_file, caption="📂 Website Downloaded")
        os.remove(zip_file)
    else:
        await message.reply_text("❌ Failed to download the website.")
        
# ✅ Pyrogram Handler for /txt Command
@pyro_bot.on_message(filters.command("txt"))
async def ask_for_file(client: Client, message: Message):
    await message.reply_text("📂 **Send Your HTML file**")

@pyro_bot.on_message(filters.document)
async def handle_html_file(client: Client, message: Message):
    if not message.document.file_name.endswith(".html"):
        await message.reply_text("❌ Please upload a valid HTML file.")
        return
    
    html_file = await client.download_media(message.document)
    extracted_text, urls, videos = html_to_txt(html_file)

    if not extracted_text.strip():
        await message.reply_text("❌ The uploaded HTML file contains no valid text content.")
        os.remove(html_file)
        return
    
    txt_file = html_file.replace(".html", ".txt")
    urls_file = html_file.replace(".html", "_urls.txt")
    videos_file = html_file.replace(".html", "_videos.txt")

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    with open(urls_file, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))
    with open(videos_file, "w", encoding="utf-8") as f:
        f.write("\n".join(videos))
    
    await message.reply_document(txt_file, caption="📜 Extracted Text")
    await message.reply_document(urls_file, caption="🔗 Extracted URLs")
    await message.reply_document(videos_file, caption="🎥 Extracted Videos")
    
    os.remove(html_file)
    os.remove(txt_file)
    os.remove(urls_file)
    os.remove(videos_file)

# ✅ Run the bot
pyro_bot.run()
