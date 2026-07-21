from dotenv import load_dotenv
from google import genai
import os
import telebot
import requests
# 1. IMPORT CUSTOM FUNCTION
from prompts import build_coach_prompt

#LOAD ENVIRONMENT VARIABLES
load_dotenv()

#PULLING TELEGRAM TOKEN FROM ENVIRONMENT VARIABLES
bot_token = os.environ.get("TELEGRAM_TOKEN")

#INITIALIZING TELEGRAM BOT
bot = telebot.TeleBot(bot_token)

#PULLING GEMINI TOKEN FROM ENVIROMENT VARIABLES
gemini_token = os.environ.get("GEMINI_TOKEN")

#INITIALIZING GEMINI CLIENT
client = genai.Client(api_key=gemini_token)

#BASE URL
BASE_URL = os.environ.get("GENSHIN_URL")
# ADDING ENKA URL
ENKA_URL = os.environ.get("ENKA_BASE_URL")

#CALLING A DECORATOR FUNCTION TO HANDLE THE /GENSHIN COMMAND
@bot.message_handler(commands=['genshin'])
def get_character(message):
    try:
        #SLICE THE TEXT
        text_part = message.text.split()

        #SAFETY CHECK: DID THEY FORGET THE CHARACTER NAME
        if len(text_part) < 2:
            bot.reply_to(message,"Please provide a character name! Example: /genshin amber")
            return
        character_name = text_part[1].lower()

        #CREATING THE URL FOR FETCHING THE USER REQUEST
        url = f"{BASE_URL}/characters/{character_name}"
        #FETCHING REQUEST
        response = requests.get(url)

        #CHECKING IF THE RESPONCE IS SUCCESS
        if response.status_code == 200:
            #UNPAKING THE DATA INTO READABLE FORMAT
            data = response.json()
            name = data.get("name")
            weapon = data.get("weapon")
            element = data.get("vision")
            rarity = data.get("rarity")
        else:
            bot.reply_to(message, "Character not found. Check your spelling!")
        
        reply_text = (
                f"🌟 Character: {name}\n"
                f"⚔️ Weapon: {weapon}\n"
                f"🔮 Element: {element}\n"
                f"⭐ Rarity: {rarity}-Star"
            )
        bot.reply_to(message,reply_text)
        
    except Exception as e:
        # 1. Print the exact error in your terminal so YOU can debug it
        print(f"Error fetching data: {e}")
        
        # 2. Send a polite apology to the user in Telegram
        bot.reply_to(message, "Oops! The Genshin database is currently unreachable. Please try again later.")

#CALLING A DECORATOR FUNCTION TO HANDLE THE /COACH COMMAND
@bot.message_handler(commands=['coach'])
def get_coach_data(message):
    try:
        #SLICE THE TEXT
        text_part = message.text.split()

        #SAFETY CHECK: DID THEY FORGET THE CHARACTER NAME
        if len(text_part) < 3:
            bot.reply_to(message, "Please provide your Genshin UID! Example: /coach 812345678 character_name")
            return
        uid = text_part[1].lower()
        character = " ".join(text_part[2:]).lower()

        #CREATING THE URL FOR FETCHING THE USER REQUEST
        url = f"{ENKA_URL}/{uid}"

        #SETTING HEADER FOR FETCHING REQUESTED DATA
        headeres = {"User-Agent": "MyTelegramCoachBot/1.0"}

        #FETCHING THE REQUEST
        responce = requests.get(url,headers=headeres)
        
        if responce.status_code == 200:
            data = responce.json()
            
            # 1. Print to your terminal so YOU can see the real Enka structure
            print("--- ENKA DATA RECEIVED ---")
            print(f"Main Categories: {data.keys()}")
            
            # 2. Safety check: Did they hide their profile in-game?
            if "avatarInfoList" in data:
                #ISOLATING THE AVATAR INFO LIST
                showcase_data = data["avatarInfoList"]
                #
                bot.reply_to(message,"Analyzint your showcase...")

                #CREATING THE PROMPT FOR GEMINI
                prompt = build_coach_prompt(showcase_data,character)

                #FETCHING THE AI RESPONCE
                ai_responce = client.models.generate_content(model="gemini-3.5-flash",contents= prompt)

                #SENDING THE AI RESPONCE TO THE TELEGRAM FOR OUTPUT
                bot.reply_to(message,ai_responce.text,parse_mode='HTML')
            else:
                bot.reply_to(message, "Your profile is private! Please turn on 'Show Character Details' in-game.")
        else:
            bot.reply_to(message, "Could not find that UID. Please check and try again!")

    except Exception as e:
        # 1. Print the exact error in your terminal so YOU can debug it
        print(f"Error fetching data: {e}")
        
        # 2. Send a polite apology to the user in Telegram
        bot.reply_to(message, "Oops! The Genshin database is currently unreachable. Please try again later.")

#KEEPING BOT RUNNING
print("Bot is running...")
bot.infinity_polling()