import os
import sqlite3
import random
import time
from datetime import datetime, timedelta

import telebot
from telebot import types

# ====================== ТОКЕН ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_СЮДА")
bot = telebot.TeleBot(BOT_TOKEN, num_threads=1)

REQUEST_DELAY = 0.08

# ====================== БАЗА ДАННЫХ ======================
DB_NAME = "life_simulator.db"

if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print("🔄 Старая база данных удалена")

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
            nickname TEXT DEFAULT '',
            family_wealth TEXT DEFAULT 'medium',
            difficulty TEXT DEFAULT 'normal',
            talent TEXT DEFAULT '',
            appearance TEXT DEFAULT '',
            age_months INTEGER DEFAULT 0,
            extra_weeks INTEGER DEFAULT 0,
            school_grade INTEGER DEFAULT 0,
            education TEXT DEFAULT '',
            university TEXT DEFAULT '',
            job TEXT DEFAULT '',
            salary INTEGER DEFAULT 0,
            car TEXT DEFAULT '',
            bike TEXT DEFAULT '',
            has_apartment INTEGER DEFAULT 0,
            has_penthouse INTEGER DEFAULT 0,
            intelligence INTEGER DEFAULT 30,
            health INTEGER DEFAULT 80,
            charisma INTEGER DEFAULT 30,
            luck INTEGER DEFAULT 30,
            money INTEGER DEFAULT 0,
            stress INTEGER DEFAULT 20,
            happiness INTEGER DEFAULT 60,
            reputation INTEGER DEFAULT 50,
            criminal_level INTEGER DEFAULT 0,
            bonus_points INTEGER DEFAULT 0,
            military_category TEXT DEFAULT '',
            military_rank TEXT DEFAULT '',
            army_served INTEGER DEFAULT 0,
            prison_sentence INTEGER DEFAULT 0,
            is_alive INTEGER DEFAULT 1,
            game_stage TEXT DEFAULT 'baby',
            last_event_date TEXT DEFAULT '',
            og_math INTEGER DEFAULT 0,
            og_rus INTEGER DEFAULT 0,
            ege_math INTEGER DEFAULT 0,
            ege_rus INTEGER DEFAULT 0,
            ege_physics INTEGER DEFAULT 0,
            ege_info INTEGER DEFAULT 0,
            vpr_math INTEGER DEFAULT 0,
            vpr_rus INTEGER DEFAULT 0
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
            relation_type TEXT DEFAULT 'friend',
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
    print("✅ База данных создана")

init_db()

# ====================== ВРЕМЕННЫЕ ДАННЫЕ ======================
user_temp = {}
last_request_time = {}

def anti_flood(user_id):
    now = time.time()
    if user_id in last_request_time:
        elapsed = now - last_request_time[user_id]
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
    last_request_time[user_id] = time.time()

# ====================== ИГРОВЫЕ ДАННЫЕ ======================

DIFFICULTIES = [
    ("😊 Лёгкий", "easy", 2.0, 0.7, 1.5),
    ("😐 Нормальный", "normal", 1.0, 1.0, 1.0),
    ("😈 Хардкор", "hard", 0.5, 1.3, 0.7),
    ("💀 Реализм", "realism", 0.3, 1.5, 0.5),
]

TALENTS = [
    ("🏀 Спортсмен", "sport", {"health": 15, "charisma": 5}),
    ("📚 Умник", "smart", {"intelligence": 15, "stress": 10}),
    ("😎 Душа компании", "social", {"charisma": 15, "happiness": 10}),
    ("🔪 Криминальный", "criminal", {"criminal_level": 10, "luck": 5}),
]

APPEARANCES = [
    ("😍 Красавчик", "handsome", {"charisma": 15}),
    ("😐 Обычный", "normal", {}),
    ("😨 Страшный", "ugly", {"charisma": -10, "stress": 10}),
]

START_AGES = [
    ("👶 С рождения (0 лет)", 0),
    ("🧒 Пропустить детство (7 лет)", 84),
    ("👦 Пропустить школу (17 лет)", 204),
    ("🧑 Сразу взрослый (22 года)", 264),
    ("🎲 Случайный возраст", -1),
]

FAMILY_TYPES = [
    ("💰 Богатая (500к)", "rich", 500000, 15, 20),
    ("🏠 Средняя (50к)", "medium", 50000, 5, 15),
    ("🏚️ Бедная (5к)", "poor", 5000, 0, 10),
    ("💀 Детдом (0)", "orphanage", 0, -10, 30),
    ("🚔 Криминальная (100к)", "criminal", 100000, -5, 35),
]

