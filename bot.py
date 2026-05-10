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

# Антифлуд: задержка между запросами
REQUEST_DELAY = 0.1

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
last_request_time = {}

def anti_flood(user_id):
    now = time.time()
    if user_id in last_request_time:
        elapsed = now - last_request_time[user_id]
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
    last_request_time[user_id] = time.time()

# ====================== ДАННЫЕ ИГРЫ ======================

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
    ("🔪 Криминальный талант", "criminal", {"criminal_level": 10, "luck": 5}),
    ("🎨 Творческий", "creative", {"charisma": 10, "happiness": 10}),
]

APPEARANCES = [
    ("😍 Красавчик (+харизма)", "handsome", {"charisma": 15}),
    ("😐 Обычный", "normal", {}),
    ("😨 Страшный (-харизма, +стресс)", "ugly", {"charisma": -10, "stress": 10}),
]

SHOP_ITEMS = {
    "food": [
        ("🍔 Бургер", 200, {"health": 2, "happiness": 5, "stress": -3}),
        ("🍕 Пицца", 500, {"health": -2, "happiness": 10, "stress": -5}),
        ("🥗 Салат", 300, {"health": 5, "happiness": 2, "stress": -2}),
        ("🍜 Доширак", 59, {"health": -1, "happiness": -2, "stress": 2}),
        ("🌭 Хот-дог", 150, {"health": -1, "happiness": 3, "stress": -1}),
        ("🍣 Роллы", 450, {"health": 3, "happiness": 8, "stress": -4}),
    ],
    "alcohol": [
        ("🍺 Балтика 7 0.5", 89, {"health": -3, "happiness": 8, "stress": -10}),
        ("🍺 Heineken 0.5", 129, {"health": -2, "happiness": 10, "stress": -8}),
        ("🍺 Corona Extra 0.33", 179, {"health": -1, "happiness": 12, "stress": -7}),
        ("🥃 Jack Daniels 0.5", 1499, {"health": -6, "happiness": 18, "stress": -15}),
        ("🥃 Red Label 0.5", 1299, {"health": -5, "happiness": 16, "stress": -14}),
        ("🍷 Крымское вино 0.7", 399, {"health": 2, "happiness": 10, "stress": -8}),
        ("🍾 Шампанское 0.75", 499, {"health": -1, "happiness": 15, "stress": -10}),
    ],
    "cigarettes": [
        ("🚬 Winston XStyle", 179, {"health": -5, "stress": -10, "happiness": 3}),
        ("🚬 Marlboro Gold", 219, {"health": -4, "stress": -12, "happiness": 4}),
        ("🚬 Parliament Aqua Blue", 249, {"health": -3, "stress": -13, "happiness": 5}),
        ("🚬 Lucky Strike", 159, {"health": -6, "stress": -8, "happiness": 2}),
        ("🚬 Chapman", 139, {"health": -7, "stress": -7, "happiness": 1}),
    ],
    "vape": [
        ("💨 HQD Cuvie Plus", 599, {"health": -3, "stress": -15, "happiness": 10}),
        ("💨 Elf Bar 1500", 799, {"health": -2, "stress": -18, "happiness": 12}),
        ("💨 Vaporesso XROS 3", 1499, {"health": -1, "stress": -20, "happiness": 15}),
        ("💨 JUUL", 1199, {"health": -2, "stress": -16, "happiness": 11}),
        ("💨 SOAK", 449, {"health": -4, "stress": -10, "happiness": 5}),
        ("💨 Pons", 699, {"health": -3, "stress": -14, "happiness": 9}),
    ],
    "energy": [
        ("⚡ Red Bull 0.25", 149, {"health": -2, "stress": -5, "intelligence": 3}),
        ("⚡ Monster 0.5", 169, {"health": -3, "stress": -7, "intelligence": 5}),
        ("⚡ Burn 0.33", 129, {"health": -1, "stress": -4, "intelligence": 2}),
        ("⚡ Adrenaline Rush 0.25", 99, {"health": -2, "stress": -3, "intelligence": 1}),
        ("⚡ Gorilla 0.5", 139, {"health": -3, "stress": -6, "intelligence": 4}),
    ],
}

