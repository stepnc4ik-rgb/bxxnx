"""
🎓 Бот-репетитор по всем предметам (OpenRouter)
"""

import telebot
import requests
import json
import os
import base64
from datetime import date

# ============================================================
# 🔑 КЛЮЧИ
# ============================================================
TG_TOKEN = os.environ.get("TG_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
FREE_LIMIT = 10
PAID_PRICE = "299 руб"
ADMIN_ID = 908695451
MODEL = "qwen/qwen3-235b-a22b:free"

# ============================================================
# 📚 ПРЕДМЕТЫ
# ============================================================
SUBJECTS = {
    "math": "📐 Математика",
    "physics": "⚡ Физика",
    "chemistry": "🧪 Химия",
    "biology": "🌿 Биология",
    "history": "📜 История",
    "geography": "🌍 География",
    "russian": "📝 Русский язык",
    "english": "🇬🇧 Английский язык",
    "social": "🏛️ Обществознание",
    "informatics": "💻 Информатика",
}

SUBJECT_PROMPTS = {
    "math": "Ты опытный репетитор по математике. Объясняй решения пошагово, используй формулы и примеры.",
    "physics": "Ты репетитор по физике. Объясняй законы и формулы простым языком, приводи примеры из жизни.",
    "chemistry": "Ты репетитор по химии. Объясняй реакции, формулы и свойства веществ доступно.",
    "biology": "Ты репетитор по биологии. Объясняй процессы и термины простым языком.",
    "history": "Ты репетитор по истории. Отвечай точно, указывай даты и причинно-следственные связи.",
    "geography": "Ты репетитор по географии. Объясняй географические процессы и номенклатуру.",
    "russian": "Ты репетитор по русскому языку. Объясняй правила с примерами.",
    "english": "Ты репетитор по английскому языку. Объясняй грамматику на русском, помогай с переводами.",
    "social": "Ты репетитор по обществознанию. Объясняй понятия и законы, помогай с ЕГЭ.",
    "informatics": "Ты репетитор по информатике. Объясняй алгоритмы и программирование.",
}

# ============================================================
# 💾 БАЗА ДАННЫХ
# ============================================================
DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "questions_today": 0,
            "last_date": str(date.today()),
            "is_premium": False,
            "subject": None,
        }
        save_db(db)
    user = db[uid]
    if user["last_date"] != str(date.today()):
        user["questions_today"] = 0
        user["last_date"] = str(date.today())
        save_db(db)
    return user

def update_user(user_id, data):
    db = load_db()
    uid = str(user_id)
    db[uid].update(data)
    save_db(db)

# ============================================================
# 🤖 ФУНКЦИЯ ЗАПРОСА К AI
# ============================================================
def ask_ai(system_prompt, user_message):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
    )
    data = response.json()
    print(f"OpenRouter response: {data}")
    if "choices" not in data:
        raise Exception(f"OpenRouter error: {data}")
    return data["choices"][0]["message"]["content"]

# ============================================================
# 🤖 ИНИЦИАЛИЗАЦИЯ
# ============================================================
bot = telebot.TeleBot(TG_TOKEN)

# ============================================================
# 📋 КЛАВИАТУРЫ
# ============================================================
def subjects_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [telebot.types.KeyboardButton(name) for name in SUBJECTS.values()]
    markup.add(*buttons)
    markup.add(telebot.types.KeyboardButton("📊 Мой статус"))
    markup.add(telebot.types.KeyboardButton("💳 Купить подписку"))
    return markup

def back_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🔙 Выбрать предмет"))
    markup.add(telebot.types.KeyboardButton("📊 Мой статус"))
    return markup

