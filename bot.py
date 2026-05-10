import os
import sqlite3
import random
from datetime import datetime, timedelta

import telebot
from telebot import types

# ====================== ТОКЕН ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_СЮДА")
bot = telebot.TeleBot(BOT_TOKEN)

# ====================== БАЗА ДАННЫХ ======================
DB_NAME = "life_simulator.db"

# Удаляем старую БД при запуске, чтобы избежать ошибок со структурой
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print("🔄 Старая база данных удалена")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 29 колонок
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
            nickname TEXT DEFAULT '',
            family_wealth TEXT DEFAULT 'medium',
            age_months INTEGER DEFAULT 0,
            intelligence INTEGER DEFAULT 30,
            health INTEGER DEFAULT 80,
            charisma INTEGER DEFAULT 30,
            luck INTEGER DEFAULT 30,
            money INTEGER DEFAULT 0,
            stress INTEGER DEFAULT 20,
            happiness INTEGER DEFAULT 60,
            reputation INTEGER DEFAULT 50,
            criminal_level INTEGER DEFAULT 0,
            education TEXT DEFAULT '',
            job TEXT DEFAULT '',
            car TEXT DEFAULT '',
            bike TEXT DEFAULT '',
            has_apartment INTEGER DEFAULT 0,
            has_penthouse INTEGER DEFAULT 0,
            is_alive INTEGER DEFAULT 1,
            game_stage TEXT DEFAULT 'baby',
            last_event_date TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_type TEXT,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
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
    print("✅ Новая база данных создана")

init_db()

# ====================== ВРЕМЕННЫЕ ДАННЫЕ ======================
user_temp = {}

# ====================== ТОВАРЫ, ТРАНСПОРТ, ПУТЕШЕСТВИЯ ======================

SHOP_ITEMS = {
    "food": [
        ("🍔 Бургер", 200, {"health": 2, "happiness": 5, "stress": -3}),
        ("🍕 Пицца", 500, {"health": -2, "happiness": 10, "stress": -5}),
        ("🥗 Салат", 300, {"health": 5, "happiness": 2, "stress": -2}),
    ],
    "alcohol": [
        ("🍺 Пиво Baltika 7", 100, {"health": -3, "happiness": 8, "stress": -10}),
        ("🍺 Пиво Heineken", 180, {"health": -2, "happiness": 10, "stress": -8}),
        ("🥃 Виски Jack Daniels", 1500, {"health": -6, "happiness": 18, "stress": -15}),
    ],
    "cigarettes": [
        ("🚬 Winston XStyle", 180, {"health": -5, "stress": -10, "happiness": 3}),
        ("🚬 Marlboro Gold", 220, {"health": -4, "stress": -12, "happiness": 4}),
        ("🚬 Parliament Aqua Blue", 250, {"health": -3, "stress": -13, "happiness": 5}),
    ],
    "vape": [
        ("💨 HQD Cuvie Plus", 600, {"health": -3, "stress": -15, "happiness": 10}),
        ("💨 Elf Bar 1500", 800, {"health": -2, "stress": -18, "happiness": 12}),
        ("💨 Vaporesso XROS", 1500, {"health": -1, "stress": -20, "happiness": 15}),
    ],
    "energy": [
        ("⚡ Red Bull", 150, {"health": -2, "stress": -5, "intelligence": 3}),
        ("⚡ Monster Energy", 180, {"health": -3, "stress": -7, "intelligence": 5}),
    ],
}