TRANSPORT = {
    "bicycles": [
        ("🚲 Stels Navigator 500", 15000, "Велик"),
        ("🚲 Merida Big Nine", 45000, "Велик"),
        ("🚲 Trek Marlin 5", 70000, "Велик"),
    ],
    "pitbikes": [
        ("🏍️ Kayo Basic 125", 80000, "Питбайк"),
        ("🏍️ BSE J2 140", 110000, "Питбайк"),
        ("🏍️ Apollo RFZ 160", 150000, "Питбайк"),
    ],
    "motorcycles": [
        ("🏍️ Honda CB500F", 450000, "Мотоцикл"),
        ("🏍️ Yamaha R3", 550000, "Мотоцикл"),
        ("🏍️ Kawasaki Ninja 650", 750000, "Мотоцикл"),
        ("🏍️ Harley-Davidson Sportster S", 1200000, "Мотоцикл"),
    ],
    "cars": [
        ("🚗 LADA Granta", 700000, "Машина"),
        ("🚗 Kia Rio X", 1200000, "Машина"),
        ("🚗 Hyundai Solaris", 1500000, "Машина"),
        ("🚗 Toyota Camry", 2800000, "Машина"),
        ("🚗 BMW X5", 7500000, "Машина"),
        ("🚗 Mercedes-Benz S500", 15000000, "Машина"),
        ("🚗 Porsche 911 Carrera", 11000000, "Машина"),
        ("🚗 Tesla Model 3", 4990000, "Машина"),
    ],
}

TRAVELS = [
    ("🏡 В деревню к бабушке", 5000, 1, {"happiness": 15, "stress": -20, "health": 5}),
    ("🏖️ На море (Сочи)", 50000, 2, {"happiness": 30, "stress": -30, "health": 10, "charisma": 5}),
    ("🏔️ В горы (Алтай)", 35000, 1, {"happiness": 20, "stress": -25, "health": 15}),
    ("🌆 Пентхаус пати (Москва-Сити)", 150000, 1, {"happiness": 50, "charisma": 15, "reputation": 10}),
    ("✈️ Турция all inclusive", 120000, 2, {"happiness": 55, "stress": -35, "health": 5, "charisma": 10}),
    ("✈️ Европа (Париж)", 200000, 3, {"happiness": 60, "charisma": 20, "intelligence": 10}),
    ("🎰 Вегас", 500000, 2, {"happiness": 70, "money": random.randint(-500000, 1000000), "stress": -20}),
]

FAMILY_TYPES = [
    ("💰 Богатая (500к старт)", "rich", 500000, 15, 20),
    ("🏠 Средняя (50к старт)", "medium", 50000, 5, 15),
    ("🏚️ Бедная (5к старт)", "poor", 5000, 0, 10),
    ("💀 Детдом (0 старт)", "orphanage", 0, -10, 30),
    ("🚔 Криминальная (100к, риск)", "criminal", 100000, -5, 35),
]

