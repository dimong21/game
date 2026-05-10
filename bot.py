import os
import sqlite3
import random
from datetime import datetime, timedelta

import telebot
from telebot import types

# ====================== ТОКЕН ======================
# На BotHost токен берётся из переменной окружения BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    # Если переменной нет — вставь свой токен прямо сюда
    BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"

bot = telebot.TeleBot(BOT_TOKEN)

# ====================== БАЗА ДАННЫХ ======================
DB_NAME = "life_simulator.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            gender TEXT,
            birth_date TEXT,
            country TEXT,
            city TEXT,
            name TEXT,
            age_months INTEGER DEFAULT 0,
            intelligence INTEGER DEFAULT 0,
            health INTEGER DEFAULT 100,
            charisma INTEGER DEFAULT 0,
            luck INTEGER DEFAULT 0,
            money INTEGER DEFAULT 0,
            stress INTEGER DEFAULT 0,
            happiness INTEGER DEFAULT 50,
            reputation INTEGER DEFAULT 50,
            criminal_level INTEGER DEFAULT 0,
            education TEXT DEFAULT '',
            job TEXT DEFAULT '',
            is_alive INTEGER DEFAULT 1,
            game_stage TEXT DEFAULT 'birth'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            npc_name TEXT,
            npc_type TEXT,
            attachment INTEGER DEFAULT 50,
            trust INTEGER DEFAULT 50,
            jealousy INTEGER DEFAULT 0,
            status TEXT DEFAULT 'stranger',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            business_type TEXT,
            name TEXT,
            level INTEGER DEFAULT 1,
            income INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reason TEXT,
            sentence_months INTEGER,
            months_served INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS past_lives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            life_number INTEGER,
            death_age INTEGER,
            money INTEGER,
            reputation INTEGER,
            happiness INTEGER,
            death_reason TEXT,
            life_rank TEXT,
            country TEXT,
            job TEXT,
            children_count INTEGER DEFAULT 0,
            marriages_count INTEGER DEFAULT 0,
            date_ended TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ====================== ВРЕМЕННЫЕ ДАННЫЕ ======================
user_temp = {}

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

def get_countries():
    return [
        ("🇷🇺 Россия", "Russia", "Москва", 5000, 30, 20),
        ("🇺🇸 США", "USA", "Нью-Йорк", 15000, 10, 40),
        ("🇯🇵 Япония", "Japan", "Токио", 10000, 5, 15),
        ("🇧🇷 Бразилия", "Brazil", "Рио-де-Жанейро", 3000, 40, 35),
        ("🇩🇪 Германия", "Germany", "Берлин", 12000, 8, 25),
        ("🇰🇵 КНДР", "North Korea", "Пхеньян", 500, 5, 90),
        ("🇨🇳 Китай", "China", "Пекин", 8000, 15, 30),
        ("🇮🇳 Индия", "India", "Мумбаи", 2000, 25, 50),
        ("🇫🇷 Франция", "France", "Париж", 11000, 12, 20),
        ("🇳🇬 Нигерия", "Nigeria", "Лагос", 1500, 45, 60)
    ]

def get_random_name(gender):
    male_names = ["Александр", "Дмитрий", "Максим", "Иван", "Сергей", "Андрей", "Михаил", "Артём", "Никита", "Даниил"]
    female_names = ["Анна", "Мария", "Елена", "Ольга", "Наталья", "Екатерина", "Ирина", "Татьяна", "Светлана", "Анастасия"]
    return random.choice(male_names if gender == "male" else female_names)

def get_db_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_new_life(user_id, username, first_name, gender, country, city):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    birth_date = datetime.now() - timedelta(days=random.randint(0, 365*18))
    birth_date_str = birth_date.strftime("%d.%m.%Y")

    name = get_random_name(gender)

    cursor.execute('''
        INSERT OR REPLACE INTO users
        (user_id, username, first_name, gender, birth_date, country, city, name,
         age_months, money, happiness, reputation, is_alive, game_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 50, 50, 1, 'baby')
    ''', (user_id, username, first_name, gender, birth_date_str, country, city, name, 0))

    conn.commit()
    conn.close()

def get_age_text(months):
    years = months // 12
    months_rest = months % 12
    if years == 0:
        return f"{months_rest} мес."
    elif years < 3:
        return f"{years} г. {months_rest} мес."
    else:
        return f"{years} лет"