TRANSPORT = {
    "bicycles": [
        ("🚲 Stels Navigator", 15000, "Велик"),
        ("🚲 Merida Big Nine", 45000, "Велик"),
        ("🚲 Trek Marlin", 70000, "Велик"),
    ],
    "pitbikes": [
        ("🏍️ Pitbike Kayo 125", 80000, "Питбайк"),
        ("🏍️ Pitbike BSE 140", 110000, "Питбайк"),
        ("🏍️ Pitbike Apollo 160", 150000, "Питбайк"),
    ],
    "motorcycles": [
        ("🏍️ Honda CB500", 400000, "Мотоцикл"),
        ("🏍️ Yamaha R3", 550000, "Мотоцикл"),
        ("🏍️ Kawasaki Ninja 650", 750000, "Мотоцикл"),
        ("🏍️ Harley Sportster", 1200000, "Мотоцикл"),
    ],
    "cars": [
        ("🚗 Lada Granta", 700000, "Машина"),
        ("🚗 Kia Rio", 1200000, "Машина"),
        ("🚗 Toyota Camry", 2500000, "Машина"),
        ("🚗 BMW X5", 6000000, "Машина"),
        ("🚗 Mercedes S-Class", 12000000, "Машина"),
        ("🚗 Porsche 911", 9000000, "Машина"),
        ("🚗 Tesla Model 3", 4500000, "Машина"),
    ],
}

TRAVELS = [
    ("🏡 Поездка в деревню", 5000, {"happiness": 15, "stress": -20, "health": 5}),
    ("🏖️ Отдых на море", 50000, {"happiness": 30, "stress": -30, "health": 10, "charisma": 5}),
    ("🏔️ Поход в горы", 20000, {"happiness": 20, "stress": -25, "health": 15}),
    ("🌆 Пентхаус вечеринка", 100000, {"happiness": 40, "stress": -15, "charisma": 15, "reputation": 10}),
    ("✈️ Путешествие в Европу", 150000, {"happiness": 50, "stress": -40, "charisma": 20, "intelligence": 5}),
]

FAMILY_TYPES = [
    ("💰 Богатая семья", "rich", 500000, 15, 40),
    ("🏠 Средняя семья", "medium", 50000, 5, 20),
    ("🏚️ Бедная семья", "poor", 5000, 0, 5),
    ("🏚️ Неблагополучная семья", "bad", 1000, -5, 30),
]

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

def get_countries():
    return [
        ("🇷🇺 Россия", "Russia", "Москва", 50000, 30),
        ("🇺🇸 США", "USA", "Нью-Йорк", 150000, 10),
        ("🇯🇵 Япония", "Japan", "Токио", 100000, 5),
        ("🇩🇪 Германия", "Germany", "Берлин", 120000, 8),
    ]

def get_db_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

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
    if years < 3: return "baby"
    elif years < 7: return "kindergarten"
    elif years < 17: return "school"
    elif years < 23: return "student"
    elif years < 60: return "adult"
    elif years < 75: return "elderly"
    else: return "old"

def apply_effects(user_id, effects):
    if not effects: return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    changes = []
    for stat, delta in effects.items():
        stat_map = {
            "intelligence": "intelligence", "health": "health", "charisma": "charisma",
            "luck": "luck", "money": "money", "stress": "stress",
            "happiness": "happiness", "reputation": "reputation", "criminal_level": "criminal_level"
        }
        col = stat_map.get(stat)
        if col:
            if col == "money":
                cursor.execute(f"UPDATE users SET {col} = {col} + ? WHERE user_id = ?", (delta, user_id))
            else:
                cursor.execute(f"UPDATE users SET {col} = MAX(0, MIN(100, {col} + ?)) WHERE user_id = ?", (delta, user_id))
            sign = "+" if delta >= 0 else ""
            changes.append(f"{get_stat_emoji(col)} {get_stat_name(col)}: {sign}{delta}")
    conn.commit()
    conn.close()
    return changes

def get_stat_emoji(stat):
    emojis = {"intelligence":"🧠","health":"💪","charisma":"😎","luck":"🍀","money":"💰","stress":"😵","happiness":"❤️","reputation":"🔥","criminal_level":"🚔"}
    return emojis.get(stat, "📊")