COUNTRIES = [
    ("🇷🇺 Россия", "Russia", "Москва", 50000),
    ("🇺🇸 США", "USA", "Нью-Йорк", 150000),
    ("🇯🇵 Япония", "Japan", "Токио", 100000),
    ("🇩🇪 Германия", "Germany", "Берлин", 120000),
    ("🇧🇷 Бразилия", "Brazil", "Рио", 30000),
    ("🇰🇵 КНДР", "North Korea", "Пхеньян", 5000),
]

SHOP_ITEMS = {
    "food": [
        ("🍔 Бургер", 200, {"health": 2, "happiness": 5, "stress": -3}),
        ("🍕 Пицца", 500, {"health": -2, "happiness": 10, "stress": -5}),
        ("🍜 Доширак", 59, {"health": -1, "happiness": -2, "stress": 2}),
    ],
    "alcohol": [
        ("🍺 Балтика 7", 89, {"health": -3, "happiness": 8, "stress": -10}),
        ("🍺 Heineken 0.5", 129, {"health": -2, "happiness": 10, "stress": -8}),
        ("🥃 Jack Daniels 0.5", 1499, {"health": -6, "happiness": 18, "stress": -15}),
    ],
    "cigarettes": [
        ("🚬 Winston XStyle", 179, {"health": -5, "stress": -10, "happiness": 3}),
        ("🚬 Marlboro Gold", 219, {"health": -4, "stress": -12, "happiness": 4}),
    ],
    "vape": [
        ("💨 HQD Cuvie Plus", 599, {"health": -3, "stress": -15, "happiness": 10}),
        ("💨 Elf Bar 1500", 799, {"health": -2, "stress": -18, "happiness": 12}),
    ],
    "energy": [
        ("⚡ Red Bull", 149, {"health": -2, "stress": -5, "intelligence": 3}),
        ("⚡ Monster", 169, {"health": -3, "stress": -7, "intelligence": 5}),
    ],
}

TRANSPORT = {
    "bicycles": [("🚲 Stels Navigator", 15000, "Велик"), ("🚲 Merida Big Nine", 45000, "Велик")],
    "pitbikes": [("🏍️ Kayo 125", 80000, "Питбайк"), ("🏍️ BSE 140", 110000, "Питбайк")],
    "motorcycles": [("🏍️ Honda CB500", 450000, "Мотоцикл"), ("🏍️ Yamaha R3", 550000, "Мотоцикл")],
    "cars": [("🚗 LADA Granta", 700000, "Машина"), ("🚗 Toyota Camry", 2800000, "Машина"), ("🚗 BMW X5", 7500000, "Машина")],
}

TRAVELS = [
    ("🏡 В деревню", 5000, 1, {"happiness": 15, "stress": -20}),
    ("🏖️ На море", 50000, 2, {"happiness": 30, "stress": -30}),
    ("✈️ Турция", 120000, 2, {"happiness": 55, "stress": -35}),
]

# ====================== ФУНКЦИИ ======================

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
    m = months % 12
    if years == 0: return f"{m} мес."
    elif years < 3: return f"{years} г. {m} мес."
    else: return f"{years} лет"

def get_stage(user):
    years = user["age_months"] // 12
    if years < 3: return "baby"
    elif years < 7: return "kindergarten"
    elif years < 12: return "junior_school"
    elif years < 17: return "school"
    elif years < 23: return "university" if user.get('university') else "young_adult"
    elif years < 60: return "adult"
    elif years < 75: return "elderly"
    else: return "old"

def apply_effects(user_id, effects):
    if not effects: return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    user = get_db_user(user_id)
    difficulty = user["difficulty"] if user else "normal"
    diff_data = next((d for d in DIFFICULTIES if d[1] == difficulty), DIFFICULTIES[1])
    money_mult = diff_data[2]
    changes = []
    for stat, delta in effects.items():
        col_map = {
            "intelligence":"intelligence","health":"health","charisma":"charisma",
            "luck":"luck","money":"money","stress":"stress",
            "happiness":"happiness","reputation":"reputation","criminal_level":"criminal_level"
        }
        col = col_map.get(stat)
        if col:
            if col == "money":
                delta = int(delta * money_mult)
                cursor.execute(f"UPDATE users SET money = money + ? WHERE user_id = ?", (delta, user_id))
            else:
                cursor.execute(f"UPDATE users SET {col} = MAX(0, MIN(100, {col} + ?)) WHERE user_id = ?", (delta, user_id))
            emoji = {"intelligence":"🧠","health":"💪","charisma":"😎","luck":"🍀","money":"💰","stress":"😵","happiness":"❤️","reputation":"🔥","criminal_level":"🚔"}.get(col,"📊")
            name = {"intelligence":"Интеллект","health":"Здоровье","charisma":"Харизма","luck":"Удача","money":"Деньги","stress":"Стресс","happiness":"Счастье","reputation":"Репутация","criminal_level":"Криминал"}.get(col,col)
            sign = "+" if delta >= 0 else ""
            changes.append(f"{emoji} {name}: {sign}{delta}")
    conn.commit()
    conn.close()
    return changes