def get_stage_by_age(months):
    years = months // 12
    if years < 3:
        return "baby"
    elif years < 7:
        return "kindergarten"
    elif years < 17:
        return "school"
    elif years < 23:
        return "student"
    elif years < 60:
        return "adult"
    elif years < 75:
        return "elderly"
    else:
        return "old"

def get_life_events(stage, user):
    events = []

    if stage == "baby":
        events = [
            ("🍼 Первые шаги!", "Ты научился ходить! Родители счастливы.", {"happiness": 10}),
            ("🤒 Болезнь", "Ты заболел обычной простудой. Мама лечит тебя.", {"health": -5, "happiness": -5}),
            ("🎁 Подарок", "Бабушка подарила игрушку!", {"happiness": 5, "luck": 3}),
        ]
    elif stage == "kindergarten":
        events = [
            ("👶 Детский сад", "Ты пошёл в детский сад. Новые друзья!", {"charisma": 5, "happiness": 5}),
            ("🤼 Драка", "Подрался с мальчиком за игрушку.", {"health": -3, "reputation": -2}),
            ("🎨 Рисование", "Ты нарисовал красивый рисунок.", {"intelligence": 5, "happiness": 5}),
        ]
    elif stage == "school":
        events = [
            ("📚 Школа", "Очередной учебный месяц. Ты учишься.", {"intelligence": 10, "stress": 5}),
            ("🏀 Спорт", "Ты записался в спортивную секцию!", {"health": 10, "charisma": 5}),
            ("💻 Компьютер", "Родители купили тебе компьютер.", {"intelligence": 15, "happiness": 10}),
            ("🚬 Плохая компания", "Ты попал в плохую компанию.", {"criminal_level": 10, "reputation": -10, "stress": 10}),
            ("❤️ Первая любовь", "Ты влюбился в одноклассника!", {"happiness": 20, "stress": -10}),
        ]
    elif stage == "student":
        events = [
            ("🎓 Универ", "Ты поступил в университет!", {"intelligence": 20, "money": -2000, "happiness": 10}),
            ("💼 Подработка", "Нашёл подработку.", {"money": random.randint(500, 2000), "stress": 10}),
            ("🍺 Вечеринка", "Сходил на вечеринку. Было весело!", {"happiness": 15, "charisma": 10, "health": -5}),
        ]
    elif stage == "adult":
        events = [
            ("💼 Работа", "Рабочий месяц. Карьерный рост!", {"money": random.randint(1000, 10000), "stress": 15, "intelligence": 5}),
            ("💰 Бизнес идея", "У тебя появилась идея для бизнеса!", {}),
            ("❤️ Свидание", "Ты пошёл на свидание. Всё прошло отлично!", {"happiness": 20, "charisma": 5}),
            ("🤒 Болезнь", "Ты заболел. Нужно лечиться.", {"health": -20, "money": -3000, "stress": 20}),
            ("🚔 Проблемы с законом", "Тебя задержала полиция!", {"criminal_level": 15, "reputation": -20, "stress": 30}),
            ("🎰 Лотерея", "Ты выиграл в лотерею!", {"money": random.randint(5000, 50000), "luck": 10, "happiness": 30}),
        ]
    elif stage == "elderly":
        events = [
            ("👴 Пенсия", "Ты вышел на пенсию.", {"money": 500, "happiness": 5, "stress": -20}),
            ("👨‍👩‍👧‍👦 Внуки", "Ты стал дедушкой/бабушкой!", {"happiness": 30}),
            ("🏥 Больница", "Проблемы со здоровьем.", {"health": -20, "money": -5000, "stress": 20}),
        ]
    elif stage == "old":
        events = [
            ("🧓 Старость", "Годы берут своё...", {"health": -10, "happiness": -5}),
            ("💀 Смерть близко", "Ты чувствуешь приближение смерти...", {"stress": 30, "happiness": -20}),
        ]

    if not events:
        return [("⏳ Жизнь идёт", "Обычный месяц. Ничего особенного.", {})]
    return events

