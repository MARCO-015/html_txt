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

# Command handler for /h2t
@bot.message_handler(commands=['h2t'])
def request_html(message):
    bot.reply_to(message, "**Send Your HTML file**")

# File handler for processing the HTML file
@bot.message_handler(content_types=['document'])
def process_html_file(message):
    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        html_file_path = message.document.file_name
        
        # Save the downloaded HTML file
        with open(html_file_path, "wb") as f:
            f.write(downloaded_file)
        
        # Process the HTML file
        with open(html_file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'html.parser')
            tables = soup.find_all('table')
            videos = []
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:  # Ensure there are enough columns
                        name = cols[0].get_text(strip=True)
                        link_tag = cols[1].find('a')
                        if link_tag and 'href' in link_tag.attrs:
                            link = link_tag['href']
                            videos.append(f'{name}: {link}')
        
        # Define .txt file path
        txt_file_path = os.path.splitext(html_file_path)[0] + ".txt"
        
        # Save to .txt file only if there is content
        if videos:
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(videos))
        else:
            bot.send_message(message.chat.id, "No video links found in the HTML file.")
            os.remove(html_file_path)
            return  # Stop execution
        
        # Check if file is empty
        if os.path.getsize(txt_file_path) == 0:
            bot.send_message(message.chat.id, "The generated TXT file is empty. Please check your HTML file.")
            os.remove(txt_file_path)
            os.remove(html_file_path)
            return
        
        # Send the file
        with open(txt_file_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption="Here is your TXT file.")
        
        # Cleanup
        os.remove(html_file_path)
        os.remove(txt_file_path)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")
        logging.error(f"Error: {str(e)}")

# Start the bot
bot.polling(none_stop=True)
