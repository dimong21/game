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
            age_months INTEGER DEFAULT 0,
            school_grade INTEGER DEFAULT 0,
            education TEXT DEFAULT '',
            university TEXT DEFAULT '',
            job TEXT DEFAULT '',
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
            is_alive INTEGER DEFAULT 1,
            game_stage TEXT DEFAULT 'baby',
            extra_weeks INTEGER DEFAULT 0,
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

# ====================== ДАННЫЕ ИГРЫ ======================

SHOP_ITEMS = {
    "food": [
        ("🍔 Бургер", 200, {"health": 2, "happiness": 5, "stress": -3}),
        ("🍕 Пицца", 500, {"health": -2, "happiness": 10, "stress": -5}),
        ("🥗 Салат", 300, {"health": 5, "happiness": 2, "stress": -2}),
        ("🍜 Доширак", 50, {"health": -1, "happiness": -2, "stress": 2}),
    ],
    "alcohol": [
        ("🍺 Пиво Baltika 7", 100, {"health": -3, "happiness": 8, "stress": -10}),
        ("🍺 Пиво Heineken", 180, {"health": -2, "happiness": 10, "stress": -8}),
        ("🍺 Пиво Guinness", 250, {"health": -1, "happiness": 12, "stress": -7}),
        ("🥃 Виски Jack Daniels", 1500, {"health": -6, "happiness": 18, "stress": -15}),
        ("🍷 Вино Красное", 600, {"health": 2, "happiness": 10, "stress": -8}),
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
        ("⚡ Burn", 130, {"health": -1, "stress": -4, "intelligence": 2}),
    ],
}

TRANSPORT = {
    "bicycles": [
        ("🚲 Stels Navigator", 15000, "Велик"),
        ("🚲 Merida Big Nine", 45000, "Велик"),
    ],
    "pitbikes": [
        ("🏍️ Pitbike Kayo 125", 80000, "Питбайк"),
        ("🏍️ Pitbike BSE 140", 110000, "Питбайк"),
    ],
    "motorcycles": [
        ("🏍️ Honda CB500", 400000, "Мотоцикл"),
        ("🏍️ Yamaha R3", 550000, "Мотоцикл"),
    ],
    "cars": [
        ("🚗 Lada Granta", 700000, "Машина"),
        ("🚗 Kia Rio", 1200000, "Машина"),
        ("🚗 Toyota Camry", 2500000, "Машина"),
        ("🚗 BMW X5", 6000000, "Машина"),
        ("🚗 Tesla Model 3", 4500000, "Машина"),
    ],
}

TRAVELS = [
    ("🏡 В деревню", 5000, 1, {"happiness": 15, "stress": -20, "health": 5}),
    ("🏖️ На море", 50000, 2, {"happiness": 30, "stress": -30, "health": 10}),
    ("🏔️ В горы", 20000, 1, {"happiness": 20, "stress": -25, "health": 15}),
    ("🌆 Пентхаус вечеринка", 100000, 1, {"happiness": 50, "charisma": 15, "reputation": 10}),
    ("✈️ Европа", 150000, 3, {"happiness": 60, "charisma": 20, "intelligence": 10}),
]

FAMILY_TYPES = [
    ("💰 Богатая", "rich", 500000, 15, 20),
    ("🏠 Средняя", "medium", 50000, 5, 20),
    ("🏚️ Бедная", "poor", 5000, 0, 10),
    ("💀 Неблагополучная", "bad", 1000, -5, 40),
]

