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
TOKEN = '8099253215:AAHJuwiaNNujUVN6sefQslaTrmi3NCPxI8E'  # Replace with actual bot token
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
ALLOWED_USERS = ['7297683223']  # List of allowed user IDs (Admins)
CREDIT_FILE = 'user_credits.json'  # Credit System File

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
    return credits.get(str(user_id), 0)

def add_credits(user_id, amount):
    credits = load_credits()
    user_str_id = str(user_id)
    credits[user_str_id] = credits.get(user_str_id, 0) + amount
    save_credits(credits)

# Command to Add Credits (Admin Only)
@bot.message_handler(commands=["addcredits"])
def add_credits_command(message):
    user_id = message.chat.id
    if str(user_id) not in ALLOWED_USERS:
        bot.reply_to(message, "🚫 You don't have permission to add credits.")
        return

    try:
        _, target_user, amount = message.text.split()
        amount = int(amount)
    except (ValueError, IndexError):
        bot.reply_to(message, "❌ Usage: `/addcredits user_id amount`")
        return

    add_credits(target_user, amount)
    bot.reply_to(message, f"✅ Added {amount} credits to user {target_user}. New Balance: **{get_user_credits(target_user)}**")

# Command to Redeem a Code for Credits
@bot.message_handler(commands=["redeem"])
def redeem_code(message):
    user_id = message.chat.id
    try:
        code = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "❌ Please provide a valid redeem code: `/redeem CODE`")
        return

    if code == "FREE100":  # Example fixed redeem code
        add_credits(user_id, 100)
        bot.reply_to(message, f"✅ Redeemed 100 credits! Your new balance: **{get_user_credits(user_id)}**")
    else:
        bot.reply_to(message, "❌ Invalid redeem code. Try again.")

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
