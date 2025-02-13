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
TOKEN = '8099253215:AAFRFcoh5qnuXXtVPq8O3CN6OsO9ibC73kY'  # Replace with actual bot token
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
        braintree_response = asyncio.run(run_checker([cc_input]))[0]

        # Parsing Braintree response
        try:
            braintree_data = json.loads(braintree_response)
            success = braintree_data.get("success", False)
            message_text = braintree_data.get("message", "Transaction Failed ❌")

            if success:
                formatted_response = f"✅ **Braintree Payment Successful!**\n💳 **CC:** `{cc_input}`\n🎉 **Response:** {message_text}"
            else:
                formatted_response = "❌ **Braintree Payment Failed!**"

        except json.JSONDecodeError:
            formatted_response = "❌ **Error processing Braintree response!**"

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
    stripe_response = asyncio.run(stripe_payment())

    # Parsing Stripe response
    try:
        stripe_data = json.loads(stripe_response)
        success = stripe_data.get("success", False)
        message_text = stripe_data.get("message", "Transaction Failed ❌")

        if success:
            formatted_response = f"✅ **Stripe Payment Successful!**\n🎉 **Response:** {message_text}"
        else:
            formatted_response = "❌ **Stripe Payment Failed!**"

    except json.JSONDecodeError:
        formatted_response = "❌ **Error processing Stripe response!**"

    bot.edit_message_text(chat_id=message.chat.id, message_id=processing_msg.message_id, text=formatted_response)

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
