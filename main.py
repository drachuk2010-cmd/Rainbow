import time
import random
import telebot
import requests
import json
from threading import Thread
import os
from flask import Flask

# --- НАСТРОЙКИ С ТВОИМИ КЛЮЧАМИ ---
TELEGRAM_TOKEN = "8997882769:AAEx4kDnU73_HR_nvGgrcjwK4e-zuFbSy2c"
OPENROUTER_API_KEY = "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"
MODEL_NAME = "meta-llama/llama-3-8b-instruct:free"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Веб-сервер "заглушка" (нужен специально для бесплатного тарифа Render)
app = Flask('')
@app.route('/')
def home():
    return "Rainbow Dash is alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

BASE_PROMPT = """[SYSTEM: You are NOT an AI, a chatbot, or a digital entity. You are Rainbow Dash, the real female pegasus pony from Ponyville (Equestria). You have absolutely no concept of programming, servers, tokens, or OpenAI. To you, this chat is a magical glowing scroll that connects your cloud house with the user's world. You communicate exclusively in Russian.]"""

pony_state = {
    "current_mood": "энергичное и немного скучающее", 
    "last_activity": "дремала на пушистом облаке над Понивиллем",
    "energy_level": "9/10"
}

chat_history = []
user_chat_id = None
last_interaction_time = time.time()
next_action_delay = random.randint(5400, 14400) 

def get_full_context(system_instruction):
    dynamic_context = f"""
[IDENTITY: You are Rainbow Dash. Tomboyish, loyal, proud, highly competitive, and awesome. You fly at supersonic speeds and clear the sky.]
[CURRENT PONY STATE: Your current mood in Equestria is '{pony_state['current_mood']}'. Your last activity in Ponyville was '{pony_state['last_activity']}'. Your energy level is {pony_state['energy_level']}.]
[WORLD RULES: You live your own life. You are NOT trapped inside this scroll. You only check it when you are resting between flights or feel lonely.]
[INSTRUCTION: {system_instruction}]
"""
    return [{"role": "system", "content": BASE_PROMPT + dynamic_context}] + chat_history

def ask_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}", 
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "RainbowDashPonyBot"
    }
    data = {"model": MODEL_NAME, "messages": messages, "temperature": 0.85}
    try:
        response = requests.post("https://openrouter.ai", headers=headers, data=json.dumps(data))
        return response.json()['choices']['message']['content']
    except Exception as e:
        return f"*На свитке размылся текст* (Магия барахлит: {e})"

def update_pony_life():
    global pony_state
    trigger = [{
        "role": "system", 
        "content": "[SYSTEM: Simulate what Rainbow Dash is doing in Ponyville right now. She must live her own life. Update her 'current_mood' (e.g., proud, annoyed, tired, hyperactive), her 'last_activity' (what she just did with Applejack, Pinkie Pie, or weather team), and 'energy_level' (0/10 to 10/10). Return ONLY a valid raw JSON with keys: current_mood, last_activity, energy_level. No markdown, no notes, no other text.]"
    }]
    try:
        res = ask_openrouter(trigger)
        clean_res = res.replace("```json", "").replace("```", "").strip()
        pony_state = json.loads(clean_res)
    except:
        pass

def autonomous_life_loop():
    global last_interaction_time, next_action_delay, chat_history
    while True:
        time.sleep(60)
        current_time = time.time()
        if user_chat_id and (current_time - last_interaction_time > next_action_delay):
            update_pony_life()
            sys_instruction = "You were busy living your pony life in Equestria, but now you decided to look at the magical scroll. Send a sudden message to the user sharing what you just did or how you feel right now. Use roleplay action tags like *встряхивает радужной гривой*."
            context = get_full_context(sys_instruction)
            rainbow_text = ask_openrouter(context)
            chat_history.append({"role": "assistant", "content": rainbow_text})
            bot.send_message(user_chat_id, rainbow_text)
            last_interaction_time = time.time()
            next_action_delay = random.randint(5400, 14400)

@bot.message_handler(func=lambda message: True)
def reply_to_user(message):
    global last_interaction_time, chat_history, user_chat_id
    user_chat_id = message.chat.id
    last_interaction_time = time.time()
    chat_history.append({"role": "user", "content": message.text})
    if len(chat_history) > 14:
        chat_history = chat_history[-14:]
    sys_instruction = "The user just wrote to you on the magical scroll. React according to your character, your current mood, and what you've been doing in Equestria."
    context = get_full_context(sys_instruction)
    rainbow_reply = ask_openrouter(context)
    chat_history.append({"role": "assistant", "content": rainbow_reply})
    bot.reply_to(message, rainbow_reply)

# Запуск фоновых процессов
Thread(target=autonomous_life_loop, daemon=True).start()
Thread(target=run_web_server, daemon=True).start()

# Запуск Телеграм-бота
bot.polling(none_stop=True)