# ============================================================
# 📩 КОМАНДЫ
# ============================================================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    get_user(user_id)
    name = message.from_user.first_name or "друг"
    text = (
        f"👋 Привет, {name}!\n\n"
        f"Я твой личный репетитор по всем школьным предметам 🎓\n\n"
        f"📚 Помогу с:\n"
        f"• Объяснением тем и правил\n"
        f"• Решением задач пошагово\n"
        f"• Подготовкой к ЕГЭ/ОГЭ\n"
        f"• Домашними заданиями\n"
        f"• 📷 Фото задач!\n\n"
        f"🆓 Бесплатно: {FREE_LIMIT} вопросов в день\n"
        f"⭐ Премиум: безлимит за {PAID_PRICE}/мес\n\n"
        f"Выбери предмет 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=subjects_keyboard())

# ============================================================
# 📊 СТАТУС
# ============================================================
def show_status(message):
    user = get_user(message.from_user.id)
    remaining = FREE_LIMIT - user["questions_today"]
    subject = user.get("subject")
    subject_name = SUBJECTS.get(subject, "не выбран")
    if user["is_premium"]:
        limit_text = "⭐ Премиум — безлимитные вопросы"
    else:
        limit_text = f"🆓 Осталось сегодня: {max(0, remaining)} из {FREE_LIMIT}"
    text = (
        f"📊 Твой статус:\n\n"
        f"{limit_text}\n"
        f"📚 Текущий предмет: {subject_name}\n"
        f"📅 Лимит обновляется каждый день в полночь"
    )
    bot.send_message(message.chat.id, text)

# ============================================================
# 💬 СООБЩЕНИЯ
# ============================================================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text
    user_id = message.from_user.id
    user = get_user(user_id)

    if text == "📊 Мой статус":
        show_status(message)
        return

    if text == "💳 Купить подписку":
        buy_subscription(message)
        return

    if text == "🔙 Выбрать предмет":
        update_user(user_id, {"subject": None})
        bot.send_message(message.chat.id, "Выбери предмет 👇", reply_markup=subjects_keyboard())
        return

    subject_key = None
    for key, name in SUBJECTS.items():
        if text == name:
            subject_key = key
            break

    if subject_key:
        update_user(user_id, {"subject": subject_key})
        bot.send_message(
            message.chat.id,
            f"Отлично! Выбран предмет: {SUBJECTS[subject_key]}\n\nЗадавай свой вопрос! 💬",
            reply_markup=back_keyboard()
        )
        return

    subject = user.get("subject")
    if not subject:
        bot.send_message(message.chat.id, "Сначала выбери предмет 👇", reply_markup=subjects_keyboard())
        return

    if not user["is_premium"] and user["questions_today"] >= FREE_LIMIT:
        bot.send_message(
            message.chat.id,
            f"❌ Исчерпан дневной лимит ({FREE_LIMIT} вопросов)\n\n"
            f"⭐ Купи премиум за {PAID_PRICE}/мес!\n\nНажми 💳 Купить подписку"
        )
        return

    bot.send_chat_action(message.chat.id, "typing")

    try:
        system_prompt = SUBJECT_PROMPTS[subject] + "\n\nОтвечай на русском языке. Будь дружелюбным и понятным для школьника. Используй эмодзи."
        answer = ask_ai(system_prompt, text)

        update_user(user_id, {"questions_today": user["questions_today"] + 1})
        user = get_user(user_id)

        if not user["is_premium"]:
            remaining = FREE_LIMIT - user["questions_today"]
            answer += f"\n\n─────────────────\n🆓 Осталось вопросов сегодня: {remaining}"

        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуй ещё раз через минуту.")
        print(f"Ошибка: {e}")

# ============================================================
# 📷 ФОТО
# ============================================================
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    subject = user.get("subject")
    if not subject:
        bot.send_message(message.chat.id, "Сначала выбери предмет 👇", reply_markup=subjects_keyboard())
        return

    if not user["is_premium"] and user["questions_today"] >= FREE_LIMIT:
        bot.send_message(message.chat.id, f"❌ Исчерпан лимит. Купи премиум!\nНажми 💳 Купить подписку")
        return

    bot.send_chat_action(message.chat.id, "typing")
    bot.send_message(message.chat.id, "📷 Анализирую фото...")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_base64 = base64.b64encode(downloaded).decode("utf-8")
        caption = message.caption or "Реши или объясни задание на фото."

        system_prompt = SUBJECT_PROMPTS[subject] + "\n\nОтвечай на русском языке. Будь дружелюбным. Используй эмодзи."

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.2-11b-vision-instruct:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": caption},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                    ]}
                ]
            }
        )
        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        update_user(user_id, {"questions_today": user["questions_today"] + 1})
        user = get_user(user_id)

        if not user["is_premium"]:
            remaining = FREE_LIMIT - user["questions_today"]
            answer += f"\n\n─────────────────\n🆓 Осталось вопросов сегодня: {remaining}"

        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Не удалось обработать фото. Попробуй ещё раз.")
        print(f"Ошибка фото: {e}")

# ============================================================
# 💳 ПОДПИСКА
# ============================================================
def buy_subscription(message):
    text = (
        f"⭐ Премиум подписка — {PAID_PRICE}/мес\n\n"
        f"✅ Безлимитные вопросы\n"
        f"✅ Все 10 предметов\n"
        f"✅ Фото задач\n\n"
        f"Для оплаты: @k0rion\n\n"
        f"Доступ активируется в течение 5 минут."
    )
    bot.send_message(message.chat.id, text)
    try:
        bot.send_message(ADMIN_ID, f"💳 Хочет подписку!\nID: {message.from_user.id}\nИмя: {message.from_user.first_name}\n@{message.from_user.username}")
    except:
        pass

# ============================================================
# 🔧 ВЫДАТЬ ПРЕМИУМ
# ============================================================
@bot.message_handler(commands=["premium"])
def give_premium(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = message.text.split()[1]
        update_user(int(target_id), {"is_premium": True})
        bot.send_message(message.chat.id, f"✅ Премиум выдан {target_id}")
        bot.send_message(int(target_id), "🎉 Премиум активирован! Безлимитные вопросы.")
    except:
        bot.send_message(message.chat.id, "Использование: /premium USER_ID")

# ============================================================
# 🚀 ЗАПУСК
# ============================================================
if __name__ == "__main__":
    print("🤖 Бот запущен на OpenRouter!")
    print(f"📚 Предметов: {len(SUBJECTS)}")
    bot.infinity_polling()