def get_stat_name(stat):
    names = {"intelligence":"Интеллект","health":"Здоровье","charisma":"Харизма","luck":"Удача","money":"Деньги","stress":"Стресс","happiness":"Счастье","reputation":"Репутация","criminal_level":"Криминал"}
    return names.get(stat, stat)

def check_death(user):
    years = user["age_months"] // 12
    health = user["health"]
    if years >= 95: return True, "Естественная смерть от старости"
    if health <= 0: return True, "Смерть от болезней"
    if health <= 10 and years >= 70 and random.random() < 0.2: return True, "Осложнения от болезней"
    return False, None

def end_life(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    death_age = user["age_months"] // 12
    death_reason = "Несчастный случай"
    if user["health"] <= 0: death_reason = "Болезнь"
    elif death_age >= 95: death_reason = "Старость"
    
    score = (user["money"] / 1000 + user["happiness"] * 2 + user["reputation"] * 2 + user["intelligence"]) / 10
    rank = "S" if score >= 90 else "A" if score >= 75 else "B" if score >= 60 else "C" if score >= 45 else "D" if score >= 30 else "E" if score >= 15 else "F"
    
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE user_id = ? AND npc_type = 'child'", (user["user_id"],))
    children = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE user_id = ? AND status = 'married'", (user["user_id"],))
    marriages = cursor.fetchone()[0]
    
    life_count = cursor.execute("SELECT COUNT(*) FROM past_lives WHERE user_id = ?", (user["user_id"],)).fetchone()[0]
    cursor.execute('''INSERT INTO past_lives VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (user["user_id"], life_count+1, death_age, user["money"], user["reputation"],
                    user["happiness"], death_reason, rank, user["country"], user["job"],
                    children, marriages, datetime.now().strftime("%d.%m.%Y")))
    
    cursor.execute("DELETE FROM relationships WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM businesses WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM jail WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user["user_id"],))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user["user_id"],))
    conn.commit()
    conn.close()
    return death_age, death_reason, rank, int(score)

def get_profile_text(user):
    age_text = get_age_text(user["age_months"])
    nickname_text = f'\n💬 "{user["nickname"]}"' if user.get("nickname") else ""
    car_text = f"\n🚗 {user['car']}" if user.get('car') else ""
    bike_text = f"\n🏍️ {user['bike']}" if user.get('bike') else ""
    home_text = "\n🏠 Квартира есть" if user.get('has_apartment') else ""
    pent_text = "\n🌆 Пентхаус есть" if user.get('has_penthouse') else ""
    
    return f"""
👤 *{user['name']}*{nickname_text}
📅 {user['birth_date']} | {age_text}
📍 {user['country']}, {user['city']}
🏦 Семья: {user.get('family_wealth','medium')}
🎓 {user['education'] or 'Без образования'}
💼 {user['job'] or 'Безработный'}
{car_text}{bike_text}{home_text}{pent_text}

🧠 Интеллект: {user['intelligence']}/100
💪 Здоровье: {user['health']}/100
😎 Харизма: {user['charisma']}/100
🍀 Удача: {user['luck']}/100
💰 Деньги: {user['money']:,} ₽
😵 Стресс: {user['stress']}/100
❤️ Счастье: {user['happiness']}/100
🔥 Репутация: {user['reputation']}/100
🚔 Криминал: {user['criminal_level']}/100
"""

# ====================== КЛАВИАТУРЫ ======================

def main_menu_keyboard(user=None):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Продолжить жизнь", callback_data="continue_life"),
        types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🚗 Транспорт", callback_data="transport"),
        types.InlineKeyboardButton("✈️ Путешествия", callback_data="travel"),
        types.InlineKeyboardButton("❤️ Отношения", callback_data="relationships"),
        types.InlineKeyboardButton("💰 Бизнес", callback_data="business"),
        types.InlineKeyboardButton("🚔 Тюрьма", callback_data="jail_status"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("📜 Прошлые жизни", callback_data="past_lives"),
        types.InlineKeyboardButton("❌ Выход", callback_data="exit_game")
    )
    return keyboard

def life_actions_keyboard(user):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    stage = get_stage_by_age(user["age_months"])
    keyboard.add(types.InlineKeyboardButton("▶️ Прожить месяц", callback_data="next_month"))
    
    if stage == "adult":
        keyboard.add(
            types.InlineKeyboardButton("💼 Работать", callback_data="action_work"),
            types.InlineKeyboardButton("📚 Учиться", callback_data="action_study"),
            types.InlineKeyboardButton("🏋️ Тренировка", callback_data="action_sport"),
            types.InlineKeyboardButton("🎉 Тусовка", callback_data="action_party"),
        )
    elif stage == "school":
        keyboard.add(
            types.InlineKeyboardButton("📚 Учиться", callback_data="action_study"),
            types.InlineKeyboardButton("🏀 Спорт", callback_data="action_sport"),
            types.InlineKeyboardButton("🎮 Играть", callback_data="action_play"),
        )
    elif stage == "student":
        keyboard.add(
            types.InlineKeyboardButton("📚 Учиться", callback_data="action_study"),
            types.InlineKeyboardButton("💼 Подработка", callback_data="action_work"),
            types.InlineKeyboardButton("🎉 Тусовка", callback_data="action_party"),
        )
    
    keyboard.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# ====================== ОБРАБОТЧИКИ КОМАНД ======================

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user = get_db_user(user_id)
    
    if user and user["is_alive"] == 1:
        bot.send_message(user_id, f"👋 С возвращением, {user['name']}!", reply_markup=main_menu_keyboard(user))
    else:
        # Удаляем старую запись если есть
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        user_temp[user_id] = {}
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
            types.InlineKeyboardButton("👩 Женский", callback_data="gender_female")
        )
        bot.send_message(user_id, "🌟 *Новая жизнь!*\nВыбери пол:", parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def choose_gender(call):
    user_id = call.from_user.id
    gender = call.data.split("_")[1]
    user_temp[user_id] = {"gender": gender}
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✏️ Выбрать имя", callback_data="name_choose"),
        types.InlineKeyboardButton("🎲 Случайное имя", callback_data="name_random")
    )
    bot.edit_message_text("✏️ Выбери имя:", user_id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("name_"))
def choose_name(call):
    user_id = call.from_user.id
    choice = call.data.split("_")[1]
    
    if choice == "random":
        gender = user_temp[user_id]["gender"]
        male_names = ["Александр","Дмитрий","Максим","Иван","Сергей"]
        female_names = ["Анна","Мария","Елена","Ольга","Екатерина"]
        name = random.choice(male_names if gender == "male" else female_names)
        user_temp[user_id]["name"] = name
        ask_nickname(call)
    else:
        msg = bot.edit_message_text("✏️ Отправь имя персонажа:", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_name)

def process_name(message):
    user_id = message.from_user.id
    user_temp[user_id]["name"] = message.text
    ask_nickname_by_message(message)

def ask_nickname(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✏️ Ввести", callback_data="nick_choose"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="nick_skip")
    )
    bot.edit_message_text("💬 Ласковое имя (прозвище)?", call.from_user.id, call.message.message_id, reply_markup=keyboard)

def ask_nickname_by_message(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✏️ Ввести", callback_data="nick_choose"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="nick_skip")
    )
    bot.send_message(message.from_user.id, "💬 Ласковое имя (прозвище)?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("nick_"))
def choose_nickname(call):
    user_id = call.from_user.id
    choice = call.data.split("_")[1]
    if choice == "skip":
        user_temp[user_id]["nickname"] = ""
        ask_family(call)
    else:
        msg = bot.edit_message_text("✏️ Отправь прозвище:", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_nickname)

def process_nickname(message):
    user_id = message.from_user.id
    user_temp[user_id]["nickname"] = message.text
    ask_family_by_message(message)

def ask_family(call):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, ftype, _, _, _ in FAMILY_TYPES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"family_{ftype}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="family_random"))
    bot.edit_message_text("🏠 Выбери семью:", call.from_user.id, call.message.message_id, reply_markup=keyboard)

def ask_family_by_message(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, ftype, _, _, _ in FAMILY_TYPES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"family_{ftype}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="family_random"))
    bot.send_message(message.from_user.id, "🏠 Выбери семью:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("family_"))
def choose_family(call):
    user_id = call.from_user.id
    ftype = call.data.split("_")[1]
    
    if ftype == "random":
        fam = random.choice(FAMILY_TYPES)
    else:
        fam = next((f for f in FAMILY_TYPES if f[1] == ftype), FAMILY_TYPES[1])
    
    user_temp[user_id]["family_wealth"] = fam[1]
    user_temp[user_id]["money"] = fam[2]
    user_temp[user_id]["luck"] = fam[3]
    user_temp[user_id]["stress"] = fam[4]
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _, _ in get_countries():
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"country_{code}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="country_random"))
    bot.edit_message_text("🌍 Страна рождения:", user_id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def choose_country(call):
    user_id = call.from_user.id
    code = call.data.split("_")[1]
    
    if code == "random":
        country = random.choice(get_countries())
    else:
        country = next((c for c in get_countries() if c[1] == code), get_countries()[0])
    
    name = user_temp[user_id].get("name", "Персонаж")
    nickname = user_temp[user_id].get("nickname", "")
    gender = user_temp[user_id]["gender"]
    family = user_temp[user_id].get("family_wealth", "medium")
    money = user_temp[user_id].get("money", 50000)
    luck = user_temp[user_id].get("luck", 30)
    stress = user_temp[user_id].get("stress", 20)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    birth_date = (datetime.now() - timedelta(days=random.randint(0, 365*18))).strftime("%d.%m.%Y")
    
    # Ровно 29 значений
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, gender, birth_date, country, city, name, nickname,
         family_wealth, age_months, intelligence, health, charisma, luck, money, stress,
         happiness, reputation, criminal_level, education, job, car, bike,
         has_apartment, has_penthouse, is_alive, game_stage, last_event_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 30, 80, 30, ?, ?, ?, 60, 50, 0, '', '', '', '', 0, 0, 1, 'baby', '')
    ''', (user_id, call.from_user.username or "", call.from_user.first_name or "", gender,
          birth_date, country[0], country[2], name, nickname, family,
          luck, money, stress))
    
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    
    bot.edit_message_text(
        f"🎉 *Рождение!*\n\n👶 {user['name']} '{nickname}'\n📅 {birth_date}\n📍 {country[0]}, {country[2]}\n🏦 Семья: {family}\n💰 Стартовый капитал: {money:,} ₽\n\nТвоя история начинается!",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))
    
    if user_id in user_temp: del user_temp[user_id]

