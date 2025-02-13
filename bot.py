import requests
import telebot
import time
import re
import os
import json
import asyncio
from telebot import types
from full_checker import run_checker  # Import Braintree checker
from stripe_charge import process_payment as stripe_payment  # Import Stripe charge module
from braintree_auth import get_braintree_auth  # Import Braintree auth module

# Telegram Bot Configuration
TOKEN = '8099253215:AAFwlNrt1gOTRj329LCB9QTQKISyQvp11A4'  # Replace with actual bot token
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
ALLOWED_USERS = ['7222795580']  # List of allowed user IDs (Admins)
CREDIT_FILE = 'user_credits.json'  # Credit System File
DEFAULT_CREDITS = 1000  # Default starting credits for new users

# Load and Save Credits
def load_credits():
    try:
        with open(CREDIT_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_credits(credits):
    with open(CREDIT_FILE, 'w') as f:
        json.dump(credits, f, indent=4)

def get_user_credits(user_id):
    credits = load_credits()
    return credits.get(str(user_id), DEFAULT_CREDITS)  # Default credits for new users

def deduct_credits(user_id, amount=1):
    credits = load_credits()
    user_str_id = str(user_id)
    
    if user_str_id not in credits:
        credits[user_str_id] = DEFAULT_CREDITS  # Give default credits if user is new

    if credits[user_str_id] >= amount:
        credits[user_str_id] -= amount
        save_credits(credits)
        return True
    return False

def add_credits(user_id, amount):
    credits = load_credits()
    user_str_id = str(user_id)
    credits[user_str_id] = credits.get(user_str_id, DEFAULT_CREDITS) + amount  # Ensure default credits
    save_credits(credits)

# Formatting function for responses
def format_card_response(cc, result, card_info, country, bank, response_time):
    return (f"✅ **Approved!**\n"
            f"💳 **CC:** `{cc}`\n\n"
            f"🎉 **Response:** {result}\n"
            f"ℹ **Info:** {card_info}\n"
            f"🌍 **Country:** {country}\n"
            f"🏦 **Bank:** {bank}\n"
            f"⏳ **Time:** {response_time}s")

# Command to Check a Single Credit Card using Braintree
@bot.message_handler(commands=["b3"])
def check_card_braintree(message):
    user_id = message.chat.id
    if not deduct_credits(user_id):
        bot.reply_to(message, "🚫 Insufficient credits! Purchase more to continue.")
        return

    try:
        cc_input = message.text.split(maxsplit=1)[1].strip()
        if not re.match(r'\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}', cc_input):
            bot.reply_to(message, "❌ Invalid CC format. Use: `/b3 cc|mm|yy|cvv`")
            return

        checking_msg = bot.reply_to(message, "🔍 Checking Card via Braintree... Please wait.")
        result = asyncio.run(run_checker([cc_input]))[0]

        # Mock response details (replace with actual parsed data)
        card_info = "516989 - CREDIT - MASTERCARD"
        country = "INDIA 🇮🇳"
        bank = "BANK OF INDIA"
        response_time = "7.0"

        formatted_response = format_card_response(cc_input, "Thank You For Donation 🎉", card_info, country, bank, response_time)
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=checking_msg.message_id, text=formatted_response)

    except IndexError:
        bot.reply_to(message, "❌ Please provide a card in the format: `/b3 cc|mm|yy|cvv`")

# Command to Check a Single Credit Card using Stripe
@bot.message_handler(commands=["s3"])
def check_card_stripe(message):
    user_id = message.chat.id
    if not deduct_credits(user_id):
        bot.reply_to(message, "🚫 Insufficient credits! Purchase more to continue.")
        return

    processing_msg = bot.reply_to(message, "🔍 Checking Card via Stripe... Please wait.")
    result = asyncio.run(stripe_payment())

    # Mock response details (replace with actual parsed data)
    card_info = "516989 - CREDIT - MASTERCARD"
    country = "INDIA 🇮🇳"
    bank = "BANK OF INDIA"
    response_time = "7.0"

    formatted_response = format_card_response("XXXX-XXXX-XXXX-XXXX", "Thank You For Donation 🎉", card_info, country, bank, response_time)

    bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=formatted_response)

# Start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.reply_to(message, f"👋 Welcome! You have **{get_user_credits(user_id)}** credits.\n\n"
                          "💳 Use `/b3` to check a card via **Braintree**.\n"
                          "💳 Use `/s3` to check a card via **Stripe**.\n"
                          "💰 Use `/chk` to process a **Braintree** payment.\n"
                          "🎟️ Use `/redeem CODE` to claim free credits.\n"
                          "➕ Admins can use `/addcredits user_id amount` to add credits.")

# Run Bot
print("🚀 Bot is running...")
bot.polling()