def apply_effects(user_id, effects):
    if not effects:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for stat, delta in effects.items():
        stat_map = {
            "intelligence": "intelligence", "health": "health", "charisma": "charisma",
            "luck": "luck", "money": "money", "stress": "stress",
            "happiness": "happiness", "reputation": "reputation", "criminal_level": "criminal_level"
        }
        col = stat_map.get(stat)
        if col:
            cursor.execute(f"UPDATE users SET {col} = MAX(0, MIN(100, {col} + ?)) WHERE user_id = ?", (delta, user_id))
    conn.commit()
    conn.close()

def check_death(user):
    years = user["age_months"] // 12
    health = user["health"]

    if years >= 90:
        return True, "Естественная смерть от старости"
    if health <= 0:
        return True, "Смерть от болезни"
    if user["stress"] >= 100 and random.random() < 0.1:
        return True, "Сердечный приступ из-за стресса"
    if years >= 70 and health < 20:
        return True, "Осложнения от болезней"
    if random.random() < 0.001:
        return True, "Несчастный случай"
    return False, None

def end_life(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    death_age = user["age_months"] // 12

    if user["health"] <= 0:
        death_reason = "Болезнь"
    elif death_age >= 90:
        death_reason = "Старость"
    elif user["stress"] >= 100:
        death_reason = "Стресс"
    else:
        death_reason = random.choice(["Несчастный случай", "Сердечный приступ", "Авария"])

    score = (user["money"] / 1000 + user["happiness"] * 2 + user["reputation"] * 2 + user["intelligence"]) / 10
    if score >= 90:
        rank = "S"
    elif score >= 75:
        rank = "A"
    elif score >= 60:
        rank = "B"
    elif score >= 45:
        rank = "C"
    elif score >= 30:
        rank = "D"
    elif score >= 15:
        rank = "E"
    else:
        rank = "F"

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE user_id = ? AND npc_type = 'child'", (user["user_id"],))
    children = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE user_id = ? AND status = 'married'", (user["user_id"],))
    marriages = cursor.fetchone()[0]

    life_count = cursor.execute("SELECT COUNT(*) FROM past_lives WHERE user_id = ?", (user["user_id"],)).fetchone()[0]
    cursor.execute('''
        INSERT INTO past_lives (user_id, life_number, death_age, money, reputation, happiness,
                               death_reason, life_rank, country, job, children_count, marriages_count, date_ended)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user["user_id"], life_count + 1, death_age, user["money"], user["reputation"],
          user["happiness"], death_reason, rank, user["country"], user["job"],
          children, marriages, datetime.now().strftime("%d.%m.%Y")))

    cursor.execute("DELETE FROM relationships WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM businesses WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM jail WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user["user_id"],))

    conn.commit()
    conn.close()

    return death_age, death_reason, rank, int(score)

def get_profile_text(user):
    age_text = get_age_text(user["age_months"])
    return f"""
👤 *{user['name']}*
📅 {user['birth_date']} | {age_text}
📍 {user['country']}, {user['city']}
🎓 Образование: {user['education'] or 'Нет'}
💼 Работа: {user['job'] or 'Безработный'}

🧠 Интеллект: {user['intelligence']}
💪 Здоровье: {user['health']}
😎 Харизма: {user['charisma']}
🍀 Удача: {user['luck']}
💰 Деньги: {user['money']:,} ₽
😵 Стресс: {user['stress']}
❤️ Счастье: {user['happiness']}
🔥 Репутация: {user['reputation']}
🚔 Криминал: {user['criminal_level']}
"""

# ====================== КЛАВИАТУРЫ ======================

def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Продолжить жизнь", callback_data="continue_life"),
        types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"),
        types.InlineKeyboardButton("❤️ Отношения", callback_data="relationships"),
        types.InlineKeyboardButton("💰 Бизнес", callback_data="business"),
        types.InlineKeyboardButton("🚔 Тюрьма", callback_data="jail_status"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏆 Топ игроков", callback_data="top_players"),
        types.InlineKeyboardButton("📜 Прошлые жизни", callback_data="past_lives"),
        types.InlineKeyboardButton("❌ Выход", callback_data="exit_game")
    )
    return keyboard

def gender_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
        types.InlineKeyboardButton("👩 Женский", callback_data="gender_female")
    )
    return keyboard

def country_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for display_name, country_code, _, _, _, _ in get_countries():
        keyboard.add(types.InlineKeyboardButton(display_name, callback_data=f"country_{country_code}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайная страна", callback_data="country_random"))
    return keyboard

def life_actions_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Следующий месяц", callback_data="next_month"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

def event_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("▶️ Продолжить", callback_data="next_month"))
    keyboard.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return keyboard

# ====================== ОБРАБОТЧИКИ КОМАНД ======================

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "player"
    first_name = message.from_user.first_name or "Игрок"

    user = get_db_user(user_id)

    if user and user["is_alive"] == 1:
        bot.send_message(
            user_id,
            f"👋 С возвращением, {user['name']}! Жизнь продолжается.",
            reply_markup=main_menu_keyboard()
        )
    else:
        bot.send_message(
            user_id,
            "🌟 *Добро пожаловать в Life Simulator!*\n\n"
            "Проживи жизнь от рождения до смерти.\n"
            "Каждое решение меняет твою судьбу!\n\n"
            "*Выбери пол:*",
            parse_mode="Markdown",
            reply_markup=gender_keyboard()
        )

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    user = get_db_user(message.from_user.id)
    if user and user["is_alive"] == 1:
        bot.send_message(
            message.from_user.id,
            "Действие отменено. Возвращаемся в главное меню.",
            reply_markup=main_menu_keyboard()
        )
    else:
        start_command(message)

# ====================== CALLBACK ОБРАБОТЧИКИ ======================

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def choose_gender(call):
    user_id = call.from_user.id
    gender = call.data.split("_")[1]

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🌍 *Выбери страну рождения:*",
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=country_keyboard()
    )

    user_temp[user_id] = {"gender": gender}

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def choose_country(call):
    user_id = call.from_user.id
    country_code = call.data.split("_")[1]

    if user_id not in user_temp:
        bot.answer_callback_query(call.id, "Ошибка! Начни заново: /start")
        return

    gender = user_temp[user_id]["gender"]

    if country_code == "random":
        display_name, country_code, city, money, crim, luck = random.choice(get_countries())
    else:
        for dn, cc, c, m, cr, l in get_countries():
            if cc == country_code:
                display_name, city, money, crim, luck = dn, c, m, cr, l
                break
        else:
            display_name, city, money, crim, luck = "Россия", "Москва", 5000, 30, 20

    create_new_life(user_id, call.from_user.username, call.from_user.first_name, gender, display_name, city)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET money = ? WHERE user_id = ?", (money, user_id))
    conn.commit()
    conn.close()

    user = get_db_user(user_id)

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"🎉 *Рождение!*\n\n"
        f"👶 Родился {user['name']}\n"
        f"📅 {user['birth_date']}\n"
        f"📍 {display_name}, {city}\n\n"
        f"Начинается твоя история...",
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=life_actions_keyboard()
    )

    if user_id in user_temp:
        del user_temp[user_id]

@bot.callback_query_handler(func=lambda call: call.data == "continue_life")
def continue_life(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни. Начни новую!")
        return

    bot.edit_message_text(
        get_profile_text(user),
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=life_actions_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "next_month")
def next_month(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        bot.edit_message_text("Начни новую жизнь: /start", user_id, call.message.message_id)
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age_months = age_months + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    user = get_db_user(user_id)
    stage = get_stage_by_age(user["age_months"])
    events = get_life_events(stage, user)
    event = random.choice(events)

    title, description, effects = event
    apply_effects(user_id, effects)

    user_after = get_db_user(user_id)
    is_dead, death_reason = check_death(user_after)

    age_text = get_age_text(user_after["age_months"])

    if is_dead or user_after["health"] <= 10:
        death_age, death_reason, rank, score = end_life(user_after)
        bot.edit_message_text(
            f"💀 *Ты умер!*\n\n"
            f"Возраст: {death_age} лет\n"
            f"Причина: {death_reason}\n"
            f"Деньги: {user_after['money']:,} ₽\n"
            f"Рейтинг жизни: *{rank}* ({score}/100)\n\n"
            f"Начни новую жизнь!",
            user_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return

    text = f"📅 *{age_text}* | {title}\n\n{description}\n\n{get_profile_text(user_after)}"
    bot.edit_message_text(
        text,
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=event_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return

    bot.edit_message_text(
        get_profile_text(user),
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def return_to_menu(call):
    user = get_db_user(call.from_user.id)
    if user and user["is_alive"] == 1:
        text = f"🏠 *Главное меню*\n\n{get_profile_text(user)}"
    else:
        text = "🏠 *Главное меню*\n\nНачни новую жизнь!"

    bot.edit_message_text(
        text,
        call.from_user.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "past_lives")
def show_past_lives(call):
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_lives WHERE user_id = ? ORDER BY life_number DESC LIMIT 5", (user_id,))
    lives = cursor.fetchall()
    conn.close()

    if not lives:
        bot.answer_callback_query(call.id, "У тебя ещё нет прошлых жизней!")
        return

    text = "📜 *Твои прошлые жизни:*\n\n"
    for life in lives:
        text += f"Жизнь #{life['life_number']} | {life['country']}\n"
        text += f"Возраст: {life['death_age']} лет\n"
        text += f"Причина: {life['death_reason']}\n"
        text += f"Рейтинг: *{life['life_rank']}*\n"
        text += f"💰 {life['money']:,} ₽ | ❤️ {life['happiness']}\n\n"

    bot.edit_message_text(
        text,
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "top_players")
def top_players(call):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, SUM(money) as total_money, COUNT(*) as lives_count,
               AVG(happiness) as avg_happiness
        FROM past_lives
        GROUP BY user_id
        ORDER BY total_money DESC
        LIMIT 10
    ''')
    top = cursor.fetchall()
    conn.close()

    if not top:
        text = "🏆 Пока никто не завершил жизнь! Стань первым!"
    else:
        text = "🏆 *Топ игроков:*\n\n"
        for i, row in enumerate(top, 1):
            text += f"{i}. ID:{row['user_id']} - 💰 {row['total_money']:,} ₽ ({row['lives_count']} жизней)\n"

    bot.edit_message_text(
        text,
        call.from_user.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "new_life")
def new_life_button(call):
    user = get_db_user(call.from_user.id)
    if user and user["is_alive"] == 1:
        end_life(user)

    bot.edit_message_text(
        "🌟 *Новая жизнь!*\n\nВыбери пол:",
        call.from_user.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=gender_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "relationships")
def relationships_menu(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM relationships WHERE user_id = ?", (user_id,))
    rels = cursor.fetchall()
    conn.close()

    if not rels:
        text = "❤️ *Отношения*\n\nУ тебя пока нет отношений. Живи дальше!"
    else:
        text = f"❤️ *Твои отношения:*\n\n"
        for r in rels:
            text += f"{r['npc_name']} ({r['npc_type']})\n"
            text += f"Статус: {r['status']} | Привязанность: {r['attachment']}%\n"
            text += f"Доверие: {r['trust']}% | Ревность: {r['jealousy']}%\n\n"

    bot.edit_message_text(
        text,
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "business")
def business_menu(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE user_id = ? AND is_active = 1", (user_id,))
    businesses = cursor.fetchall()
    conn.close()

    if not businesses:
        text = "💰 *Бизнес*\n\nУ тебя нет активного бизнеса.\nПродолжай жить - возможно, появится идея!"
    else:
        text = "💰 *Твои бизнесы:*\n\n"
        for b in businesses:
            text += f"🏢 {b['name']} ({b['business_type']})\n"
            text += f"Уровень: {b['level']} | Доход: {b['income']} ₽/мес\n\n"

    bot.edit_message_text(
        text,
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "jail_status")
def jail_status(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)

    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jail WHERE user_id = ? AND is_active = 1", (user_id,))
    active_jail = cursor.fetchone()
    conn.close()

    if active_jail:
        text = f"🚔 *Ты в тюрьме!*\n\n"
        text += f"Причина: {active_jail['reason']}\n"
        text += f"Срок: {active_jail['sentence_months']} мес.\n"
        text += f"Отбыто: {active_jail['months_served']} мес.\n"
        text += f"Осталось: {active_jail['sentence_months'] - active_jail['months_served']} мес.\n"
    else:
        text = "🚔 *Тюрьма*\n\nТы на свободе! Пока что..."

    bot.edit_message_text(
        text,
        user_id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "exit_game")
def exit_game(call):
    bot.edit_message_text(
        "👋 До встречи! Чтобы начать заново, напиши /start",
        call.from_user.id,
        call.message.message_id
    )

# ====================== ЗАПУСК ======================

if __name__ == "__main__":
    print("🤖 Бот Life Simulator запущен!")
    # Удаляем вебхук на всякий случай и используем long polling
    bot.remove_webhook()
    bot.infinity_polling()