@bot.callback_query_handler(func=lambda call: call.data == "next_month")
def next_month(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age_months = age_months + 1 WHERE user_id = ?", (user_id,))
    
    if user["age_months"] // 12 >= 18:
        if user["job"]:
            salary = random.randint(20000, 80000)
            cursor.execute("UPDATE users SET money = money + ? WHERE user_id = ?", (salary, user_id))
    
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    is_dead, reason = check_death(user)
    
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(
            f"💀 *Ты умер!*\nВозраст: {death_age} лет\nПричина: {death_reason}\n💰 {user['money']:,} ₽\nРейтинг: *{rank}*",
            user_id, call.message.message_id, parse_mode="Markdown",
            reply_markup=main_menu_keyboard())
        return
    
    age_text = get_age_text(user["age_months"])
    text = f"📅 *{age_text}*\nМесяц пролетел...\n\n{get_profile_text(user)}"
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def player_action(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    if not user: return
    
    action = call.data.split("_")[1]
    effects = {}
    title = ""
    desc = ""
    
    if action == "work":
        salary = random.randint(5000, 50000)
        effects = {"money": salary, "stress": 10, "intelligence": 3}
        title = "💼 Работа"
        desc = f"Ты усердно работал и заработал {salary:,} ₽"
    elif action == "study":
        effects = {"intelligence": 10, "stress": 5}
        title = "📚 Учёба"
        desc = "Ты учился и стал умнее!"
    elif action == "sport":
        effects = {"health": 10, "stress": -5, "happiness": 5}
        title = "🏋️ Тренировка"
        desc = "Хорошая тренировка! Здоровье +10"
    elif action == "party":
        effects = {"happiness": 15, "stress": -10, "health": -3, "money": -3000}
        title = "🎉 Тусовка"
        desc = "Отличная вечеринка! Но здоровье подкосилось..."
    elif action == "play":
        effects = {"happiness": 10, "stress": -5, "intelligence": -2}
        title = "🎮 Игры"
        desc = "Поиграл в игры, повеселился"
    
    changes = apply_effects(user_id, effects)
    user = get_db_user(user_id)
    change_text = "\n".join(changes) if changes else "Без изменений"
    
    bot.edit_message_text(
        f"*{title}*\n{desc}\n\n📊 *Изменения:*\n{change_text}\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop_menu(call):
    user = get_db_user(call.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🍔 Еда", callback_data="shop_food"),
        types.InlineKeyboardButton("🍺 Алкоголь", callback_data="shop_alcohol"),
        types.InlineKeyboardButton("🚬 Сигареты", callback_data="shop_cigarettes"),
        types.InlineKeyboardButton("💨 Вейпы", callback_data="shop_vape"),
        types.InlineKeyboardButton("⚡ Энергетики", callback_data="shop_energy"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    bot.edit_message_text("🛒 *Магазин*\nВыбери категорию:", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    user_id = call.from_user.id
    category = call.data.split("_")[1]
    items = SHOP_ITEMS.get(category, [])
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, _ in items:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽", callback_data=f"buy_{category}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="shop"))
    
    bot.edit_message_text(f"🛒 *Товары:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    parts = call.data.split("_")
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    items = SHOP_ITEMS.get(category, [])
    item = next((i for i in items if i[0] == item_name), None)
    
    if not item:
        bot.answer_callback_query(call.id, "Товар не найден")
        return
    
    name, price, effects = item
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает денег! Нужно {price} ₽")
        return
    
    changes = apply_effects(user_id, {"money": -price})
    changes2 = apply_effects(user_id, effects)
    all_changes = changes + changes2
    
    user = get_db_user(user_id)
    change_text = "\n".join(all_changes)
    
    bot.edit_message_text(
        f"✅ Куплено: {name}\n\n📊 *Изменения:*\n{change_text}\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "transport")
def transport_menu(call):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🚲 Велосипеды", callback_data="trans_bicycles"),
        types.InlineKeyboardButton("🏍️ Питбайки", callback_data="trans_pitbikes"),
        types.InlineKeyboardButton("🏍️ Мотоциклы", callback_data="trans_motorcycles"),
        types.InlineKeyboardButton("🚗 Машины", callback_data="trans_cars"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    bot.edit_message_text("🚗 *Транспорт*", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("trans_"))
def transport_category(call):
    user_id = call.from_user.id
    cat = call.data.split("_")[1]
    items = TRANSPORT.get(cat, [])
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, vtype in items:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽", callback_data=f"buyveh_{vtype}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="transport"))
    
    bot.edit_message_text(f"🚗 *Выбери:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyveh_"))
def buy_vehicle(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    parts = call.data.split("_")
    vtype = parts[1]
    vname = "_".join(parts[2:])
    
    all_vehicles = []
    for cat_items in TRANSPORT.values():
        all_vehicles.extend(cat_items)
    
    vehicle = next((v for v in all_vehicles if v[0] == vname), None)
    if not vehicle: return
    
    name, price, _ = vehicle
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает денег! Нужно {price:,} ₽")
        return
    
    apply_effects(user_id, {"money": -price, "happiness": 10})
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if vtype in ["Машина"]:
        cursor.execute("UPDATE users SET car = ? WHERE user_id = ?", (name, user_id))
    else:
        cursor.execute("UPDATE users SET bike = ? WHERE user_id = ?", (name, user_id))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(f"✅ Куплено: {name}\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "travel")
def travel_menu(call):
    user = get_db_user(call.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, _ in TRAVELS:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽", callback_data=f"travelgo_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    bot.edit_message_text(f"✈️ *Путешествия*\n💰 {user['money']:,} ₽", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("travelgo_"))
def travel_go(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    tname = "_".join(call.data.split("_")[1:])
    
    travel = next((t for t in TRAVELS if t[0] == tname), None)
    if not travel: return
    
    name, price, effects = travel
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает денег! Нужно {price:,} ₽")
        return
    
    changes = apply_effects(user_id, {"money": -price})
    changes2 = apply_effects(user_id, effects)
    all_changes = changes + changes2
    
    user = get_db_user(user_id)
    change_text = "\n".join(all_changes)
    
    bot.edit_message_text(
        f"✈️ *{name}*\nОтличная поездка!\n\n📊 *Изменения:*\n{change_text}\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user = get_db_user(call.from_user.id)
    if not user or user["is_alive"] != 1: return
    bot.edit_message_text(get_profile_text(user), call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=main_menu_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def return_to_menu(call):
    user = get_db_user(call.from_user.id)
    if user and user["is_alive"] == 1:
        text = f"🏠 *Главное меню*\n\n{get_profile_text(user)}"
        markup = main_menu_keyboard(user)
    else:
        text = "🏠 *Главное меню*\n\nНачни новую жизнь!"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"))
    bot.edit_message_text(text, call.from_user.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "past_lives")
def show_past_lives(call):
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_lives WHERE user_id = ? ORDER BY life_number DESC LIMIT 5", (user_id,))
    lives = cursor.fetchall()
    conn.close()
    if lives:
        text = "📜 *Прошлые жизни:*\n\n" + "\n\n".join([
            f"#{l['life_number']} | {l['country']}\n{l['death_age']} лет | {l['death_reason']}\nРейтинг: *{l['life_rank']}* | 💰 {l['money']:,} ₽"
            for l in lives
        ])
    else:
        text = "Нет прошлых жизней"
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "new_life")
def new_life_button(call):
    user = get_db_user(call.from_user.id)
    if user and user["is_alive"] == 1: end_life(user)
    user_temp[call.from_user.id] = {}
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
        types.InlineKeyboardButton("👩 Женский", callback_data="gender_female")
    )
    bot.edit_message_text("🌟 *Новая жизнь!*\nВыбери пол:", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["relationships", "business", "jail_status", "continue_life"])
def stub_menus(call):
    user = get_db_user(call.from_user.id)
    if not user: return
    texts = {"relationships": "❤️ *Отношения*\nВ разработке...", 
             "business": "💰 *Бизнес*\nВ разработке...", 
             "jail_status": "🚔 *Тюрьма*\nТы на свободе!",
             "continue_life": "▶️ Продолжаем жить!"}
    bot.edit_message_text(f"{texts.get(call.data, '')}\n\n{get_profile_text(user)}",
                         call.from_user.id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=main_menu_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "exit_game")
def exit_game(call):
    bot.edit_message_text("👋 До встречи! /start для новой игры", call.from_user.id, call.message.message_id)

if __name__ == "__main__":
    print("🤖 Бот Life Simulator запущен!")
    bot.remove_webhook()
    bot.infinity_polling()
