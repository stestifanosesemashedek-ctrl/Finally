#!/usr/bin/env python3
"""
SUNDAY SCHOOL MANAGEMENT TELEGRAM BOT
Complete solution for students, teachers, and parents
"""

import os
import logging
import time
import random
from datetime import datetime
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEVELOPER_NAME = "Sunday School Management System"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ==================== LANGUAGE MANAGER ====================
class LanguageManager:
    def __init__(self):
        self.languages = {
            "en": {"name": "English 🇺🇸", "code": "en"},
            "am": {"name": "አማርኛ 🇪🇹", "code": "am"},
            "or": {"name": "Oromiffa 🇪🇹", "code": "or"}
        }
        self.user_languages = {}
    
    def set_language(self, user_id, lang_code):
        self.user_languages[user_id] = lang_code
    
    def get_language(self, user_id):
        return self.user_languages.get(user_id, "en")

language_manager = LanguageManager()

# ==================== SIMPLE DATABASE ====================
class SimpleDB:
    def __init__(self):
        self.users = {
            "STS0001": {"name": "ሚካኤል አለማየሁ", "class": "ቀዳማይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "", 
                       "grades": {"Bible": 85, "Math": 90}, "attendance": {"2024-01": 95}},
            
            "STS0002": {"name": "Sarah Johnson", "class": "ካልኣይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "",
                       "grades": {"Bible": 92, "Math": 88}, "attendance": {"2024-01": 90}},
            
            "TCH1001": {"name": "ወንድም ገብረመድህን", "subject": "Mathematics", 
                       "password": "teacher123", "role": "teacher", 
                       "password_changed": False, "contact": ""},
            
            "ADM5001": {"name": "Mr. Daniel G/Michael", "password": "admin123", 
                       "role": "admin", "password_changed": False, "contact": ""},
        }
        
        self.shared_contacts = []
        self.quiz_questions = {
            "bible": [
                {"question": "Who built the ark?", "options": ["Moses", "Noah", "David", "Abraham"], "answer": "Noah"},
                {"question": "How many books in the New Testament?", "options": ["27", "39", "66", "12"], "answer": "27"},
            ],
            "math": [
                {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "answer": "4"},
                {"question": "What is 5 × 3?", "options": ["10", "15", "20", "25"], "answer": "15"},
            ],
        }
        self.quizzes = {}
        self.study_materials = {
            "ቀዳማይ": ["Bible Stories", "Basic Math", "Alphabet"],
            "ካልኣይ": ["Bible Verses", "Addition/Subtraction", "Simple Sentences"],
        }
    
    def get_user(self, user_id):
        user_id = user_id.upper().strip()
        return self.users.get(user_id)
    
    def verify_password(self, user_id, password):
        user = self.get_user(user_id)
        if not user:
            return False
        return user["password"] == password
    
    def update_password(self, user_id, new_password):
        if user_id in self.users:
            self.users[user_id]["password"] = new_password
            self.users[user_id]["password_changed"] = True
            return True
        return False
    
    def check_password_change(self, user_id):
        user = self.get_user(user_id)
        return user.get("password_changed", False) if user else False
    
    def update_contact(self, user_id, contact_info):
        if user_id in self.users:
            self.users[user_id]["contact"] = contact_info
            return True
        return False
    
    def add_shared_contact(self, user_id, contact_info):
        self.shared_contacts.append({
            "user_id": user_id,
            "contact": contact_info,
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        return True
    
    def start_quiz(self, user_id, subject):
        quiz_id = f"quiz_{int(time.time())}_{user_id}"
        questions = self.quiz_questions.get(subject, [])
        if not questions:
            return None
        
        self.quizzes[quiz_id] = {
            "user_id": user_id,
            "subject": subject,
            "questions": random.sample(questions, min(2, len(questions))),
            "current_question": 0,
            "score": 0,
            "start_time": time.time(),
            "answers": []
        }
        return quiz_id
    
    def get_next_question(self, quiz_id):
        quiz = self.quizzes.get(quiz_id)
        if not quiz or quiz["current_question"] >= len(quiz["questions"]):
            return None
        
        question = quiz["questions"][quiz["current_question"]]
        quiz["current_question"] += 1
        return question
    
    def submit_answer(self, quiz_id, answer):
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return False
        
        current_idx = quiz["current_question"] - 1
        if current_idx < 0:
            return False
        
        question = quiz["questions"][current_idx]
        is_correct = (answer == question["answer"])
        
        quiz["answers"].append({
            "question": question["question"],
            "user_answer": answer,
            "correct_answer": question["answer"],
            "is_correct": is_correct
        })
        
        if is_correct:
            quiz["score"] += 1
        
        return is_correct
    
    def get_quiz_result(self, quiz_id):
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return None
        
        return {
            "score": quiz["score"],
            "total": len(quiz["questions"]),
            "percentage": (quiz["score"] / len(quiz["questions"])) * 100 if quiz["questions"] else 0,
            "time_taken": time.time() - quiz["start_time"],
            "answers": quiz["answers"]
        }

db = SimpleDB()
# ==================== START COMMAND ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am")],
        [InlineKeyboardButton("Oromiffa 🇪🇹", callback_data="lang_or")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌍 **Please choose your language / ቋንቋዎን ይምረጡ / Afaan kee filadhu:**",
        reply_markup=reply_markup
    )

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    lang_code = query.data.split("_")[1]
    user_id = str(query.from_user.id)
    language_manager.set_language(user_id, lang_code)
    
    await query.edit_message_text(
        f"✅ Language set to {language_manager.languages[lang_code]['name']}\n\n"
        "👤 **Please enter your User ID:**\n\n"
        "📝 **Examples:** STS0001, TCH1001, ADM5001\n\n"
        "🔑 **Default Passwords:**\n"
        "• Students: student123\n"
        "• Teachers: teacher123\n"
        "• Admins: admin123"
    )
    context.user_data['expecting'] = 'user_id'

async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input"""
    user_id = update.message.text.upper().strip()
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ **Invalid User ID!**\n\n"
            "Try: STS0001, TCH1001, ADM5001\n\n"
            "Enter again:"
        )
        return
    
    context.user_data['login_user_id'] = user_id
    context.user_data['login_user_data'] = user_data
    
    await update.message.reply_text(
        f"👋 **Welcome {user_data['name']}!**\n"
        f"🎭 Role: {user_data['role'].title()}\n\n"
        "🔐 Enter your password:"
    )
    context.user_data['expecting'] = 'password'

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password input"""
    password = update.message.text.strip()
    user_id = context.user_data.get('login_user_id')
    user_data = context.user_data.get('login_user_data')
    
    if not user_id or not user_data:
        await update.message.reply_text("❌ Session error. Use /start")
        return
    
    if db.verify_password(user_id, password):
        if not db.check_password_change(user_id):
            context.user_data['expecting'] = 'new_password'
            await update.message.reply_text(
                "⚠️ **Change default password first!**\n\n"
                "Enter new password (min 6 chars):"
            )
            return
        
        # Check contact
        if not user_data.get('contact'):
            await update.message.reply_text(
                "📱 **Contact Verification Required**"
            )
            keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Tap to share:", reply_markup=reply_markup)
            context.user_data['expecting'] = 'initial_contact'
            return
        
        # Login successful
        await complete_login(update, context, user_id, user_data)
    else:
        await update.message.reply_text("❌ Incorrect password! Try again:")

async def handle_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new password"""
    new_password = update.message.text.strip()
    user_id = context.user_data.get('login_user_id')
    user_data = context.user_data.get('login_user_data')
    
    if len(new_password) < 6:
        await update.message.reply_text("❌ Min 6 characters. Try again:")
        return
    
    db.update_password(user_id, new_password)
    context.user_data.pop('expecting', None)
    await update.message.reply_text("✅ Password changed!")
    
    # Check contact
    if not user_data.get('contact'):
        await update.message.reply_text(
            "📱 **Contact Verification Required**"
        )
        keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Tap to share:", reply_markup=reply_markup)
        context.user_data['expecting'] = 'initial_contact'
        return
    
    await complete_login(update, context, user_id, user_data)
    async def complete_login(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, user_data):
    """Complete login process"""
    context.user_data['user_id'] = user_id
    context.user_data['user_name'] = user_data['name']
    context.user_data['user_role'] = user_data['role']
    context.user_data['logged_in'] = True
    
    if user_data['role'] == 'student':
        context.user_data['student_class'] = user_data['class']
    elif user_data['role'] == 'teacher':
        context.user_data['teacher_subject'] = user_data.get('subject', 'Unknown')
    
    context.user_data.pop('login_user_id', None)
    context.user_data.pop('login_user_data', None)
    
    await show_main_menu(update, context, is_callback=False)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact sharing"""
    if update.message.contact:
        phone = update.message.contact.phone_number
        user_id = context.user_data.get('login_user_id') or context.user_data.get('user_id')
        user_name = context.user_data.get('login_user_data', {}).get('name') or context.user_data.get('user_name')
        
        if not user_id:
            await update.message.reply_text("❌ Session error. Use /start")
            return
        
        contact_info = {"phone": phone, "name": user_name}
        db.update_contact(user_id, contact_info)
        db.add_shared_contact(user_id, contact_info)
        
        await update.message.reply_text("✅ Contact verified!", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop('expecting', None)
        
        # Complete login if this was initial contact
        if context.user_data.get('login_user_id'):
            user_id = context.user_data['login_user_id']
            user_data = context.user_data['login_user_data']
            await complete_login(update, context, user_id, user_data)
        else:
            # Return to menu
            await show_main_menu(update, context, is_callback=False)
            async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=True):
    """Show main menu"""
    user_name = context.user_data.get('user_name', 'User')
    user_role = context.user_data.get('user_role', 'user')
    
    if user_role == "student":
        student_class = context.user_data.get('student_class', 'Unknown')
        welcome_text = f"""🎓 **Welcome {user_name}!**
🏫 **Class:** {student_class}

Please choose:"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Study Materials", callback_data="materials")],
            [InlineKeyboardButton("📅 Schedule", callback_data="schedule")],
            [InlineKeyboardButton("📊 Grades", callback_data="grades")],
            [InlineKeyboardButton("🎯 Take Quiz", callback_data="take_quiz")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    elif user_role == "teacher":
        teacher_subject = context.user_data.get('teacher_subject', 'Unknown')
        welcome_text = f"""👨‍🏫 **Welcome {user_name}!**
📚 **Subject:** {teacher_subject}

Please choose:"""
        
        keyboard = [
            [InlineKeyboardButton("👨‍🎓 My Students", callback_data="my_students")],
            [InlineKeyboardButton("📝 Assign HW", callback_data="assign_hw")],
            [InlineKeyboardButton("📊 Take Attendance", callback_data="take_attendance")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    else:  # admin
        welcome_text = f"""👨‍💼 **Welcome {user_name}!**
🏢 **Administrator**

Please choose:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Analytics", callback_data="analytics")],
            [InlineKeyboardButton("👨‍🎓 Students", callback_data="manage_students")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        # ==================== STUDENT FEATURES ====================
async def student_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    student_class = context.user_data.get('student_class', 'Unknown')
    materials = db.study_materials.get(student_class, [])
    
    text = f"📚 **Study Materials for {student_class}**\n\n"
    if materials:
        for i, material in enumerate(materials, 1):
            text += f"{i}. {material}\n"
    else:
        text += "No materials available."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def student_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📅 **Weekly Schedule**

**Sunday:**
9:00-10:00 - Sunday School
10:00-11:00 - Worship Service

**Wednesday:**
5:00-6:00 - Prayer Meeting

**Friday:**
5:00-6:30 - Choir Practice"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def student_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = context.user_data.get('user_id')
    student = db.get_user(user_id)
    
    text = "📊 **Your Grades**\n\n"
    if student and "grades" in student:
        for subject, grade in student["grades"].items():
            text += f"**{subject}:** {grade}%\n"
    else:
        text += "No grades recorded."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    # ==================== QUIZ SYSTEM ====================
async def take_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """🎯 **Take a Quiz**

Choose subject:"""
    
    keyboard = [
        [InlineKeyboardButton("📖 Bible", callback_data="quiz_bible")],
        [InlineKeyboardButton("🧮 Mathematics", callback_data="quiz_math")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    subject = query.data.replace("quiz_", "")
    user_id = context.user_data.get('user_id')
    
    quiz_id = db.start_quiz(user_id, subject)
    if not quiz_id:
        await query.edit_message_text("❌ No questions available.")
        return
    
    context.user_data['current_quiz'] = quiz_id
    question = db.get_next_question(quiz_id)
    
    if not question:
        await query.edit_message_text("❌ Error loading questions.")
        return
    
    text = f"❓ **Question 1:** {question['question']}\n\n"
    keyboard = []
    for i, option in enumerate(question['options'], 1):
        keyboard.append([InlineKeyboardButton(f"{i}. {option}", callback_data=f"answer_{option}")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    answer = query.data.replace("answer_", "")
    quiz_id = context.user_data.get('current_quiz')
    
    if not quiz_id:
        await query.edit_message_text("❌ Quiz expired. Start again.")
        return
    
    is_correct = db.submit_answer(quiz_id, answer)
    question = db.get_next_question(quiz_id)
    
    if question:
        quiz = db.quizzes.get(quiz_id)
        current_q = quiz['current_question'] if quiz else 1
        
        text = f"✅ **{'Correct!' if is_correct else 'Incorrect!'}**\n\n"
        text += f"❓ **Question {current_q}:** {question['question']}\n\n"
        
        keyboard = []
        for i, option in enumerate(question['options'], 1):
            keyboard.append([InlineKeyboardButton(f"{i}. {option}", callback_data=f"answer_{option}")])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        result = db.get_quiz_result(quiz_id)
        
        text = f"""🏆 **Quiz Completed!**

📊 **Score:** {result['score']}/{result['total']}
📈 **Percentage:** {result['percentage']:.1f}%
⏱️ **Time:** {result['time_taken']:.1f}s"""
        
        keyboard = [[InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data.pop('current_quiz', None)
        # ==================== TEACHER FEATURES ====================
async def teacher_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """👨‍🎓 **My Students**

1. **ሚካኤል አለማየሁ** (STS0001)
   - Class: ቀዳማይ
   - Grade: 87%
   
2. **Sarah Johnson** (STS0002)
   - Class: ካልኣይ
   - Grade: 90%"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def teacher_assign_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📝 **Assign Homework**

Select class:"""
    
    keyboard = [
        [InlineKeyboardButton("ቀዳማይ", callback_data="hw_1")],
        [InlineKeyboardButton("ካልኣይ", callback_data="hw_2")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def teacher_take_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📊 **Take Attendance**

Select student:"""
    
    keyboard = [
        [InlineKeyboardButton("✅ ሚካኤል", callback_data="att_1")],
        [InlineKeyboardButton("✅ Sarah", callback_data="att_2")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    # ==================== ADMIN FEATURES ====================
async def admin_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📊 **System Analytics**

👨‍🎓 **Students:** 2
👨‍🏫 **Teachers:** 1
🏫 **Classes:** 2

**Status:** ✅ Operational"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== CONTACT MANAGEMENT ====================
async def share_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📞 **Share Contact**

Choose method:"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Share via Button", callback_data="request_contact")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def request_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await query.edit_message_text("Tap button to share:", reply_markup=reply_markup)
    context.user_data['expecting'] = 'contact_button'

async def view_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    contacts = db.shared_contacts[-5:]
    text = "📱 **Recent Contacts**\n\n"
    
    if contacts:
        for i, contact in enumerate(reversed(contacts), 1):
            user = db.get_user(contact['user_id'])
            name = user['name'] if user else contact['user_id']
            text += f"{i}. {name}\n"
    else:
        text += "No contacts shared."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    # ==================== SETTINGS ====================
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """⚙️ **Settings**

Choose option:"""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("🔐 Change Password", callback_data="change_pass")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data="set_en")],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="set_am")],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings")]
    ]
    await query.edit_message_text("Select language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang_map = {"set_en": "en", "set_am": "am"}
    lang_code = lang_map.get(query.data, "en")
    user_id = str(query.from_user.id)
    
    language_manager.set_language(user_id, lang_code)
    await query.edit_message_text(f"✅ Language set to {language_manager.languages[lang_code]['name']}")
    await show_settings(update, context)

async def change_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("Enter new password (min 6 chars):")
    context.user_data['expecting'] = 'change_password'
    # ==================== CALLBACK HANDLER ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Check login for protected routes
    protected_routes = [
        "materials", "schedule", "grades", "take_quiz", "my_students",
        "assign_hw", "take_attendance", "analytics", "manage_students",
        "share_contact", "view_contacts", "settings", "change_lang",
        "change_pass"
    ]
    
    if data in protected_routes and not context.user_data.get('logged_in'):
        await query.edit_message_text("❌ Please login with /start")
        return
    
    # Route handling
    if data == "main_menu":
        await show_main_menu(update, context, is_callback=True)
    
    elif data == "logout":
        context.user_data.clear()
        await query.edit_message_text("✅ Logged out. Use /start")
    
    elif data.startswith("lang_"):
        await handle_language_selection(update, context)
    
    elif data in ["set_en", "set_am"]:
        await set_language(update, context)
    
    elif data.startswith("quiz_"):
        await start_quiz(update, context)
    
    elif data.startswith("answer_"):
        await handle_quiz_answer(update, context)
    
    # Student features
    elif data == "materials":
        await student_materials(update, context)
    elif data == "schedule":
        await student_schedule(update, context)
    elif data == "grades":
        await student_grades(update, context)
    elif data == "take_quiz":
        await take_quiz(update, context)
    
    # Teacher features
    elif data == "my_students":
        await teacher_students(update, context)
    elif data == "assign_hw":
        await teacher_assign_hw(update, context)
    elif data == "take_attendance":
        await teacher_take_attendance(update, context)
    
    # Admin features
    elif data == "analytics":
        await admin_analytics(update, context)
    elif data == "manage_students":
        await query.edit_message_text("✅ Student management")
        await show_main_menu(update, context, is_callback=True)
    
    # Contact features
    elif data == "share_contact":
        await share_contact(update, context)
    elif data == "request_contact":
        await request_contact(update, context)
    elif data == "view_contacts":
        await view_contacts(update, context)
    
    # Settings
    elif data == "settings":
        await show_settings(update, context)
    elif data == "change_lang":
        await change_lang(update, context)
    elif data == "change_pass":
        await change_pass(update, context)
    
    else:
        # Handle attendance or other dynamic callbacks
        if data.startswith("att_") or data.startswith("hw_"):
            await query.edit_message_text("✅ Action completed!")
            await show_main_menu(update, context, is_callback=True)
        else:
            await query.edit_message_text("❌ Unknown command")
            # ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle contact sharing
    if update.message.contact:
        await handle_contact(update, context)
        return
    
    if not update.message.text:
        return
    
    expecting = context.user_data.get('expecting')
    text = update.message.text.strip()
    
    if expecting == 'user_id':
        await handle_user_id(update, context)
    
    elif expecting == 'password':
        await handle_password(update, context)
    
    elif expecting == 'new_password':
        await handle_new_password(update, context)
    
    elif expecting == 'change_password':
        user_id = context.user_data.get('user_id')
        if len(text) < 6:
            await update.message.reply_text("❌ Min 6 chars. Try again:")
            return
        
        db.update_password(user_id, text)
        await update.message.reply_text("✅ Password changed!")
        context.user_data.pop('expecting', None)
        await show_main_menu(update, context, is_callback=False)
    
    elif expecting == 'manual_contact':
        user_id = context.user_data.get('user_id')
        contact_info = {"phone": text, "name": context.user_data.get('user_name')}
        db.update_contact(user_id, contact_info)
        db.add_shared_contact(user_id, contact_info)
        await update.message.reply_text("✅ Contact saved!")
        context.user_data.pop('expecting', None)
        await show_main_menu(update, context, is_callback=False)
    
    else:
        await update.message.reply_text("Use /start to begin")
        # ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Error occurred. Use /start")
    except:
        pass

# ==================== MAIN FUNCTION ====================
def main():
    if not BOT_TOKEN:
        print("❌ Set TELEGRAM_BOT_TOKEN environment variable!")
        print("💡 Run: export TELEGRAM_BOT_TOKEN='your_token'")
        return
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        app.add_error_handler(error_handler)
        
        print("=" * 50)
        print("✅ Sunday School Bot Started!")
        print(f"🤖 Developer: {DEVELOPER_NAME}")
        print("=" * 50)
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
    