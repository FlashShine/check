import requests
import telebot
import time
import os
import json
from telebot import types
from gate import Tele  # Ensure this module is correctly implemented

# Load bot token securely
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it as an environment variable.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Load subscribers from a file for persistence
SUBSCRIBER_FILE = "subscribers.json"

def load_subscribers():
    """Load authorized user IDs from a JSON file."""
    if os.path.exists(SUBSCRIBER_FILE):
        with open(SUBSCRIBER_FILE, "r") as file:
            return json.load(file)
    return ["7222795580"]  # Default admin users

def save_subscribers(subscribers):
    """Save subscribers to a JSON file."""
    with open(SUBSCRIBER_FILE, "w") as file:
        json.dump(subscribers, file)

subscribers = load_subscribers()

@bot.message_handler(commands=["start"])
def start(message):
    """Handle /start command"""
    if str(message.chat.id) not in subscribers:
        bot.reply_to(message, "❌ Only authorized users! Contact Admin @lurhe")
        return
    bot.reply_to(message, "<b>Welcome to Mash CC Checker!\nPlease send your Combo for checking.\n\nJoin @lurhe\nDeveloped By @lurhe</b>")

@bot.message_handler(commands=["add"])
def add_user(message):
    """Handle /add command to add new users"""
    if str(message.chat.id) != subscribers[0]:  
        bot.reply_to(message, "❌ Only the Admin can use this command!")
        return

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Usage: /add <user_id>")
        return

    new_user = args[1]
    if new_user in subscribers:
        bot.reply_to(message, "⚠️ User is already authorized!")
    else:
        subscribers.append(new_user)
        save_subscribers(subscribers)
        bot.reply_to(message, f"✅ User {new_user} added successfully!")

@bot.message_handler(content_types=["document"])
def process_file(message):
    """Process uploaded files containing card details"""
    if str(message.chat.id) not in subscribers:
        bot.reply_to(message, "❌ Access Denied! Contact Admin @lurhe")
        return

    declined = approved = 0
    processing_msg = bot.reply_to(message, "🔄 Checking Your Cards...⌛").message_id

    file_info = bot.get_file(message.document.file_id)
    file_data = bot.download_file(file_info.file_path)
    
    with open("combo.txt", "wb") as combo_file:
        combo_file.write(file_data)

    try:
        with open("combo.txt", "r") as file:
            card_lines = file.readlines()
            total_cards = len(card_lines)

            for card in card_lines:
                if os.path.exists("stop.stop"):
                    bot.edit_message_text(
                        chat_id=message.chat.id, message_id=processing_msg,
                        text="⏹️ Processing Stopped! \nBot By: @lurhe"
                    )
                    os.remove("stop.stop")
                    return

                # Fetch BIN details
                bin_info = get_bin_info(card[:6])

                # Process the card through gateway
                try:
                    response = str(Tele(card))
                except Exception as e:
                    print(f"Error processing card: {e}")
                    response = "ERROR"

                status, declined, approved = interpret_response(response, declined, approved)

                keyboard = generate_keyboard(card.strip(), status, approved, declined, total_cards)
                
                bot.edit_message_text(
                    chat_id=message.chat.id, message_id=processing_msg,
                    text=f"🔄 Processing Cards...\nPowered by @lurhe | Credit: @lurhe", 
                    reply_markup=keyboard
                )

                if 'success' in response:
                    details = format_card_details(card.strip(), bin_info)
                    bot.reply_to(message, details, parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")

    bot.edit_message_text(
        chat_id=message.chat.id, message_id=processing_msg,
        text="✅ Processing Completed!\nBot By: @lurhe | Credit: @lurhe"
    )

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_callback(call):
    """Stop processing when the user clicks the stop button"""
    open("stop.stop", "w").close()
    bot.answer_callback_query(call.id, "⏹️ Processing will stop soon!")

def get_bin_info(bin_number):
    """Fetch BIN information from binlist API"""
    try:
        response = requests.get(f'https://lookup.binlist.net/{bin_number}')
        data = response.json()
        return {
            "bank": data.get('bank', {}).get('name', 'Unknown'),
            "country": data.get('country', {}).get('name', 'Unknown'),
            "emoji": data.get('country', {}).get('emoji', '🌍'),
            "scheme": data.get('scheme', 'Unknown'),
            "type": data.get('type', 'Unknown'),
            "bank_url": data.get('bank', {}).get('url', 'N/A')
        }
    except:
        return {"bank": "Unknown", "country": "Unknown", "emoji": "🌍", "scheme": "Unknown", "type": "Unknown", "bank_url": "N/A"}

def interpret_response(response, declined, approved):
    """Interpret the response from the gateway"""
    if 'risk' in response or 'declined' in response:
        return "❌ Declined", declined + 1, approved
    elif 'success' in response:
        return "✅ Approved", declined, approved + 1
    else:
        return "⚠️ Unknown Response", declined, approved

def generate_keyboard(card, status, approved, declined, total_cards):
    """Generate an inline keyboard for card processing updates"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(f"🔹 Card: {card}", callback_data='info'),
        types.InlineKeyboardButton(f"🔹 Status: {status}", callback_data='info'),
        types.InlineKeyboardButton(f"🔹 Approved ✅: {approved}", callback_data='info'),
        types.InlineKeyboardButton(f"🔹 Declined ❌: {declined}", callback_data='info'),
        types.InlineKeyboardButton(f"🔹 Total Cards 📊: {total_cards}", callback_data='info'),
        types.InlineKeyboardButton(f"⏹ Stop", callback_data='stop')
    )
    return keyboard

def format_card_details(card, bin_info):
    """Format card details for sending as a message"""
    return f"""
🔹 **Card**: `{card}`
🔹 **Status**: ✅ Approved
🔹 **BIN**: {bin_info["scheme"]} - {bin_info["type"]}
🔹 **Country**: {bin_info["country"]} {bin_info["emoji"]}
🔹 **Bank**: {bin_info["bank"]}
🔹 **Bank URL**: {bin_info["bank_url"]}
🔹 **Checked By**: @lurhe
🔹 **Credit**: @lurhe
"""

if __name__ == "__main__":
    print("🚀 Bot Started Successfully!")
    bot.polling()