COUNTRIES = [
    ("🇷🇺 Россия", "Russia", "Москва", 50000),
    ("🇺🇸 США", "USA", "Нью-Йорк", 150000),
    ("🇯🇵 Япония", "Japan", "Токио", 100000),
    ("🇩🇪 Германия", "Germany", "Берлин", 120000),
    ("🇧🇷 Бразилия", "Brazil", "Рио", 30000),
    ("🇰🇵 КНДР", "North Korea", "Пхеньян", 5000),
    ("🇨🇳 Китай", "China", "Пекин", 80000),
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
    if years == 0:
        return f"{m} мес."
    elif years < 3:
        return f"{years} г. {m} мес."
    else:
        return f"{years} лет"

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
    user = get_db_user(user_id)
    difficulty = user["difficulty"] if user else "normal"
    diff_data = next((d for d in DIFFICULTIES if d[1] == difficulty), DIFFICULTIES[1])
    money_mult = diff_data[2]
    stress_mult = diff_data[4]
    
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
            elif col == "stress":
                delta = int(delta * stress_mult)
                cursor.execute(f"UPDATE users SET {col} = MAX(0, MIN(100, {col} + ?)) WHERE user_id = ?", (delta, user_id))
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
    difficulty = user.get("difficulty", "normal")
    
    if difficulty == "realism":
        if health <= 20: return True, "Осложнения (реализм)"
        if years >= 80: return True, "Старость (реализм)"
    else:
        if years >= 95: return True, "Естественная смерть от старости"
    
    if health <= 0: return True, "Смерть от болезней"
    if health <= 10 and years >= 70 and random.random() < 0.3: return True, "Осложнения от болезней"
    if user["stress"] >= 100 and health < 40 and random.random() < 0.2: return True, "Сердечный приступ"
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

def get_profile_text(user):
    u = dict(user)
    age_text = get_age_text(u["age_months"])
    nick = f'\n💬 "{u["nickname"]}"' if u.get("nickname") else ""
    diff = f'\n🎮 Сложность: {u.get("difficulty","normal")}'
    tal = f'\n⭐ Талант: {u.get("talent","")}' if u.get("talent") else ""
    app = f'\n👤 Внешность: {u.get("appearance","")}' if u.get("appearance") else ""
    
    stage = get_stage(user)
    ed_text = ""
    if stage == "school":
        grade = get_school_grade(u["age_months"])
        ed_text = f"\n🏫 {grade} класс"
    elif stage == "university":
        ed_text = f"\n🎓 {u.get('university','Универ')}"
    elif stage == "kindergarten":
        ed_text = "\n🧒 Детский сад"
    
    car_text = f"\n🚗 {u['car']}" if u.get('car') else ""
    bike_text = f"\n🏍️ {u['bike']}" if u.get('bike') else ""
    home_text = "\n🏠 Квартира" if u.get('has_apartment') else ""
    pent_text = "\n🌆 Пентхаус" if u.get('has_penthouse') else ""
    army_text = "\n🎖️ Служил" if u.get('army_served') else ""
    
    return f"""
👤 *{u['name']}*{nick}{diff}{tal}{app}
📅 {u['birth_date']} | {age_text}
📍 {u['country']}, {u['city']}
🏦 Семья: {u.get('family_wealth','medium')}{ed_text}
💼 {u['job'] or 'Без работы'} | 💰 {u.get('salary',0):,} ₽/мес
{car_text}{bike_text}{home_text}{pent_text}{army_text}

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
    cursor.execute("SELECT id, item_name, item_type, quantity FROM inventory WHERE user_id = ?", (user_id,))
    items = cursor.fetchall()
    conn.close()
    if not items: return "🎒 *Инвентарь пуст*"
    text = "🎒 *Инвентарь:*\n"
    for item in items:
        text += f"{item['item_name']} x{item['quantity']} [ID:{item['id']}]\n"
    return text

# ====================== КЛАВИАТУРЫ ======================

def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("▶️ Продолжить жизнь", callback_data="continue_life"),
        types.InlineKeyboardButton("🆕 Новая жизнь", callback_data="new_life"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🚗 Транспорт", callback_data="transport"),
        types.InlineKeyboardButton("✈️ Путешествия", callback_data="travel"),
        types.InlineKeyboardButton("❤️ Отношения", callback_data="relationships"),
        types.InlineKeyboardButton("💰 Бизнес", callback_data="business"),
        types.InlineKeyboardButton("🚔 Криминал", callback_data="crime_menu"),
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
        if grade == 9 and years >= 15:
            keyboard.add(types.InlineKeyboardButton("📝 Сдать ОГЭ", callback_data="exam_oge"))
        if grade >= 10 and years >= 17:
            keyboard.add(types.InlineKeyboardButton("📝 Сдать ЕГЭ", callback_data="exam_ege"))
        if years >= 12:
            keyboard.add(types.InlineKeyboardButton("🔪 АУЕ тема", callback_data="crime_au"))
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
        if years >= 18 and not user.get("military_category"):
            keyboard.add(types.InlineKeyboardButton("🎖️ Военкомат", callback_data="military_office"))
    elif stage == "adult" or stage == "work":
        keyboard.add(
            types.InlineKeyboardButton("💼 Работа (1 мес)", callback_data="action_work"),
            types.InlineKeyboardButton("🏋️ Спорт (1 мес)", callback_data="action_sport"),
            types.InlineKeyboardButton("🎉 Тусовка (1 нед)", callback_data="action_party"),
            types.InlineKeyboardButton("📚 Саморазвитие (1 мес)", callback_data="action_study"),
        )
        if years >= 18 and not user.get("army_served") and user.get("gender") == "male":
            keyboard.add(types.InlineKeyboardButton("🎖️ Военкомат", callback_data="military_office"))
    elif stage == "baby":
        keyboard.add(types.InlineKeyboardButton("👶 Расти (1 мес)", callback_data="action_baby"))
    
    keyboard.add(
        types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory_use"),
        types.InlineKeyboardButton("📊 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏠 Меню", callback_data="main_menu")
    )
    return keyboard

# ====================== ОБРАБОТЧИКИ КОМАНД ======================

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
    bot.edit_message_text("✏️ Выбери имя персонажа:", user_id, call.message.message_id, reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("name_"))
def choose_name(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    choice = call.data.split("_")[1]
    
    if choice == "random":
        gender = user_temp[user_id]["gender"]
        names_m = ["Александр","Дмитрий","Максим","Иван","Сергей","Артём","Денис"]
        names_f = ["Анна","Мария","Елена","Ольга","Екатерина","Анастасия","Дарья"]
        user_temp[user_id]["name"] = random.choice(names_m if gender == "male" else names_f)
        user_temp[user_id]["step"] = "nickname"
        ask_nickname(call)
    else:
        user_temp[user_id]["step"] = "name_input"
        msg = bot.edit_message_text("✏️ Отправь имя (текстом):", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_name)
    time.sleep(REQUEST_DELAY)

def process_name(message):
    user_id = message.from_user.id
    user_temp[user_id]["name"] = message.text
    user_temp[user_id]["step"] = "nickname"
    ask_nickname_by_message(message)

def ask_nickname(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✏️ Ввести прозвище", callback_data="nick_choose"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="nick_skip")
    )
    bot.edit_message_text("💬 Ласковое прозвище?", call.from_user.id, call.message.message_id, reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

def ask_nickname_by_message(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✏️ Ввести прозвище", callback_data="nick_choose"),
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="nick_skip")
    )
    bot.send_message(message.from_user.id, "💬 Ласковое прозвище?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("nick_"))
def choose_nickname(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    if call.data == "nick_skip":
        user_temp[user_id]["nickname"] = ""
        user_temp[user_id]["step"] = "difficulty"
        choose_difficulty_menu(call)
    else:
        user_temp[user_id]["step"] = "nickname_input"
        msg = bot.edit_message_text("✏️ Отправь прозвище:", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_nickname)
    time.sleep(REQUEST_DELAY)

def process_nickname(message):
    user_id = message.from_user.id
    user_temp[user_id]["nickname"] = message.text
    user_temp[user_id]["step"] = "difficulty"
    choose_difficulty_menu(message)

def choose_difficulty_menu(source):
    user_id = source.from_user.id if hasattr(source, 'from_user') else source.chat.id
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _, _ in DIFFICULTIES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"diff_{code}"))
    
    if hasattr(source, 'message'):
        bot.send_message(user_id, "🎮 *Выбери сложность:*", parse_mode="Markdown", reply_markup=keyboard)
    else:
        bot.edit_message_text("🎮 *Выбери сложность:*", user_id, source.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("diff_"))
def choose_difficulty(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    code = call.data.split("_")[1]
    user_temp[user_id]["difficulty"] = code
    user_temp[user_id]["step"] = "talent"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, tcode, _ in TALENTS:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"talent_{tcode}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайный", callback_data="talent_random"))
    
    bot.edit_message_text("⭐ *Выбери талант:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("talent_"))
def choose_talent(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    tcode = call.data.split("_")[1]
    if tcode == "random":
        talent = random.choice(TALENTS)
    else:
        talent = next((t for t in TALENTS if t[1] == tcode), TALENTS[1])
    user_temp[user_id]["talent"] = talent[1]
    user_temp[user_id]["talent_effects"] = talent[2]
    user_temp[user_id]["step"] = "appearance"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, acode, _ in APPEARANCES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"appearance_{acode}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайная", callback_data="appearance_random"))
    
    bot.edit_message_text("👤 *Выбери внешность:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("appearance_"))
def choose_appearance(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    acode = call.data.split("_")[1]
    if acode == "random":
        app = random.choice(APPEARANCES)
    else:
        app = next((a for a in APPEARANCES if a[1] == acode), APPEARANCES[1])
    user_temp[user_id]["appearance"] = app[1]
    user_temp[user_id]["appearance_effects"] = app[2]
    user_temp[user_id]["step"] = "family"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, ftype, _, _, _ in FAMILY_TYPES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"family_{ftype}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="family_random"))
    
    bot.edit_message_text("🏠 *Выбери семью:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("family_"))
def choose_family(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    ftype = call.data.split("_")[1]
    fam = random.choice(FAMILY_TYPES) if ftype == "random" else next((f for f in FAMILY_TYPES if f[1] == ftype), FAMILY_TYPES[1])
    
    user_temp[user_id]["family_wealth"] = fam[1]
    user_temp[user_id]["money"] = fam[2]
    user_temp[user_id]["luck"] = fam[3]
    user_temp[user_id]["stress"] = fam[4]
    user_temp[user_id]["step"] = "country"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for name, code, _, _ in COUNTRIES:
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"country_{code}"))
    keyboard.add(types.InlineKeyboardButton("🎲 Случайно", callback_data="country_random"))
    
    bot.edit_message_text("🌍 *Страна рождения:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def choose_country(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    code = call.data.split("_")[1]
    country = random.choice(COUNTRIES) if code == "random" else next((c for c in COUNTRIES if c[1] == code), COUNTRIES[0])
    
    data = user_temp[user_id]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    birth_date = (datetime.now() - timedelta(days=random.randint(0, 365*18))).strftime("%d.%m.%Y")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, gender, birth_date, country, city, name, nickname,
         family_wealth, difficulty, talent, appearance, age_months, intelligence, health, 
         charisma, luck, money, stress, happiness, reputation, criminal_level, 
         education, university, job, car, bike, has_apartment, has_penthouse, 
         army_served, is_alive, game_stage, extra_weeks, last_event_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,30,80,30,?,?,?,60,50,0,'','','','','',0,0,0,1,'baby',0,'')
    ''', (user_id, call.from_user.username or "", call.from_user.first_name or "", data["gender"],
          birth_date, country[0], country[2], data.get("name","Персонаж"), data.get("nickname",""),
          data.get("family_wealth","medium"), data.get("difficulty","normal"),
          data.get("talent",""), data.get("appearance",""),
          data.get("luck",30), data.get("money",50000), data.get("stress",20)))
    
    conn.commit()
    conn.close()
    
    # Применяем эффекты таланта и внешности
    user = get_db_user(user_id)
    if data.get("talent_effects"):
        apply_effects(user_id, data["talent_effects"])
    if data.get("appearance_effects"):
        apply_effects(user_id, data["appearance_effects"])
    
    user = get_db_user(user_id)
    if user_id in user_temp: del user_temp[user_id]
    
    bot.edit_message_text(
        f"🎉 *Рождение!*\n\n👶 {user['name']} '{user['nickname']}'\n📅 {birth_date}\n"
        f"📍 {country[0]}, {country[2]}\n🏦 Семья: {user['family_wealth']}\n"
        f"🎮 Сложность: {user['difficulty']}\n⭐ Талант: {user['talent']}\n"
        f"💰 {user['money']:,} ₽\n\nТвоя история начинается!",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

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
    
    if months:
        add_months(user_id, months)
    elif weeks:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET extra_weeks = extra_weeks + ? WHERE user_id = ?", (weeks, user_id))
        cursor.execute("UPDATE users SET age_months = age_months + extra_weeks / 4, extra_weeks = extra_weeks % 4 WHERE user_id = ? AND extra_weeks >= 4", (user_id,))
        conn.commit()
        conn.close()
    
    changes = apply_effects(user_id, effects)
    user = get_db_user(user_id)
    
    is_dead, reason = check_death(user)
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(
            f"💀 *Ты умер!*\nВозраст: {death_age} лет\nПричина: {death_reason}\nРейтинг: *{rank}*",
            user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        time.sleep(REQUEST_DELAY)
        return
    
    change_text = "\n".join(changes) if changes else "Без изменений"
    bot.edit_message_text(
        f"*{title}*\n{desc}\n\n📊 *Изменения:*\n{change_text}\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== МАГАЗИН И ИНВЕНТАРЬ ======================

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🍔 Еда", callback_data="shop_food"),
        types.InlineKeyboardButton("🍺 Алкоголь", callback_data="shop_alcohol"),
        types.InlineKeyboardButton("🚬 Сигареты", callback_data="shop_cigarettes"),
        types.InlineKeyboardButton("💨 Вейпы", callback_data="shop_vape"),
        types.InlineKeyboardButton("⚡ Энергетики", callback_data="shop_energy"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    bot.edit_message_text(f"🛒 *Магазин*\n💰 {user['money']:,} ₽", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
def shop_category(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
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
    bot.edit_message_text("🛒 *Товары:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("underage_"))
def underage_buy(call):
    user_id = call.from_user.id
    anti_flood(user_id)
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
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_"))
def ask_person(call):
    user_id = call.from_user.id
    anti_flood(user_id)
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
        
        # Добавляем в инвентарь
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, name))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("UPDATE inventory SET quantity = quantity + 1 WHERE id = ?", (existing[0],))
        else:
            cursor.execute("INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?,?,?,1)", (user_id, name, data["ask_category"]))
        conn.commit()
        conn.close()
        
        bot.edit_message_text(
            f"✅ Получил {name}!\n\n📊 Изменения:\n" + "\n".join(changes + changes2),
            user_id, call.message.message_id, parse_mode="Markdown",
            reply_markup=life_actions_keyboard(get_db_user(user_id)))
    else:
        apply_effects(user_id, {"stress": 10, "happiness": -5})
        if person == "brother":
            apply_effects(user_id, {"stress": 15, "reputation": -5})
            text = "👨 Брат отказал и рассказал родителям! 😡"
        elif person == "myself":
            apply_effects(user_id, {"criminal_level": 5, "reputation": -5})
            text = "🕵️ Тебя спалили! Родителей вызвали в школу!"
        else:
            text = "🧑 Друг отказался помогать..."
        bot.edit_message_text(f"❌ {text}\n\n{get_profile_text(get_db_user(user_id))}",
                             user_id, call.message.message_id, parse_mode="Markdown",
                             reply_markup=life_actions_keyboard(get_db_user(user_id)))
    
    if user_id in user_temp: del user_temp[user_id]
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    user_id = call.from_user.id
    anti_flood(user_id)
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
    # Не применяем эффекты сразу — они будут при использовании
    
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
        f"✅ Куплено: {name} (в инвентаре)\n\n📊 Изменения:\n" + "\n".join(changes) + f"\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data in ["inventory", "inventory_use"])
def show_inventory(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    if not user: return
    
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
        emoji = ""
        if item["item_type"] in ["alcohol"]: emoji = "🍺"
        elif item["item_type"] in ["cigarettes"]: emoji = "🚬"
        elif item["item_type"] in ["vape"]: emoji = "💨"
        elif item["item_type"] in ["energy"]: emoji = "⚡"
        elif item["item_type"] in ["food"]: emoji = "🍔"
        keyboard.add(types.InlineKeyboardButton(
            f"{emoji} {item['item_name']} (x{item['quantity']})", 
            callback_data=f"use_{item['id']}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life"))
    
    bot.edit_message_text("🎒 *Инвентарь*\nВыбери предмет для использования:", 
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
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
        bot.answer_callback_query(call.id, "Предмет не найден")
        conn.close()
        return
    
    # Эффекты от использования
    all_items = {}
    for cat, items in SHOP_ITEMS.items():
        for name, price, effects in items:
            all_items[name] = effects
    
    effects = all_items.get(item["item_name"], {"happiness": 5})
    changes = apply_effects(user_id, effects)
    
    if item["quantity"] > 1:
        cursor.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = ?", (item_id,))
    else:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    user = get_db_user(user_id)
    bot.edit_message_text(
        f"✅ Использовал: {item['item_name']}\n\n📊 *Эффекты:*\n" + "\n".join(changes) + f"\n\n{get_profile_text(user)}",
        user_id, call.message.message_id, parse_mode="Markdown",
        reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== ТРАНСПОРТ И ПУТЕШЕСТВИЯ ======================

@bot.callback_query_handler(func=lambda call: call.data == "transport")
def transport_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🚲 Велосипеды", callback_data="trans_bicycles"),
        types.InlineKeyboardButton("🏍️ Питбайки", callback_data="trans_pitbikes"),
        types.InlineKeyboardButton("🏍️ Мотоциклы", callback_data="trans_motorcycles"),
        types.InlineKeyboardButton("🚗 Машины", callback_data="trans_cars"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    bot.edit_message_text("🚗 *Транспорт*", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("trans_"))
def transport_category(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    cat = call.data.split("_")[1]
    items = TRANSPORT.get(cat, [])
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, vtype in items:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽", callback_data=f"buyveh_{vtype}_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="transport"))
    bot.edit_message_text("🚗 *Выбери:*", user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyveh_"))
def buy_vehicle(call):
    user_id = call.from_user.id
    anti_flood(user_id)
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
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "travel")
def travel_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, price, months, _ in TRAVELS:
        keyboard.add(types.InlineKeyboardButton(f"{name} - {price:,} ₽ ({months} мес)", callback_data=f"travelgo_{name}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    bot.edit_message_text(f"✈️ *Путешествия*\n💰 {user['money']:,} ₽", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("travelgo_"))
def travel_go(call):
    user_id = call.from_user.id
    anti_flood(user_id)
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
    time.sleep(REQUEST_DELAY)

# ====================== ОГЭ, ЕГЭ, АРМИЯ, КРИМИНАЛ ======================

@bot.callback_query_handler(func=lambda call: call.data == "exam_oge")
def exam_oge(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    intelligence = user["intelligence"]
    
    math = random.randint(max(1, intelligence - 20), min(100, intelligence + 20))
    rus = random.randint(max(1, intelligence - 20), min(100, intelligence + 20))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET og_math = ?, og_rus = ? WHERE user_id = ?", (math, rus, user_id))
    conn.commit()
    conn.close()
    
    passed = math >= 40 and rus >= 40
    money = 0
    if passed and math >= 80 and rus >= 80:
        money = 30000
        apply_effects(user_id, {"money": money, "happiness": 20})
    
    text = f"📝 *ОГЭ сдан!*\n\nМатематика: {math}/100\nРусский: {rus}/100\n\n"
    text += "✅ Сдал! Аттестат получен!" if passed else "❌ Не сдал! Пересдача..."
    if money:
        text += f"\n💰 Стипендия за отличные оценки: {money:,} ₽"
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(get_db_user(user_id)))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "exam_ege")
def exam_ege(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    intelligence = user["intelligence"]
    
    math = random.randint(max(1, intelligence - 25), min(100, intelligence + 15))
    rus = random.randint(max(1, intelligence - 25), min(100, intelligence + 15))
    physics = random.randint(max(1, intelligence - 30), min(100, intelligence + 10))
    info = random.randint(max(1, intelligence - 30), min(100, intelligence + 10))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ege_math = ?, ege_rus = ?, ege_physics = ?, ege_info = ? WHERE user_id = ?",
                   (math, rus, physics, info, user_id))
    conn.commit()
    conn.close()
    
    total = math + rus + physics
    passed = math >= 40 and rus >= 40
    
    text = f"📝 *ЕГЭ сдан!*\n\nМатематика: {math}/100\nРусский: {rus}/100\nФизика: {physics}/100\nИнформатика: {info}/100\n\n"
    text += "✅ Можно поступать в универ!" if passed and total >= 200 else "❌ Баллов маловато..."
    
    add_months(user_id, 3)
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(get_db_user(user_id)))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "military_office")
def military_office(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🩺 Пройти медкомиссию", callback_data="military_med"),
        types.InlineKeyboardButton("🏃 Пойти служить", callback_data="military_serve"),
        types.InlineKeyboardButton("💉 Откосить (взятка 50к)", callback_data="military_avoid"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
    )
    
    text = f"🎖️ *Военкомат*\n\nВозраст: {user['age_months']//12} лет\nКатегория: {user.get('military_category','не определена')}\n\n"
    if user.get("university"):
        text += "✅ Есть отсрочка по учёбе!\n"
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("military_"))
def military_action(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    action = call.data.split("_")[1]
    user = get_db_user(user_id)
    
    if action == "med":
        health = user["health"]
        if health >= 80:
            category = "А (годен)"
        elif health >= 60:
            category = "Б (годен с ограничениями)"
        elif health >= 40:
            category = "В (ограниченно годен)"
        else:
            category = "Д (не годен)"
        
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("UPDATE users SET military_category = ? WHERE user_id = ?", (category, user_id))
        conn.commit()
        conn.close()
        text = f"🩺 Медкомиссия пройдена!\nКатегория: {category}"
    
    elif action == "serve":
        if user.get("university"):
            text = "❌ Нельзя! У тебя отсрочка по учёбе."
        elif user["health"] < 40:
            text = "❌ Не годен по здоровью."
        else:
            add_months(user_id, 12)
            apply_effects(user_id, {"health": 10, "stress": 20, "happiness": -10, "reputation": 5})
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("UPDATE users SET army_served = 1, military_rank = 'Рядовой' WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            text = "🎖️ Отслужил 1 год! +Здоровье, +Репутация"
    
    elif action == "avoid":
        if user["money"] < 50000:
            text = "❌ Не хватает денег на взятку."
        else:
            apply_effects(user_id, {"money": -50000, "criminal_level": 5})
            if random.random() < 0.7:
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("UPDATE users SET military_category = 'В (куплен)' WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                text = "💉 Откосил успешно! -50,000 ₽"
            else:
                apply_effects(user_id, {"criminal_level": 15, "reputation": -20})
                text = "🚔 Врача взяли за коррупцию! Ты в деле..."
    
    bot.edit_message_text(text, user_id, call.message.message_id, parse_mode="Markdown",
                         reply_markup=life_actions_keyboard(get_db_user(user_id)))
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "crime_menu")
def crime_menu(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🔪 АУЕ/закладки", callback_data="crime_au"),
        types.InlineKeyboardButton("💰 Мошенничество", callback_data="crime_fraud"),
        types.InlineKeyboardButton("💊 Наркотики", callback_data="crime_drugs"),
        types.InlineKeyboardButton("🔫 ОПГ/разборки", callback_data="crime_gang"),
        types.InlineKeyboardButton("🚔 Я в тюрьме", callback_data="jail_status"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    bot.edit_message_text(f"🚔 *Криминал*\nУровень: {user['criminal_level']}/100\n💰 {user['money']:,} ₽",
                         user_id, call.message.message_id, parse_mode="Markdown", reply_markup=keyboard)
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data.startswith("crime_"))
def crime_actions(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    crime_type = call.data.split("_")[1]
    user = get_db_user(user_id)
    
    if crime_type == "au":
        if user["age_months"] // 12 < 12:
            text = "❌ Слишком мал для этого."
        else:
            add_months(user_id, 1)
            if random.random() < 0.6:
                money = random.randint(5000, 30000)
                apply_effects(user_id, {"money": money, "criminal_level": 10, "stress": -10, "reputation": -10})
                text = f"🔪 Сделал закладку! +{money:,} ₽, но +Криминал"
            else:
                apply_effects(user_id, {"criminal_level": 20, "reputation": -15})
                if random.random() < 0.3:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO jail (user_id, reason, sentence_months) VALUES (?, 'АУЕ закладки', ?)", 
                                 (user_id, random.randint(12, 48)))
                    conn.commit()
                    conn.close()
                    text = "🚔 Попался! Посадили на несколько лет!"
                else:
                    text = "🚔 Чудом убежал от ментов..."
    elif crime_type == "fraud":
        add_months(user_id, 2)
        money = random.randint(50000, 200000)
        if random.random() < 0.5:
            apply_effects(user_id, {"money": money, "criminal_level": 5, "intelligence": 3})
            text = f"💰 Успешное мошенничество! +{money:,} ₽"
        else:
            apply_effects(user_id, {"criminal_level": 10, "reputation": -10})
            text = "❌ Кинули тебя самого..."
    elif crime_type == "drugs":
        if user["age_months"] // 12 < 16:
            text = "❌ Слишком мал."
        else:
            add_months(user_id, 1)
            apply_effects(user_id, {"money": random.randint(20000, 100000), "criminal_level": 25, "health": -10, "stress": -15})
            if random.random() < 0.2:
                apply_effects(user_id, {"health": -50})
                text = "💊 Передозировка! Еле откачали..."
            else:
                text = "💊 Продал наркоты. Деньги есть, но здоровье подсело."
    elif crime_type == "gang":
        add_months(user_id, 3)
        if random.random() < 0.4:
            apply_effects(user_id, {"money": random.randint(100000, 500000), "criminal_level": 30, "reputation": -30})
            text = "🔫 Участвовал в разборке. Заработал, но теперь в розыске."
        elif random.random() < 0.3:
            apply_effects(user_id, {"health": -50})
            text = "🔫 Подстрелили в разборке! Чудом выжил..."
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO jail (user_id, reason, sentence_months) VALUES (?, 'ОПГ разборки', ?)", 
                         (user_id, random.randint(36, 120)))
            conn.commit()
            conn.close()
            text = "🚔 Повязали всю банду! Долгий срок..."
    
    user = get_db_user(user_id)
    is_dead, reason = check_death(user)
    if is_dead:
        death_age, death_reason, rank, score = end_life(user)
        bot.edit_message_text(f"💀 *Ты умер!*\nВозраст: {death_age} лет\nПричина: {death_reason}\nРейтинг: *{rank}*",
                             user_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        bot.edit_message_text(f"{text}\n\n{get_profile_text(user)}", user_id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=life_actions_keyboard(user))
    time.sleep(REQUEST_DELAY)

# ====================== ПРОФИЛЬ, МЕНЮ, ПРОШЛЫЕ ЖИЗНИ ======================

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
    if user and user["is_alive"] == 1:
        text = f"🏠 *Главное меню*\n\n{get_profile_text(user)}"
    else:
        text = "🏠 *Главное меню*\n\nНачни новую жизнь!"
    bot.edit_message_text(text, user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=main_menu_keyboard())
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data == "past_lives")
def show_past_lives(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_lives WHERE user_id = ? ORDER BY life_number DESC LIMIT 5", (user_id,))
    lives = cursor.fetchall()
    conn.close()
    text = "\n\n".join([f"#{l['life_number']} | {l['country']}\n{l['death_age']} лет | {l['death_reason']}\nРейтинг: *{l['life_rank']}* | 💰 {l['money']:,} ₽" for l in lives]) if lives else "Нет прошлых жизней"
    bot.edit_message_text(f"📜 *Прошлые жизни:*\n\n{text}", user_id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=main_menu_keyboard())
    time.sleep(REQUEST_DELAY)

@bot.callback_query_handler(func=lambda call: call.data in ["relationships","business","jail_status","exit_game","new_life","ask_buy"])
def stub_menus(call):
    user_id = call.from_user.id
    anti_flood(user_id)
    user = get_db_user(user_id)
    
    if call.data == "new_life":
        if user and user["is_alive"] == 1: end_life(user)
        user_temp[user_id] = {"step": "gender"}
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
                     types.InlineKeyboardButton("👩 Женский", callback_data="gender_female"))
        bot.edit_message_text("🌟 *Новая жизнь!*\nВыбери пол:", user_id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=keyboard)
    elif call.data == "exit_game":
        bot.edit_message_text("👋 До встречи! /start для новой игры", user_id, call.message.message_id)
    elif call.data == "ask_buy":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("🍺 Алкоголь", callback_data="ask_alcohol"),
            types.InlineKeyboardButton("🚬 Сигареты", callback_data="ask_cigarettes"),
            types.InlineKeyboardButton("💨 Вейпы", callback_data="ask_vape"),
            types.InlineKeyboardButton("⚡ Энергетики", callback_data="ask_energy"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="continue_life")
        )
        bot.edit_message_text("🙏 Что попросить купить?", user_id, call.message.message_id, reply_markup=keyboard)
    elif call.data in ["ask_alcohol","ask_cigarettes","ask_vape","ask_energy"]:
        category = call.data.split("_")[1]
        items = SHOP_ITEMS.get(category, [])
        user_temp[user_id] = {"ask_category": category}
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for name, price, _ in items:
            keyboard.add(types.InlineKeyboardButton(f"{name} - {price} ₽", callback_data=f"underage_{category}_{name}"))
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="ask_buy"))
        bot.edit_message_text("🙏 Что попросить?", user_id, call.message.message_id, reply_markup=keyboard)
    else:
        texts = {"relationships":"❤️ *Отношения*\nВ разработке","business":"💰 *Бизнес*\nВ разработке","jail_status":"🚔 *Тюрьма*\nНа свободе!"}
        bot.edit_message_text(texts.get(call.data,""), user_id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=main_menu_keyboard())
    time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    print("🤖 Life Simulator v2.0 запущен!")
    bot.remove_webhook()
    bot.infinity_polling()
