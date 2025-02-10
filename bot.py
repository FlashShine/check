import requests
import telebot
import time
from telebot import types
from gatet import Tele  # Ensure this module is correctly installed or replace with the proper one
import os

# Bot token and initialization
token = '7630980959:AAHVeedkDDYeFSam3pm9OSnlpc-WutMXlCE'
bot = telebot.TeleBot(token, parse_mode="HTML")

# Subscribers list (authorized users)
subscriber = [
    '6590816421',  # Admin (First user)
    '6590816421', 
    '6590816421', 
    '6590816421', 
    '6590816421', 
    '7222795580'
]

@bot.message_handler(commands=["start"])
def start(message):
    """Handler for /start command"""
    if str(message.chat.id) not in subscriber:
        bot.reply_to(message, "❌ Only For authorized users! Contact Admin @lurhe")
        return
    bot.reply_to(message, "<b>Welcome To Mash  CC Checker\n Please send the Combo For check . \n\n Must Join @INFO_ALEN\nDeveloped By @Nonsecularmuslim </b>")

@bot.message_handler(commands=["add"])
def add_user(message):
    """Handler for /add command"""
    chat_id = str(message.chat.id)

    # Ensure only the first user in the list (admin) can use /add
    if chat_id != subscriber[0]:  
        bot.reply_to(message, "❌ Admin required to use this command!")
        return

    # Extracting the new user ID from the message
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Usage: /add <user_id>")
        return

    new_user = args[1]
    
    # Check if the user is already in the list
    if new_user in subscriber:
        bot.reply_to(message, "⚠️ User already authorized!")
        return

    # Add the new user to the list
    subscriber.append(new_user)
    bot.reply_to(message, f"✅ User {new_user} added successfully!")

@bot.message_handler(content_types=["document"])
def main(message):
    """Handler for processing uploaded files"""
    if str(message.chat.id) not in subscriber:
        bot.reply_to(message, "❌ Access Denied! Contact Admin @Nonsecularmuslim")
        return

    # Status initialization
    declined = 0
    approved = 0
    processing_msg = bot.reply_to(message, "🔄 Checking Your Cards...⌛").message_id

    # Download and save the uploaded file
    file_data = bot.download_file(bot.get_file(message.document.file_id).file_path)
    with open("combo.txt", "wb") as combo_file:
        combo_file.write(file_data)

    try:
        with open("combo.txt", 'r') as file:
            card_lines = file.readlines()
            total_cards = len(card_lines)

            for card in card_lines:
                # Check for stop signal
                if os.path.exists("stop.stop"):
                    bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg, 
                                          text="⏹️ Processing Stopped! \nBot By: @lurhe)
                    os.remove("stop.stop")
                    return

                # Fetch BIN details from binlist API
                try:
                    bin_data = requests.get(f'https://lookup.binlist.net/{card[:6]}').json()
                    bank = bin_data.get('bank', {}).get('name', 'Unknown')
                    country = bin_data.get('country', {}).get('name', 'Unknown')
                    country_emoji = bin_data.get('country', {}).get('emoji', '🌍')
                    scheme = bin_data.get('scheme', 'Unknown')
                    card_type = bin_data.get('type', 'Unknown')
                    bank_url = bin_data.get('bank', {}).get('url', 'N/A')
                except Exception:
                    bank, country, country_emoji, scheme, card_type, bank_url = ('Unknown',) * 6

                # Process the card through gateway (mocked by Tele module)
                try:
                    response = str(Tele(card))
                except Exception as e:
                    print(f"Error: {e}")
                    response = "ERROR"

                # Interpret response
                if 'risk' in response or 'declined' in response:
                    status = "❌ Declined"
                    declined += 1
                elif 'success' in response:
                    status = "✅ Approved"
                    approved += 1
                else:
                    status = "⚠️ Unknown Response"

                # Update the progress
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    types.InlineKeyboardButton(f"🔹 Card: {card.strip()} ", callback_data='info'),
                    types.InlineKeyboardButton(f"🔹 Status: {status} ", callback_data='info'),
                    types.InlineKeyboardButton(f"🔹 Approved ✅: {approved} ", callback_data='info'),
                    types.InlineKeyboardButton(f"🔹 Declined ❌: {declined} ", callback_data='info'),
                    types.InlineKeyboardButton(f"🔹 Total Cards 📊: {total_cards} ", callback_data='info'),
                    types.InlineKeyboardButton(f"⏹ Stop", callback_data='stop')
                )

                bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg, 
                                      text=f"🔄 Processing Cards...\nPowered by @lurhe | Credit: @PhiloBots", 
                                      reply_markup=keyboard)

                # Send individual card details if approved
                if 'success' in response:
                    details = f"""
🔹 **Card**: `{card.strip()}`
🔹 **Status**: ✅ Approved
🔹 **BIN**: {card[:6]} - {scheme} - {card_type}
🔹 **Country**: {country} {country_emoji}
🔹 **Bank**: {bank}
🔹 **Bank URL**: {bank_url}
🔹 **Checked By**: @lurhe
🔹 **Credit**: @PhiloBots
"""
                    bot.reply_to(message, details, parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")

    bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg, 
                          text="✅ Processing Completed!\nBot By: @Nonsecularmuslim | Credit: @Nonsecularmuslim")

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_callback(call):
    """Handler for stop callback"""
    with open("stop.stop", "w") as file:
        pass
    bot.answer_callback_query(call.id, "⏹️ Processing will be stopped soon!")

# Bot execution
if __name__ == "__main__":
    print("+-------------------------------------------+")
    print("|         Bot Started Successfully!         |")
    print("+-------------------------------------------+")
    bot.polling()