def add_months(user_id, months):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age_months = age_months + ? WHERE user_id = ?", (months, user_id))
    conn.commit()
    conn.close()

def check_death(user):
    years = user["age_months"] // 12
    health = user["health"]
    if user.get("difficulty") == "realism":
        if health <= 15: return True, "Осложнения (реализм)"
        if years >= 75: return True, "Старость (реализм)"
    if years >= 95: return True, "Естественная смерть от старости"
    if health <= 0: return True, "Смерть от болезней"
    if health <= 10 and years >= 70 and random.random() < 0.3: return True, "Осложнения от болезней"
    if user["stress"] >= 100 and health < 30 and random.random() < 0.2: return True, "Сердечный приступ"
    return False, None

def end_life(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    death_age = user["age_months"] // 12
    death_reason = "Несчастный случай"
    if user["health"] <= 0: death_reason = "Болезнь"
    elif death_age >= 90: death_reason = "Старость"
    elif user["stress"] >= 100: death_reason = "Сердечный приступ"
    
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
    
    for table in ["relationships","businesses","jail","inventory","users"]:
        cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user["user_id"],))
    conn.commit()
    conn.close()
    return death_age, death_reason, rank, int(score)

def create_family(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    user = get_db_user(user_id)
    if not user: return
    
    family = user["family_wealth"]
    names_m = ["Сергей","Андрей","Владимир","Алексей","Николай"]
    names_f = ["Елена","Ольга","Татьяна","Наталья","Ирина"]
    
    if family == "orphanage":
        cursor.execute('''INSERT INTO relationships (user_id, npc_name, npc_type, relation_type, attachment, trust, status)
            VALUES (?, 'Воспитатель Мария', 'caretaker', 'family', 30, 40, 'guardian')''', (user_id,))
    else:
        father = random.choice(names_m)
        mother = random.choice(names_f)
        cursor.execute('''INSERT INTO relationships (user_id, npc_name, npc_type, relation_type, attachment, trust, status)
            VALUES (?, ?, 'parent', 'family', 60, 70, 'parent')''', (user_id, father))
        cursor.execute('''INSERT INTO relationships (user_id, npc_name, npc_type, relation_type, attachment, trust, status)
            VALUES (?, ?, 'parent', 'family', 65, 75, 'parent')''', (user_id, mother))
        if random.random() < 0.5:
            sibling = random.choice(["Дима","Катя","Саша"])
            cursor.execute('''INSERT INTO relationships (user_id, npc_name, npc_type, relation_type, attachment, trust, status)
                VALUES (?, ?, 'sibling', 'family', 50, 50, 'sibling')''', (user_id, sibling))
    conn.commit()
    conn.close()

def get_profile_text(user):
    u = dict(user)
    age_text = get_age_text(u["age_months"])
    nick = f'\n💬 "{u["nickname"]}"' if u.get("nickname") else ""
    diff = f'\n🎮 {u.get("difficulty","normal")}'
    tal = f'\n⭐ {u.get("talent","")}' if u.get("talent") else ""
    
    stage = get_stage(user)
    ed_text = ""
    if stage in ["junior_school","school"]:
        grade = (u["age_months"] // 12) - 6
        ed_text = f"\n🏫 {grade} класс"
    elif stage == "university":
        ed_text = f"\n🎓 {u.get('university','Универ')}"
    elif stage == "kindergarten":
        ed_text = "\n🧒 Детский сад"
    
    car_text = f"\n🚗 {u['car']}" if u.get('car') else ""
    bike_text = f"\n🏍️ {u['bike']}" if u.get('bike') else ""
    
    return f"""
👤 *{u['name']}*{nick}{diff}{tal}
📅 {u['birth_date']} | {age_text}
📍 {u['country']}, {u['city']}
🏦 Семья: {u.get('family_wealth','medium')}{ed_text}
💼 {u['job'] or 'Без работы'}{car_text}{bike_text}

🧠 {u['intelligence']}/100 💪 {u['health']}/100
😎 {u['charisma']}/100 🍀 {u['luck']}/100
💰 {u['money']:,} ₽ 😵 {u['stress']}/100
❤️ {u['happiness']}/100 🔥 {u['reputation']}/100
🚔 Криминал: {u['criminal_level']}/100
"""

# ====================== КЛАВИАТУРЫ ======================

def life_actions_keyboard(user):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    stage = get_stage(user)
    years = user["age_months"] // 12
    
    if stage == "baby":
        keyboard.add(types.InlineKeyboardButton("👶 Следующий месяц", callback_data="action_baby"))
    elif stage == "kindergarten":
        keyboard.add(
            types.InlineKeyboardButton("🧸 Играть", callback_data="action_play"),
            types.InlineKeyboardButton("📖 Учить буквы", callback_data="action_study"),
            types.InlineKeyboardButton("🤼 Драться", callback_data="action_fight"),
        )
    elif stage in ["junior_school","school"]:
        keyboard.add(
            types.InlineKeyboardButton("📚 Уроки", callback_data="action_study"),
            types.InlineKeyboardButton("⚽ Спорт", callback_data="action_sport"),
        )
        if years >= 12:
            keyboard.add(types.InlineKeyboardButton("🚭 За школой", callback_data="action_skip"))
            keyboard.add(types.InlineKeyboardButton("🙏 Попросить купить", callback_data="ask_buy"))
        if stage == "school" and years >= 15:
            keyboard.add(types.InlineKeyboardButton("📝 ОГЭ/ЕГЭ", callback_data="exam_oge"))
        if years >= 14:
            keyboard.add(types.InlineKeyboardButton("🔪 АУЕ тема", callback_data="crime_au"))
    elif stage == "university" or stage == "young_adult":
        keyboard.add(
            types.InlineKeyboardButton("📚 Учёба", callback_data="action_study"),
            types.InlineKeyboardButton("🍺 Вечеринка", callback_data="action_party"),
            types.InlineKeyboardButton("💼 Подработка", callback_data="action_work"),
        )
    elif stage == "adult":
        keyboard.add(
            types.InlineKeyboardButton("💼 Работа", callback_data="action_work"),
            types.InlineKeyboardButton("🏋️ Спорт", callback_data="action_sport"),
            types.InlineKeyboardButton("📚 Саморазвитие", callback_data="action_study"),
            types.InlineKeyboardButton("🎉 Тусовка", callback_data="action_party"),
        )
    
    keyboard.add(
        types.InlineKeyboardButton("⏩ Пропустить время", callback_data="skip_time"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory_use"),
        types.InlineKeyboardButton("👫 Отношения", callback_data="relations_menu"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏠 Меню", callback_data="main_menu")
    )
    return keyboard

def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Продолжить", callback_data="continue_life"),
        types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("📜 Прошлые жизни", callback_data="past_lives"),
        types.InlineKeyboardButton("❌ Выход", callback_data="exit_game")
    )
    return keyboard

# ====================== ОБРАБОТЧИК СТАРТА ======================

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    
    if user and user["is_alive"] == 1:
        bot.send_message(user_id, f"👋 С возвращением, {user['name']}!", reply_markup=main_menu_keyboard())
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        user_temp[user_id] = {"step": "gender"}
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
            types.InlineKeyboardButton("👩 Женский", callback_data="gender_female")
        )
        bot.send_message(user_id, "🌟 *Новая жизнь!*\n\nВыбери пол:", parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def choose_gender(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    gender = call.data.split("_")[1]
    user_temp[user_id] = {"gender": gender, "step": "name"}
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✏️ Выбрать имя", callback_data="name_choose"),
        types.InlineKeyboardButton("🎲 Случайное", callback_data="name_random")
    )
    bot.edit_message_text("✏️ Выбери имя:", user_id, call.message.message_id, reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("name_"))
def choose_name(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    if call.data == "name_random":
        gender = user_temp[user_id]["gender"]
        names_m = ["Александр","Дмитрий","Максим","Иван","Сергей"]
        names_f = ["Анна","Мария","Елена","Ольга","Екатерина"]
        user_temp[user_id]["name"] = random.choice(names_m if gender == "male" else names_f)
        user_temp[user_id]["nickname"] = ""
        user_temp[user_id]["step"] = "start_age"
        ask_start_age(call)
    else:
        user_temp[user_id]["step"] = "name_input"
        msg = bot.edit_message_text("✏️ Отправь имя текстом:", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_name)
    time.sleep(REQUEST_DELAY)

def process_name(message):
    user_id = message.from_user.id
    user_temp[user_id]["name"] = message.text
    user_temp[user_id]["nickname"] = ""
    user_temp[user_id]["step"] = "start_age"
    ask_start_age_by_message(message)

def ask_start_age(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, age in START_AGES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"startage_{age}"))
    bot.edit_message_text("📅 *С какого возраста начать?*", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

def ask_start_age_by_message(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, age in START_AGES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"startage_{age}"))
    bot.send_message(message.from_user.id, "📅 *С какого возраста начать?*", parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("startage_"))
def choose_start_age(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    age_months = int(call.data.split("_")[1])
    if age_months == -1:
        age_months = random.randint(0, 360)
    user_temp[user_id]["start_age"] = age_months
    user_temp[user_id]["step"] = "bonus_points"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("⭐ Распределить очки", callback_data="bonus_yes"),
        types.InlineKeyboardButton("🎲 Случайно", callback_data="bonus_random"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="bonus_skip"),
    )
    bot.edit_message_text("⭐ *Распределить бонусные очки (15)?*", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("bonus_"))
def choose_bonus(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    choice = call.data.split("_")[1]
    
    if choice == "yes":
        user_temp[user_id]["bonus_points"] = 15
        user_temp[user_id]["bonuses"] = {"intelligence": 0, "health": 0, "charisma": 0, "luck": 0}
        show_bonus_menu(call)
    elif choice == "random":
        user_temp[user_id]["bonuses"] = {
            "intelligence": random.randint(0, 15),
            "health": random.randint(0, 15),
            "charisma": random.randint(0, 15),
            "luck": 15
        }
        user_temp[user_id]["step"] = "difficulty"
        ask_difficulty(call)
    else:
        user_temp[user_id]["bonuses"] = {"intelligence": 0, "health": 0, "charisma": 0, "luck": 0}
        user_temp[user_id]["step"] = "difficulty"
        ask_difficulty(call)
    time.sleep(REQUEST_DELAY)

def show_bonus_menu(call):
    user_id = call.from_user.id
    data = user_temp[user_id]
    bonuses = data.get("bonuses", {})
    points = data.get("bonus_points", 0)
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(f"🧠 Интеллект +1 ({bonuses.get('intelligence',0)})", callback_data="add_intelligence"),
        types.InlineKeyboardButton(f"💪 Здоровье +1 ({bonuses.get('health',0)})", callback_data="add_health"),
        types.InlineKeyboardButton(f"😎 Харизма +1 ({bonuses.get('charisma',0)})", callback_data="add_charisma"),
        types.InlineKeyboardButton(f"🍀 Удача +1 ({bonuses.get('luck',0)})", callback_data="add_luck"),
        types.InlineKeyboardButton(f"✅ Готово ({points} осталось)", callback_data="bonus_done"),
    )
    bot.edit_message_text(f"⭐ Осталось очков: {points}", user_id, call.message.message_id, reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def add_bonus_point(call):
    user_id = call.from_user.id
    stat = call.data.split("_")[1]
    if user_temp[user_id].get("bonus_points", 0) > 0:
        user_temp[user_id]["bonus_points"] -= 1
        user_temp[user_id]["bonuses"][stat] = user_temp[user_id]["bonuses"].get(stat, 0) + 1
    show_bonus_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "bonus_done")
def bonus_done(call):
    user_id = call.from_user.id
    user_temp[user_id]["step"] = "difficulty"
    ask_difficulty(call)

def ask_difficulty(call):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _, _ in DIFFICULTIES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"diff_{code}"))
    bot.edit_message_text("🎮 *Сложность:*", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("diff_"))
def choose_difficulty(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user_temp[user_id]["difficulty"] = call.data.split("_")[1]
    user_temp[user_id]["step"] = "talent"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, tcode, _ in TALENTS:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"talent_{tcode}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайный", callback_data="talent_random"))
    bot.edit_message_text("⭐ *Талант:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("talent_"))
def choose_talent(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    tcode = call.data.split("_")[1]
    talent = random.choice(TALENTS) if tcode == "random" else next((t for t in TALENTS if t[1] == tcode), TALENTS[1])
    user_temp[user_id]["talent"] = talent[1]
    user_temp[user_id]["talent_effects"] = talent[2]
    user_temp[user_id]["step"] = "appearance"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, acode, _ in APPEARANCES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"appearance_{acode}"))
    bot.edit_message_text("👤 *Внешность:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("appearance_"))
def choose_appearance(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    acode = call.data.split("_")[1]
    app = random.choice(APPEARANCES) if acode == "random" else next((a for a in APPEARANCES if a[1] == acode), APPEARANCES[1])
    user_temp[user_id]["appearance"] = app[1]
    user_temp[user_id]["appearance_effects"] = app[2]
    user_temp[user_id]["step"] = "family"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, ftype, _, _, _ in FAMILY_TYPES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"family_{ftype}"))
    bot.edit_message_text("🏠 *Семья:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("family_"))
def choose_family(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    ftype = call.data.split("_")[1]
    fam = random.choice(FAMILY_TYPES) if ftype == "random" else next((f for f in FAMILY_TYPES if f[1] == ftype), FAMILY_TYPES[1])
    user_temp[user_id]["family_wealth"] = fam[1]
    user_temp[user_id]["money"] = fam[2]
    user_temp[user_id]["luck_bonus"] = fam[3]
    user_temp[user_id]["stress_bonus"] = fam[4]
    user_temp[user_id]["step"] = "country"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _ in COUNTRIES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"country_{code}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="country_random"))
    bot.edit_message_text("🌍 *Страна:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def choose_country(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    code = call.data.split("_")[1]
    country = random.choice(COUNTRIES) if code == "random" else next((c for c in COUNTRIES if c[1] == code), COUNTRIES[0])
    
    data = user_temp[user_id]
    start_age = data.get("start_age", 0)
    bonuses = data.get("bonuses", {})
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    birth_date = (datetime.now() - timedelta(days=start_age * 30 + random.randint(0, 365))).strftime("%d.%m.%Y")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, gender, birth_date, country, city, name, nickname,
         family_wealth, difficulty, talent, appearance, age_months, intelligence, health, 
         charisma, luck, money, stress, happiness, reputation, criminal_level, 
         education, university, job, car, bike, has_apartment, has_penthouse, 
         army_served, is_alive, game_stage, extra_weeks, bonus_points, last_event_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,30,80,30,?,?,?,60,50,0,'','','','','',0,0,0,1,'baby',0,0,'')
    ''', (user_id, call.from_user.username or "", call.from_user.first_name or "", data["gender"],
          birth_date, country[0], country[2], data.get("name","Персонаж"), data.get("nickname",""),
          data.get("family_wealth","medium"), data.get("difficulty","normal"),
          data.get("talent",""), data.get("appearance",""),
          data.get("luck",30) + bonuses.get("luck",0), data.get("money",50000), data.get("stress",20)))
    
    conn.commit()
    conn.close()
    
    # Применяем бонусы
    if bonuses:
        for stat, val in bonuses.items():
            if val > 0:
                apply_effects(user_id, {stat: val})
    if data.get("talent_effects"):
        apply_effects(user_id, data["talent_effects"])
    if data.get("appearance_effects"):
        apply_effects(user_id, data["appearance_effects"])
    if data.get("luck_bonus"):
        apply_effects(user_id, {"luck": data["luck_bonus"]})
    if data.get("stress_bonus"):
        apply_effects(user_id, {"stress": data["stress_bonus"]})
    
    # Создаём семью (NPC)
    create_family(user_id)
    
    user = get_db_user(user_id)
    if user_id in user_temp: del user_temp[user_id]
    
    bot.edit_message_text(
        f"🎉 *Рождение!*\n\n👶 {user['name']}\n📅 {birth_date}\n"
        f"📍 {country[0]}, {country[2]}\n🏦 {user['family_wealth']}\n"
        f"🎮 {user['difficulty']}\n⭐ {user['talent']}\n💰 {user['money']:,} ₽",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== ДЕЙСТВИЯ ИГРОКА ======================

@bot.callback_query_handler(func=lambda call: call.data == "continue_life")
def continue_life(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return
    bot.edit_message_text(get_profile_text(user), user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def player_action(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    if not user or user["is_alive"] != 1: return
    
    action = call.data.split("_")[1]
    effects, title, desc = {}, "", ""
    months = 0
    
    if action == "baby":
        months = 1
        baby_events = [
            ("🍼 Кормление", {"health": 5, "happiness": 5}),
            ("🚶 Первые шаги", {"intelligence": 3, "happiness": 10}),
            ("🦷 Первый зуб", {"health": 2, "stress": 5}),
            ("🤒 Простуда", {"health": -5, "stress": 5}),
        ]
        ev = random.choice(baby_events)
        title, desc, effects = ev[0], ev[0], ev[1]
    elif action == "play":
        months = 1
        effects, title, desc = {"happiness": 10, "charisma": 5}, "🧸 Игры", "Весело провёл время!"
    elif action == "fight":
        months = 1
        if random.random() < 0.5:
            effects, title, desc = {"health": -5, "criminal_level": 3, "reputation": -5}, "🤼 Драка", "Подрался и получил синяк"
        else:
            effects, title, desc = {"health": -3, "charisma": 5, "reputation": 3}, "🤼 Драка", "Победил в драке!"
    elif action == "study":
        months = 1
        effects, title, desc = {"intelligence": random.randint(5,15), "stress": 5}, "📚 Учёба", "Месяц учёбы"
    elif action == "sport":
        months = 1
        effects, title, desc = {"health": random.randint(5,15), "happiness": 5}, "⚽ Спорт", "Тренировка!"
    elif action == "work":
        months = 1
        salary = random.randint(10000, 50000)
        effects, title, desc = {"money": salary, "stress": 10}, "💼 Работа", f"Заработал {salary:,} ₽"
    elif action == "party":
        months = 1
        effects, title, desc = {"happiness": random.randint(10,25), "stress": -10, "health": -3, "money": -random.randint(1000,5000)}, "🎉 Тусовка", "Повеселился!"
    elif action == "skip":
        months = 1
        effects, title, desc = {"happiness": 5, "stress": -5, "reputation": -5}, "🚭 За школой", "Прогулял..."
    
    if months:
        add_months(user_id, months)
    
    changes = apply_effects(user_id, effects)
    user = get_db_user(user_id)
    
    is_dead, reason = check_death(user)
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(f"💀 *Ты умер!*\nВозраст: {death_age} лет\nПричина: {death_reason}\nРейтинг: *{rank}*",
                             user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        time.sleep(REQUEST_DELAY)
        return
    
    change_text = "\n".join(changes) if changes else "Без изменений"
    bot.edit_message_text(f"*{title}*\n{desc}\n\n📊 Изменения:\n{change_text}\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== ПРОПУСК ВРЕМЕНИ ======================

@bot.callback_query_handler(func=lambda call: call.data == "skip_time")
def skip_time_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for months, label in [(6,"+6 мес"),(12,"+1 год"),(36,"+3 года"),(60,"+5 лет"),(120,"+10 лет")]:
        keyboard.add(types.InlineKeyboardButton(f"📅 {label}", callback_data=f"skipperiod_{months}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    bot.edit_message_text("⏩ *Пропустить время*\nВыбери период:", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("skipperiod_"))
def skip_period(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    months = int(call.data.split("_")[1])
    user = get_db_user(user_id)
    
    # Авто-изменения за период
    total_effects = {}
    for _ in range(months):
        total_effects["intelligence"] = total_effects.get("intelligence", 0) + random.randint(0, 2)
        total_effects["health"] = total_effects.get("health", 0) + random.randint(-1, 1)
        total_effects["money"] = total_effects.get("money", 0) + random.randint(-500, 5000)
        total_effects["stress"] = total_effects.get("stress", 0) + random.randint(-2, 3)
    
    add_months(user_id, months)
    changes = apply_effects(user_id, total_effects)
    user = get_db_user(user_id)
    
    is_dead, reason = check_death(user)
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(f"💀 *Ты умер во время пропуска!*\nВозраст: {death_age} лет\nПричина: {death_reason}\nРейтинг: *{rank}*",
                             user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        time.sleep(REQUEST_DELAY)
        return
    
    bot.edit_message_text(f"⏩ Пропущено {months} мес.\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== МАГАЗИН, ИНВЕНТАРЬ, ОТНОШЕНИЯ ======================

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for cat_name, cat_code in [("🍔 Еда","food"),("🍺 Алко","alcohol"),("🚬 Сиги","cigarettes"),("💨 Вейпы","vape"),("⚡ Энерг","energy")]:
        keyboard.add(types.InlineKeyboardButton(cat_name, callback_data=f"shop_{cat_code}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    bot.edit_message_text(f"🛒 *Магазин*\n💰 {user['money']:,} ₽", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    user_id = call.from_user.id
    cat = call.data.split("_")[1]
    items = SHOP_ITEMS.get(cat, [])
    user = get_db_user(user_id)
    years = user["age_months"] // 12
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, _ in items:
        if cat in ["alcohol","cigarettes","vape"] and years < 18:
            keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽ 🔞", callback_data=f"underage_{cat}_{name}"))
        else:
            keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽", callback_data=f"buy_{cat}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="shop"))
    bot.edit_message_text("🛒 *Товары:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    parts = call.data.split("_")
    cat = parts[1]
    item_name = "_".join(parts[2:])
    items = SHOP_ITEMS.get(cat, [])
    item = next((i for i in items if i[0] == item_name), None)
    if not item: return
    
    name, price, _ = item
    user = get_db_user(user_id)
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает {price} ₽")
        return
    
    apply_effects(user_id, {"money": -price})
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, name))
    ex = cursor.fetchone()
    if ex:
        cursor.execute("UPDATE inventory SET quantity = quantity + 1 WHERE id = ?", (ex[0],))
    else:
        cursor.execute("INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?,?,?,1)", (user_id, name, cat))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(f"✅ Куплено: {name}\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data in ["inventory_use", "inventory"])
def show_inventory(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        bot.answer_callback_query(call.id, "Инвентарь пуст!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for item in items:
        keyboard.add(types.InlineKeyboardButton(f"{item['item_name']} (x{item['quantity']})", callback_data=f"use_{item['id']}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    bot.edit_message_text("🎒 *Инвентарь*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_item(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    item_id = int(call.data.split("_")[1])
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ? AND user_id = ?", (item_id, user_id))
    item = cursor.fetchone()
    if not item:
        bot.answer_callback_query(call.id, "Нет предмета")
        conn.close()
        return
    
    all_effects = {}
    for cat_items in SHOP_ITEMS.values():
        for name, price, eff in cat_items:
            all_effects[name] = eff
    
    effects = all_effects.get(item["item_name"], {"happiness": 5})
    changes = apply_effects(user_id, effects)
    
    if item["quantity"] > 1:
        cursor.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = ?", (item_id,))
    else:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(f"✅ {item['item_name']}\n\n📊 Эффекты:\n" + "\n".join(changes) + f"\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "relations_menu")
def relations_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM relationships WHERE user_id = ?", (user_id,))
    rels = cursor.fetchall()
    conn.close()
    
    if not rels:
        text = "👫 *Отношения*\n\nНикого нет..."
    else:
        text = "👫 *Твои отношения:*\n\n"
        for r in rels:
            text += f"{r['npc_name']} ({r['relation_type']})\n❤️ {r['attachment']}% 🤝 {r['trust']}%\n\n"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

# ====================== ПРОЧИЕ ОБРАБОТЧИКИ ======================

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    if not user: return
    bot.edit_message_text(get_profile_text(user), user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def return_to_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    text = f"🏠 *Меню*\n\n{get_profile_text(user)}" if user and user["is_alive"] == 1 else "🏠 *Меню*"
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data in ["past_lives","new_life","exit_game","crime_au","exam_oge","ask_buy","underage_alcohol","underage_cigarettes","underage_vape","underage_energy"])
def stub_handlers(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    if call.data == "new_life":
        user = get_db_user(user_id)
        if user and user["is_alive"] == 1: end_life(user)
        user_temp[user_id] = {"step": "gender"}
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
                     types.InlineKeyboardButton("👩 Женский", callback_data="gender_female"))
        bot.edit_message_text("🌟 *Новая жизнь!*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    elif call.data == "exit_game":
        bot.edit_message_text("👋 До встречи!", user_id, call.message.message_id)
    elif call.data == "past_lives":
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM past_lives WHERE user_id = ? ORDER BY life_number DESC LIMIT 5", (user_id,))
        lives = cursor.fetchall()
        conn.close()
        text = "\n\n".join([f"#{l['life_number']} | {l['country']}\n{l['death_age']} лет | {l['death_reason']}\nРейтинг: *{l['life_rank']}*" for l in lives]) if lives else "Нет прошлых жизней"
        bot.edit_message_text(f"📜 *Прошлые жизни:*\n\n{text}", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        texts = {"crime_au":"🚔 АУЕ тема\nВ разработке...","exam_oge":"📝 Экзамены\nВ разработке...","ask_buy":"🙏 Попросить купить\nВ разработке..."}
        bot.edit_message_text(texts.get(call.data,"В разработке"), user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(get_db_user(user_id)))
    time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    print("🤖 Life Simulator v3.0 запущен!")
    bot.remove_webhook()
    bot.infinity_polling()