COUNTRIES = [
    ("🇷🇺 Россия", "Russia", "Москва", 50000),
    ("🇺🇸 США", "USA", "Нью-Йорк", 150000),
    ("🇯🇵 Япония", "Japan", "Токио", 100000),
    ("🇩🇪 Германия", "Germany", "Берлин", 120000),
    ("🇧🇷 Бразилия", "Brazil", "Рио", 30000),
    ("🇰🇵 КНДР", "North Korea", "Пхеньян", 5000),
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

def dict_from_row(row):
    if not row: return None
    return dict(row)

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
    elif years < 17: return "school"
    elif years < 23: 
        if user.get('university'): return "university"
        return "work"
    elif years < 60: return "adult"
    elif years < 75: return "elderly"
    else: return "old"

def get_school_grade(months):
    years = months // 12
    if years < 7: return 0
    if years >= 17: return 11
    return years - 6

def apply_effects(user_id, effects):
    if not effects: return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    if years >= 95: return True, "Естественная смерть от старости"
    if health <= 0: return True, "Смерть от болезней"
    if health <= 15 and years >= 70 and random.random() < 0.3: return True, "Осложнения от болезней"
    if user["stress"] >= 100 and health < 40 and random.random() < 0.2: return True, "Сердечный приступ"
    return False, None

def end_life(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    death_age = user["age_months"] // 12
    death_reason = "Несчастный случай"
    if user["health"] <= 0: death_reason = "Болезнь"
    elif death_age >= 95: death_reason = "Старость"
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

def get_profile_text(user):
    u = dict(user)
    age_text = get_age_text(u["age_months"])
    nick = f'\n💬 "{u["nickname"]}"' if u.get("nickname") else ""
    grade = get_school_grade(u["age_months"])
    school_text = ""
    if get_stage(u) == "school":
        school_text = f"\n🏫 {grade} класс"
    elif get_stage(u) == "university":
        school_text = f"\n🎓 {u.get('university','Универ')}"
    elif get_stage(u) == "kindergarten":
        school_text = "\n🧒 Детский сад"
    
    car_text = f"\n🚗 {u['car']}" if u.get('car') else ""
    bike_text = f"\n🏍️ {u['bike']}" if u.get('bike') else ""
    home_text = "\n🏠 Квартира" if u.get('has_apartment') else ""
    pent_text = "\n🌆 Пентхаус" if u.get('has_penthouse') else ""
    
    return f"""
👤 *{u['name']}*{nick}
📅 {u['birth_date']} | {age_text}
📍 {u['country']}, {u['city']}
🏦 Семья: {u.get('family_wealth','medium')}{school_text}
💼 {u['job'] or 'Без работы'}
{car_text}{bike_text}{home_text}{pent_text}

🧠 Интеллект: {u['intelligence']}/100
💪 Здоровье: {u['health']}/100
😎 Харизма: {u['charisma']}/100
🍀 Удача: {u['luck']}/100
💰 Деньги: {u['money']:,} ₽
😵 Стресс: {u['stress']}/100
❤️ Счастье: {u['happiness']}/100
🔥 Репутация: {u['reputation']}/100
🚔 Криминал: {u['criminal_level']}/100
"""

def get_inventory_text(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, item_type, quantity FROM inventory WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()
    conn.close()
    if not items: return "🎒 *Инвентарь пуст*"
    text = "🎒 *Инвентарь:*\n"
    for item in items:
        text += f"{item['item_name']} x{item['quantity']}\n"
    return text

# ====================== КЛАВИАТУРЫ ======================

def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Продолжить", callback_data="continue_life"),
        types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🚗 Транспорт", callback_data="transport"),
        types.InlineKeyboardButton("✈️ Путешествия", callback_data="travel"),
        types.InlineKeyboardButton("❤️ Отношения", callback_data="relationships"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("📜 Прошлые жизни", callback_data="past_lives"),
        types.InlineKeyboardButton("❌ Выход", callback_data="exit_game")
    )
    return keyboard

def life_actions_keyboard(user):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    stage = get_stage(user)
    years = user["age_months"] // 12
    
    if stage == "school":
        grade = get_school_grade(user["age_months"])
        keyboard.add(
            types.InlineKeyboardButton("📚 Уроки (1 мес)", callback_data="action_study"),
            types.InlineKeyboardButton("🏀 Физра (1 мес)", callback_data="action_sport"),
            types.InlineKeyboardButton("🚭 За школой (1 нед)", callback_data="action_skip"),
        )
        if years >= 14:
            keyboard.add(types.InlineKeyboardButton("🙏 Попросить купить", callback_data="ask_buy"))
        if years >= 15 and grade == 9:
            keyboard.add(types.InlineKeyboardButton("🎯 Выбор после 9 класса", callback_data="choose_after9"))
        if years >= 16 and grade >= 10:
            keyboard.add(types.InlineKeyboardButton("🎯 Выбор после 11", callback_data="choose_after11"))
    elif stage == "kindergarten":
        keyboard.add(
            types.InlineKeyboardButton("🧒 Садик (1 мес)", callback_data="action_kinder"),
            types.InlineKeyboardButton("🎨 Играть (1 мес)", callback_data="action_play"),
        )
    elif stage == "university":
        keyboard.add(
            types.InlineKeyboardButton("📚 Учёба (1 мес)", callback_data="action_study"),
            types.InlineKeyboardButton("🍺 Вечеринка (1 нед)", callback_data="action_party"),
            types.InlineKeyboardButton("💼 Подработка (1 мес)", callback_data="action_work"),
        )
    elif stage == "adult":
        keyboard.add(
            types.InlineKeyboardButton("💼 Работа (1 мес)", callback_data="action_work"),
            types.InlineKeyboardButton("🏋️ Спорт (1 мес)", callback_data="action_sport"),
            types.InlineKeyboardButton("🎉 Тусовка (1 нед)", callback_data="action_party"),
        )
        if years < 23:
            keyboard.add(types.InlineKeyboardButton("🎓 Поступить", callback_data="try_university"))
    elif stage == "baby":
        keyboard.add(types.InlineKeyboardButton("👶 Расти (1 мес)", callback_data="action_baby"))
    
    keyboard.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏠 Меню", callback_data="main_menu")
    )
    return keyboard

def ask_buy_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🍺 Пиво", callback_data="ask_alcohol"),
        types.InlineKeyboardButton("🚬 Сигареты", callback_data="ask_cigarettes"),
        types.InlineKeyboardButton("💨 Вейп", callback_data="ask_vape"),
        types.InlineKeyboardButton("⚡ Энергетик", callback_data="ask_energy"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    return keyboard

# ====================== ОБРАБОТЧИКИ ======================

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user = get_db_user(user_id)
    
    if user and user["is_alive"] == 1:
        bot.send_message(user_id, f"👋 С возвращением, {user['name']}!", reply_markup=main_menu_keyboard())
    else:
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
        types.InlineKeyboardButton("🎲 Случайное", callback_data="name_random")
    )
    bot.edit_message_text("✏️ Выбери имя:", user_id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("name_"))
def choose_name(call):
    user_id = call.from_user.id
    choice = call.data.split("_")[1]
    
    if choice == "random":
        gender = user_temp[user_id]["gender"]
        names_m = ["Александр","Дмитрий","Максим","Иван","Сергей","Артём"]
        names_f = ["Анна","Мария","Елена","Ольга","Екатерина","Анастасия"]
        user_temp[user_id]["name"] = random.choice(names_m if gender == "male" else names_f)
        ask_nickname(call)
    else:
        msg = bot.edit_message_text("✏️ Отправь имя:", user_id, call.message.message_id)
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
    bot.edit_message_text("💬 Прозвище?", call.from_user.id, call.message.message_id, reply_markup=keyboard)

def ask_nickname_by_message(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✏️ Ввести", callback_data="nick_choose"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="nick_skip")
    )
    bot.send_message(message.from_user.id, "💬 Прозвище?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("nick_"))
def choose_nickname(call):
    user_id = call.from_user.id
    if call.data == "nick_skip":
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
    bot.edit_message_text("🏠 Семья:", call.from_user.id, call.message.message_id, reply_markup=keyboard)

def ask_family_by_message(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, ftype, _, _, _ in FAMILY_TYPES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"family_{ftype}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="family_random"))
    bot.send_message(message.from_user.id, "🏠 Семья:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("family_"))
def choose_family(call):
    user_id = call.from_user.id
    ftype = call.data.split("_")[1]
    fam = random.choice(FAMILY_TYPES) if ftype == "random" else next((f for f in FAMILY_TYPES if f[1] == ftype), FAMILY_TYPES[1])
    
    user_temp[user_id].update({"family_wealth": fam[1], "money": fam[2], "luck": fam[3], "stress": fam[4]})
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _ in COUNTRIES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"country_{code}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="country_random"))
    bot.edit_message_text("🌍 Страна:", user_id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def choose_country(call):
    user_id = call.from_user.id
    code = call.data.split("_")[1]
    country = random.choice(COUNTRIES) if code == "random" else next((c for c in COUNTRIES if c[1] == code), COUNTRIES[0])
    
    data = user_temp[user_id]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    birth_date = (datetime.now() - timedelta(days=random.randint(0, 365*18))).strftime("%d.%m.%Y")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, gender, birth_date, country, city, name, nickname,
         family_wealth, age_months, intelligence, health, charisma, luck, money, stress,
         happiness, reputation, criminal_level, education, university, job, car, bike,
         has_apartment, has_penthouse, is_alive, game_stage, extra_weeks, last_event_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,0,30,80,30,?,?,?,60,50,0,'','','','','',0,0,1,'baby',0,'')
    ''', (user_id, call.from_user.username or "", call.from_user.first_name or "", data["gender"],
          birth_date, country[0], country[2], data.get("name","Персонаж"), data.get("nickname",""),
          data.get("family_wealth","medium"), data.get("luck",30), data.get("money",50000), data.get("stress",20)))
    
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    if user_id in user_temp: del user_temp[user_id]
    
    bot.edit_message_text(
        f"🎉 *Рождение!*\n\n👶 {user['name']} '{user['nickname']}'\n📅 {birth_date}\n📍 {country[0]}, {country[2]}\n🏦 {user['family_wealth']}\n💰 {user['money']:,} ₽",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "continue_life")
def continue_life(call):
    user = get_db_user(call.from_user.id)
    if not user or user["is_alive"] != 1:
        bot.answer_callback_query(call.id, "Нет активной жизни!")
        return
    bot.edit_message_text(get_profile_text(user), call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def player_action(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    if not user or user["is_alive"] != 1: return
    
    action = call.data.split("_")[1]
    effects = {}
    title = desc = ""
    months = 0
    weeks = 0
    
    if action == "study":
        months = 1
        effects = {"intelligence": random.randint(5,15), "stress": random.randint(3,8)}
        title, desc = "📚 Учёба", "Месяц усердной учёбы!"
    elif action == "sport":
        months = 1
        effects = {"health": random.randint(5,15), "stress": -5, "happiness": 5}
        title, desc = "🏋️ Спорт", "Месяц тренировок!"
    elif action == "work":
        months = 1
        salary = random.randint(10000, 50000)
        effects = {"money": salary, "stress": random.randint(5,15), "intelligence": 2}
        title, desc = "💼 Работа", f"Заработал {salary:,} ₽"
    elif action == "party":
        weeks = 1
        effects = {"happiness": random.randint(10,25), "stress": -10, "health": -3, "money": -random.randint(1000,5000)}
        title, desc = "🎉 Тусовка", "Неделя веселья!"
    elif action == "skip":
        weeks = 1
        effects = {"happiness": 5, "stress": -5, "reputation": -5}
        title, desc = "🚭 За школой", "Прогулял неделю..."
    elif action == "play":
        months = 1
        effects = {"happiness": 10, "stress": -5}
        title, desc = "🎨 Игры", "Месяц игр и веселья!"
    elif action == "kinder":
        months = 1
        effects = {"intelligence": 5, "charisma": 3, "happiness": 5}
        title, desc = "🧒 Детский сад", "Месяц в садике!"
    elif action == "baby":
        months = 1
        effects = {"health": 5}
        title, desc = "👶 Растём", "Малыш подрос!"
    
    # Применяем время
    if months:
        add_months(user_id, months)
    elif weeks:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET extra_weeks = extra_weeks + ? WHERE user_id = ?", (weeks, user_id))
        # Каждые 4 недели = 1 месяц
        cursor.execute("UPDATE users SET age_months = age_months + extra_weeks / 4, extra_weeks = extra_weeks % 4 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    changes = apply_effects(user_id, effects)
    user = get_db_user(user_id)
    
    # Проверка смерти
    is_dead, reason = check_death(user)
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(
            f"💀 *Ты умер!*\nВозраст: {death_age} лет\nПричина: {death_reason}\nРейтинг: *{rank}*",
            user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return
    
    change_text = "\n".join(changes) if changes else "Без изменений"
    bot.edit_message_text(
        f"*{title}*\n{desc}\n\n📊 *Изменения:*\n{change_text}\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))

# Магазин и быстрые действия
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
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    bot.edit_message_text(f"🛒 *Магазин*\n💰 {user['money']:,} ₽", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    user = get_db_user(call.from_user.id)
    category = call.data.split("_")[1]
    items = SHOP_ITEMS.get(category, [])
    years = user["age_months"] // 12
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, _ in items:
        if category in ["alcohol","cigarettes","vape"] and years < 18:
            keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽ 🔞", callback_data=f"underage_{category}_{name}"))
        else:
            keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽", callback_data=f"buy_{category}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="shop"))
    bot.edit_message_text("🛒 *Товары:*", call.from_user.id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("underage_"))
def underage_buy(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    user_temp[user_id] = {"ask_category": category, "ask_item": item_name}
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🧑 Друга (70%)", callback_data="ask_friend"),
        types.InlineKeyboardButton("👨 Брата (50%)", callback_data="ask_brother"),
        types.InlineKeyboardButton("🕵️ Самому (40%)", callback_data="ask_myself"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="shop")
    )
    bot.edit_message_text("🙏 Кого попросить купить?", user_id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_"))
def ask_person(call):
    user_id = call.from_user.id
    person = call.data.split("_")[1]
    data = user_temp.get(user_id, {})
    
    if not data:
        bot.answer_callback_query(call.id, "Ошибка!")
        return
    
    items = SHOP_ITEMS.get(data["ask_category"], [])
    item = next((i for i in items if i[0] == data["ask_item"]), None)
    if not item: return
    
    name, price, effects = item
    user = get_db_user(user_id)
    
    chances = {"friend": 70, "brother": 50, "myself": 40}
    chance = chances.get(person, 50)
    
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает денег! Нужно {price} ₽")
        return
    
    if random.randint(1, 100) <= chance:
        changes = apply_effects(user_id, {"money": -price})
        changes2 = apply_effects(user_id, effects)
        apply_effects(user_id, {"reputation": -3})
        bot.edit_message_text(
            f"✅ Получил {name}!\n\n📊 Изменения:\n" + "\n".join(changes + changes2),
            user_id, call.message.message_id, parse_mode="Markdown",
            reply_markup=life_actions_keyboard(get_db_user(user_id)))
    else:
        apply_effects(user_id, {"stress": 10, "happiness": -5})
        if person == "brother":
            apply_effects(user_id, {"stress": 15})
            text = "👨 Брат отказал и рассказал родителям! 😡"
        elif person == "myself":
            apply_effects(user_id, {"criminal_level": 5})
            text = "🕵️ Тебя спалили! Вызвали родителей в школу!"
        else:
            text = "🧑 Друг отказался помогать..."
        bot.edit_message_text(f"❌ {text}\n\n{get_profile_text(get_db_user(user_id))}",
                             user_id, call.message.message_id, parse_mode="Markdown",
                             reply_markup=life_actions_keyboard(get_db_user(user_id)))
    
    if user_id in user_temp: del user_temp[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    items = SHOP_ITEMS.get(category, [])
    item = next((i for i in items if i[0] == item_name), None)
    if not item: return
    
    name, price, effects = item
    user = get_db_user(user_id)
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает денег! Нужно {price} ₽")
        return
    
    changes = apply_effects(user_id, {"money": -price})
    changes2 = apply_effects(user_id, effects)
    
    # Добавляем в инвентарь
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, name))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE inventory SET quantity = quantity + 1 WHERE id = ?", (existing[0],))
    else:
        cursor.execute("INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?,?,?,1)", (user_id, name, category))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(
        f"✅ Куплено: {name}\n\n📊 Изменения:\n" + "\n".join(changes + changes2) + f"\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "inventory")
def show_inventory(call):
    user = get_db_user(call.from_user.id)
    if not user: return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (call.from_user.id,))
    items = cursor.fetchall()
    conn.close()
    
    for item in items:
        keyboard.add(types.InlineKeyboardButton(f"{item['item_name']} (x{item['quantity']})", callback_data=f"use_{item['id']}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    
    bot.edit_message_text(get_inventory_text(call.from_user.id), call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("use_"))
def use_item(call):
    user_id = call.from_user.id
    item_id = int(call.data.split("_")[1])
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ? AND user_id = ?", (item_id, user_id))
    item = cursor.fetchone()
    
    if not item:
        bot.answer_callback_query(call.id, "Предмет не найден")
        conn.close()
        return
    
    # Эффекты от использования
    item_effects = {
        "🍔 Бургер": {"health": 2, "happiness": 5, "stress": -3},
        "🍕 Пицца": {"health": -2, "happiness": 10, "stress": -5},
        "🍺 Пиво Baltika 7": {"health": -3, "happiness": 8, "stress": -10},
        "🚬 Winston XStyle": {"health": -5, "stress": -10, "happiness": 3},
        "💨 HQD Cuvie Plus": {"health": -3, "stress": -15, "happiness": 10},
        "⚡ Red Bull": {"health": -2, "stress": -5, "intelligence": 3},
    }
    
    effects = item_effects.get(item["item_name"], {"happiness": 5})
    changes = apply_effects(user_id, effects)
    
    if item["quantity"] > 1:
        cursor.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = ?", (item_id,))
    else:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(
        f"✅ Использовал: {item['item_name']}\n\n📊 Изменения:\n" + "\n".join(changes) + f"\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

# Транспорт и путешествия
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
    cat = call.data.split("_")[1]
    items = TRANSPORT.get(cat, [])
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, vtype in items:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽", callback_data=f"buyveh_{vtype}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="transport"))
    bot.edit_message_text("🚗 *Выбери:*", call.from_user.id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyveh_"))
def buy_vehicle(call):
    user_id = call.from_user.id
    user = get_db_user(user_id)
    parts = call.data.split("_")
    vtype = parts[1]
    vname = "_".join(parts[2:])
    
    all_vehicles = [v for values in TRANSPORT.values() for v in values]
    vehicle = next((v for v in all_vehicles if v[0] == vname), None)
    if not vehicle: return
    
    name, price, _ = vehicle
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает {price:,} ₽")
        return
    
    add_months(user_id, 1)
    apply_effects(user_id, {"money": -price, "happiness": 10})
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if vtype == "Машина":
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
    for name, price, months, _ in TRAVELS:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽ ({months} мес)", callback_data=f"travelgo_{name}"))
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
    
    name, price, months, effects = travel
    if user["money"] < price:
        bot.answer_callback_query(call.id, f"Не хватает {price:,} ₽")
        return
    
    add_months(user_id, months)
    changes = apply_effects(user_id, {"money": -price})
    changes2 = apply_effects(user_id, effects)
    
    user = get_db_user(user_id)
    bot.edit_message_text(
        f"✈️ *{name}*\nОтлично отдохнул!\n\n📊 Изменения:\n" + "\n".join(changes + changes2) + f"\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))

# Выбор после школы
@bot.callback_query_handler(func=lambda call: call.data == "choose_after9")
def choose_after9(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🎓 10 класс", callback_data="go_10grade"),
        types.InlineKeyboardButton("🔧 Колледж", callback_data="go_college"),
        types.InlineKeyboardButton("💼 Работать", callback_data="go_work"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    bot.edit_message_text("🎯 *После 9 класса:*", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "choose_after11" or call.data == "try_university")
def choose_after11(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🎓 Универ", callback_data="go_university"),
        types.InlineKeyboardButton("🔧 Колледж", callback_data="go_college"),
        types.InlineKeyboardButton("🪖 Армия", callback_data="go_army"),
        types.InlineKeyboardButton("💼 Работать", callback_data="go_work"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    bot.edit_message_text("🎯 *После 11 класса:*", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("go_"))
def life_choice(call):
    user_id = call.from_user.id
    choice = call.data.split("_")[1]
    user = get_db_user(user_id)
    
    if choice == "10grade":
        add_months(user_id, 12)
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("UPDATE users SET education = '10 класс' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        text = "✅ Пошёл в 10 класс!"
    elif choice == "college":
        add_months(user_id, 36)
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("UPDATE users SET education = 'Колледж' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        text = "✅ Поступил в колледж! +3 года"
    elif choice == "university":
        if user["intelligence"] >= 60:
            add_months(user_id, 48)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET education = 'Высшее', university = ? WHERE user_id = ?", 
                         (random.choice(["МГУ","СПбГУ","ВШЭ","МФТИ"]), user_id))
            conn.commit()
            conn.close()
            text = "✅ Поступил на бюджет! +4 года"
        elif user["intelligence"] >= 40:
            if user["money"] >= 200000:
                add_months(user_id, 48)
                apply_effects(user_id, {"money": -200000})
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("UPDATE users SET education = 'Высшее', university = 'Платный ВУЗ' WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                text = "✅ Поступил платно (-200,000 ₽) +4 года"
            else:
                text = "❌ Нет денег на платное!"
        else:
            text = "❌ Не поступил. Интеллект слишком низкий."
    elif choice == "army":
        add_months(user_id, 12)
        apply_effects(user_id, {"health": 15, "stress": 10, "intelligence": -5})
        text = "🪖 Отслужил в армии! +1 год"
    elif choice == "work":
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("UPDATE users SET job = 'Рабочий', education = 'Школа' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        text = "💼 Пошёл работать!"
    
    user = get_db_user(user_id)
    bot.edit_message_text(f"{text}\n\n{get_profile_text(user)}",
                         user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(user))

# Профиль, меню
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user = get_db_user(call.from_user.id)
    if not user: return
    bot.edit_message_text(get_profile_text(user), call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=life_actions_keyboard(user))

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def return_to_menu(call):
    user = get_db_user(call.from_user.id)
    if user and user["is_alive"] == 1:
        text = f"🏠 *Главное меню*\n\n{get_profile_text(user)}"
    else:
        text = "🏠 *Главное меню*\n\nНачни новую жизнь!"
    bot.edit_message_text(text, call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "past_lives")
def show_past_lives(call):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_lives WHERE user_id = ? ORDER BY life_number DESC LIMIT 5", (call.from_user.id,))
    lives = cursor.fetchall()
    conn.close()
    text = "\n\n".join([f"#{l['life_number']} | {l['country']}\n{l['death_age']} лет | {l['death_reason']}\nРейтинг: *{l['life_rank']}* | 💰 {l['money']:,} ₽" for l in lives]) if lives else "Нет прошлых жизней"
    bot.edit_message_text(f"📜 *Прошлые жизни:*\n\n{text}", call.from_user.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data in ["relationships","business","jail_status","exit_game","new_life"])
def stub_menus(call):
    user = get_db_user(call.from_user.id)
    if call.data == "new_life":
        if user and user["is_alive"] == 1: end_life(user)
        user_temp[call.from_user.id] = {}
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
                     types.InlineKeyboardButton("👩 Женский", callback_data="gender_female"))
        bot.edit_message_text("🌟 *Новая жизнь!*", call.from_user.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=keyboard)
    elif call.data == "exit_game":
        bot.edit_message_text("👋 До встречи!", call.from_user.id, call.message.message_id)
    else:
        texts = {"relationships":"❤️ *Отношения*\nВ разработке","business":"💰 *Бизнес*\nВ разработке","jail_status":"🚔 *Тюрьма*\nНа свободе!"}
        bot.edit_message_text(texts.get(call.data,""), call.from_user.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "ask_buy")
def ask_buy_menu(call):
    bot.edit_message_text("🙏 Что хочешь попросить?", call.from_user.id, call.message.message_id,
                         reply_markup=ask_buy_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_") and call.data in ["ask_alcohol","ask_cigarettes","ask_vape","ask_energy"])
def ask_buy_category(call):
    user_id = call.from_user.id
    category = call.data.split("_")[1]
    items = SHOP_ITEMS.get(category, [])
    user_temp[user_id] = {"ask_category": category}
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, _ in items:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽", callback_data=f"underage_{category}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="ask_buy"))
    bot.edit_message_text("🙏 Что попросить?", user_id, call.message.message_id, reply_markup=keyboard)

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.remove_webhook()
    bot.infinity_polling()
