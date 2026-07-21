from dotenv import load_dotenv
from google import genai
import os
import telebot
import requests
import json
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

# ADDING ENKA URL
ENKA_URL = os.environ.get("ENKA_BASE_URL")

#CALLING A DECORATOR FUNCTION TO HANDLE THE /START COMMAND
@bot.message_handler(commands=['start'])
def start_guide(message):
    bot.reply_to(message,'''Use this to search:
/coach <your_uid> <your_showcase_character_name>''')

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
            
            # 2. Safety check: Did they hide their profile in-game?
            if "avatarInfoList" in data:
                #ISOLATING THE AVATAR INFO LIST
                showcase_text = str(data["avatarInfoList"])

                #LOADING THE DICTIONARY
                try:
                    with open("custom_character.json","r") as file:
                        character_dict = json.load(file)
                except FileNotFoundError:
                    bot.reply_to(message,"System error happned try again later!!!")
                for char_id , char_name in character_dict.items():
                    showcase_text = showcase_text.replace(str(char_id), char_name)

                bot.reply_to(message,"Analysing your showcase...")

                #CREATING THE PROMPT FOR GEMINI
                prompt = build_coach_prompt(showcase_text,character)
                #FETCHING THE AI RESPONCE
                ai_responce = client.models.generate_content(model="gemini-3.6-flash",contents= prompt)

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