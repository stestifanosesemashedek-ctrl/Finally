#!/usr/bin/env python3
"""
SUNDAY SCHOOL MANAGEMENT TELEGRAM BOT
Complete solution for students, teachers, and parents
"""

import os
import logging
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== CONFIGURATION ====================
# Get BOT_TOKEN from environment variable (secure for deployment)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEVELOPER_NAME = "Sunday School Management System"

# Conversation states
LANGUAGE, USER_ID, PASSWORD, NEW_PASSWORD = range(4)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ==================== LANGUAGE SETTINGS ====================
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
        # Students - STS prefix
        self.users = {
            "STS0001": {"name": "ሚካኤል አለማየሁ", "class": "ቀዳማይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "", 
                       "grades": {"Bible": 85, "Math": 90}, "attendance": {"2024-01": 95}},
            
            "STS0002": {"name": "Sarah Johnson", "class": "ካልኣይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "",
                       "grades": {"Bible": 92, "Math": 88}, "attendance": {"2024-01": 90}},
            
            "STS0003": {"name": "የሻን ገብረመድህን", "class": "ሳልሳይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "",
                       "grades": {"Bible": 78, "Math": 85}, "attendance": {"2024-01": 85}},
            
            "STS0004": {"name": "David Smith", "class": "ራብዓይ", "password": "student123", 
                       "role": "student", "password_changed": False, "contact": "",
                       "grades": {"Bible": 88, "Math": 92}, "attendance": {"2024-01": 98}},
            
            # Teachers - TCH prefix
            "TCH1001": {"name": "ወንድም ገብረመድህን", "subject": "Mathematics", 
                       "password": "teacher123", "role": "teacher", 
                       "password_changed": False, "contact": ""},
            
            "TCH1002": {"name": "Ms. Helen Brown", "subject": "English", 
                       "password": "teacher123", "role": "teacher", 
                       "password_changed": False, "contact": ""},
            
            # Admins - ADM prefix
            "ADM5001": {"name": "Mr. Daniel G/Michael", "password": "admin123", 
                       "role": "admin", "password_changed": False, "contact": ""},
        }
        
        self.shared_contacts = []
        self.quiz_questions = {
            "bible": [
                {"question": "Who built the ark?", "options": ["Moses", "Noah", "David", "Abraham"], "answer": "Noah"},
                {"question": "How many books in the New Testament?", "options": ["27", "39", "66", "12"], "answer": "27"},
                {"question": "Who betrayed Jesus?", "options": ["Peter", "John", "Judas", "Thomas"], "answer": "Judas"}
            ],
            "math": [
                {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "answer": "4"},
                {"question": "What is 5 × 3?", "options": ["10", "15", "20", "25"], "answer": "15"},
                {"question": "What is 12 ÷ 4?", "options": ["2", "3", "4", "6"], "answer": "3"}
            ],
            "english": [
                {"question": "Which is a noun?", "options": ["run", "beautiful", "school", "quickly"], "answer": "school"},
                {"question": "What is the past tense of 'go'?", "options": ["goed", "went", "gone", "going"], "answer": "went"},
            ]
        }
        self.quizzes = {}
        self.study_materials = {
            "ቀዳማይ": ["Bible Stories", "Basic Math", "Alphabet"],
            "ካልኣይ": ["Bible Verses", "Addition/Subtraction", "Simple Sentences"],
            "ሳልሳይ": ["New Testament", "Multiplication", "Grammar"],
            "ራብዓይ": ["Old Testament", "Division", "Composition"]
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
            "questions": random.sample(questions, min(3, len(questions))),
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
    """Handle /start command - Language selection first"""
    user_id = str(update.effective_user.id)
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
    
    user_id = str(query.from_user.id)
    lang_code = query.data.split("_")[1]
    language_manager.set_language(user_id, lang_code)
    
    await query.edit_message_text(
        f"✅ Language set to {language_manager.languages[lang_code]['name']}\n\n"
        "👤 **Please enter your User ID:**\n\n"
        "📝 **Format Examples:**\n"
        "• Students: STS0001, STS0002, etc.\n"
        "• Teachers: TCH1001, TCH1002, etc.\n"
        "• Admins: ADM5001\n\n"
        "🔑 **Default Passwords:**\n"
        "• Students: student123\n"
        "• Teachers: teacher123\n"
        "• Admins: admin123"
    )
    context.user_data['expecting'] = 'user_id'
    # ==================== LOGIN HANDLERS ====================
async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input"""
    user_id = update.message.text.upper().strip()
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ **Invalid User ID!**\n\n"
            "Please enter a valid User ID:\n"
            "• Students: STS0001, STS0002, STS0003, STS0004\n"
            "• Teachers: TCH1001, TCH1002\n"
            "• Admins: ADM5001\n\n"
            "Try again:"
        )
        return
    
    context.user_data['login_user_id'] = user_id
    context.user_data['login_user_data'] = user_data
    
    await update.message.reply_text(
        f"👋 **Welcome {user_data['name']}!**\n\n"
        f"🎭 Role: {user_data['role'].title()}\n\n"
        "🔐 Please enter your password:"
    )
    context.user_data['expecting'] = 'password'

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password input"""
    password = update.message.text.strip()
    user_id = context.user_data.get('login_user_id')
    user_data = context.user_data.get('login_user_data')
    
    if not user_id or not user_data:
        await update.message.reply_text("❌ Session error. Please start over with /start")
        return
    
    if db.verify_password(user_id, password):
        if not db.check_password_change(user_id):
            context.user_data['expecting'] = 'new_password'
            await update.message.reply_text(
                "⚠️ **Security Alert!**\n\n"
                "You must change your default password before continuing.\n\n"
                "Please enter a new password (min. 6 characters):"
            )
            return
        
        # Check if contact is required
        if not user_data.get('contact'):
            await update.message.reply_text(
                "📱 **Contact Verification Required**\n\n"
                "Please share your contact to continue:"
            )
            keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Tap to share:", reply_markup=reply_markup)
            context.user_data['expecting'] = 'initial_contact'
            return
        
        await show_main_menu_after_login(update, context, user_id, user_data)
    else:
        await update.message.reply_text("❌ **Incorrect password!**\n\nPlease enter your password again:")

async def handle_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new password setup"""
    new_password = update.message.text.strip()
    user_id = context.user_data.get('login_user_id')
    user_data = context.user_data.get('login_user_data')
    
    if len(new_password) < 6:
        await update.message.reply_text("❌ Password too short! Min 6 characters:")
        return
    
    db.update_password(user_id, new_password)
    context.user_data.pop('expecting', None)
    await update.message.reply_text("✅ **Password changed successfully!**")
    
    if not user_data.get('contact'):
        await update.message.reply_text(
            "📱 **Contact Verification Required**\n\n"
            "Please share your contact to continue:"
        )
        keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Tap to share:", reply_markup=reply_markup)
        context.user_data['expecting'] = 'initial_contact'
        return
    
    await show_main_menu_after_login(update, context, user_id, user_data)
    # ==================== CONTACT HANDLING ====================
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact sharing"""
    if update.message.contact:
        phone = update.message.contact.phone_number
        user_id = context.user_data.get('login_user_id') or context.user_data.get('user_id')
        user_name = context.user_data.get('login_user_data', {}).get('name') or context.user_data.get('user_name')
        
        if not user_id:
            await update.message.reply_text("❌ Session error. Please start over with /start")
            return
        
        contact_info = {"phone": phone, "name": user_name}
        db.update_contact(user_id, contact_info)
        db.add_shared_contact(user_id, contact_info)
        
        await update.message.reply_text("✅ **Contact verified successfully!**", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop('expecting', None)
        
        if context.user_data.get('login_user_id'):
            user_id = context.user_data['login_user_id']
            user_data = context.user_data['login_user_data']
            await show_main_menu_after_login(update, context, user_id, user_data)
        else:
            await show_main_menu_callback_from_message(update, context)

async def share_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact sharing options"""
    query = update.callback_query
    await query.answer()
    
    text = """📞 **Share Contact**

Choose how to share:"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Share via Button", callback_data="request_contact")],
        [InlineKeyboardButton("✏️ Enter Manually", callback_data="enter_contact")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def request_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request contact via button"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await query.edit_message_text("Tap the button below to share your contact:", reply_markup=reply_markup)
    context.user_data['expecting'] = 'contact_button'

async def enter_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enter contact manually"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter phone number (with country code):")
    context.user_data['expecting'] = 'manual_contact'

async def handle_manual_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual contact input"""
    phone = update.message.text.strip()
    user_id = context.user_data.get('user_id')
    contact_info = {"phone": phone, "name": context.user_data.get('user_name')}
    
    db.update_contact(user_id, contact_info)
    db.add_shared_contact(user_id, contact_info)
    
    await update.message.reply_text("✅ Contact saved!")
    await show_main_menu_callback_from_message(update, context)
    context.user_data.pop('expecting', None)

async def view_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View shared contacts"""
    query = update.callback_query
    await query.answer()
    
    contacts = db.shared_contacts[-10:]  # Last 10 contacts
    if not contacts:
        text = "📱 **No contacts shared yet.**"
    else:
        text = "📱 **Recent Contacts:**\n\n"
        for i, contact in enumerate(reversed(contacts), 1):
            user = db.get_user(contact['user_id'])
            name = user['name'] if user else contact['user_id']
            phone = contact['contact'].get('phone', 'N/A')
            date = contact.get('date', 'Unknown date')
            text += f"{i}. **{name}**\n📞 {phone}\n📅 {date}\n\n"
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    # ==================== MAIN MENU FUNCTIONS ====================
async def show_main_menu_after_login(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, user_data):
    """Show main menu after successful login"""
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
    await show_main_menu_callback_from_message(update, context)

async def show_main_menu_callback_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu from message context"""
    user_name = context.user_data.get('user_name', 'User')
    user_role = context.user_data.get('user_role', 'user')
    
    if user_role == "student":
        student_class = context.user_data.get('student_class', 'Unknown')
        welcome_text = f"""🎓 **Welcome {user_name}!**
🏫 **Class:** {student_class}

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Study Materials", callback_data="materials")],
            [InlineKeyboardButton("📅 Schedule", callback_data="schedule")],
            [InlineKeyboardButton("📊 Grades", callback_data="grades")],
            [InlineKeyboardButton("📊 Attendance", callback_data="attendance")],
            [InlineKeyboardButton("📝 Homework", callback_data="homework")],
            [InlineKeyboardButton("🎯 Take Quiz", callback_data="take_quiz")],
            [InlineKeyboardButton("📚 Library", callback_data="library")],
            [InlineKeyboardButton("👨‍🏫 Teachers", callback_data="teachers")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("ℹ️ Profile", callback_data="profile")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    elif user_role == "teacher":
        teacher_subject = context.user_data.get('teacher_subject', 'Unknown')
        welcome_text = f"""👨‍🏫 **Welcome {user_name}!**
📚 **Subject:** {teacher_subject}

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("👨‍🎓 My Students", callback_data="my_students")],
            [InlineKeyboardButton("📝 Assign HW", callback_data="assign_hw")],
            [InlineKeyboardButton("📊 Record Grades", callback_data="record_grades")],
            [InlineKeyboardButton("📊 Take Attendance", callback_data="take_attendance")],
            [InlineKeyboardButton("📚 Materials", callback_data="teaching_materials")],
            [InlineKeyboardButton("📅 Schedule", callback_data="teacher_schedule")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("👥 View Contacts", callback_data="view_contacts")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    else:  # admin
        welcome_text = f"""👨‍💼 **Welcome {user_name}!**
🏢 **Administrator**

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Analytics", callback_data="analytics")],
            [InlineKeyboardButton("👨‍🎓 Students", callback_data="manage_students")],
            [InlineKeyboardButton("👨‍🏫 Teachers", callback_data="manage_teachers")],
            [InlineKeyboardButton("📚 Curriculum", callback_data="curriculum")],
            [InlineKeyboardButton("🏫 Classes", callback_data="manage_classes")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("👥 View Contacts", callback_data="view_contacts")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🔄 Update Database", callback_data="update_db")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu for callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_name = context.user_data.get('user_name', 'User')
    user_role = context.user_data.get('user_role', 'user')
    
    if user_role == "student":
        student_class = context.user_data.get('student_class', 'Unknown')
        welcome_text = f"""🎓 **Welcome {user_name}!**
🏫 **Class:** {student_class}

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Study Materials", callback_data="materials")],
            [InlineKeyboardButton("📅 Schedule", callback_data="schedule")],
            [InlineKeyboardButton("📊 Grades", callback_data="grades")],
            [InlineKeyboardButton("📊 Attendance", callback_data="attendance")],
            [InlineKeyboardButton("📝 Homework", callback_data="homework")],
            [InlineKeyboardButton("🎯 Take Quiz", callback_data="take_quiz")],
            [InlineKeyboardButton("📚 Library", callback_data="library")],
            [InlineKeyboardButton("👨‍🏫 Teachers", callback_data="teachers")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("ℹ️ Profile", callback_data="profile")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    elif user_role == "teacher":
        teacher_subject = context.user_data.get('teacher_subject', 'Unknown')
        welcome_text = f"""👨‍🏫 **Welcome {user_name}!**
📚 **Subject:** {teacher_subject}

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("👨‍🎓 My Students", callback_data="my_students")],
            [InlineKeyboardButton("📝 Assign HW", callback_data="assign_hw")],
            [InlineKeyboardButton("📊 Record Grades", callback_data="record_grades")],
            [InlineKeyboardButton("📊 Take Attendance", callback_data="take_attendance")],
            [InlineKeyboardButton("📚 Materials", callback_data="teaching_materials")],
            [InlineKeyboardButton("📅 Schedule", callback_data="teacher_schedule")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("👥 View Contacts", callback_data="view_contacts")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
        
    else:  # admin
        welcome_text = f"""👨‍💼 **Welcome {user_name}!**
🏢 **Administrator**

Please choose an option:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Analytics", callback_data="analytics")],
            [InlineKeyboardButton("👨‍🎓 Students", callback_data="manage_students")],
            [InlineKeyboardButton("👨‍🏫 Teachers", callback_data="manage_teachers")],
            [InlineKeyboardButton("📚 Curriculum", callback_data="curriculum")],
            [InlineKeyboardButton("🏫 Classes", callback_data="manage_classes")],
            [InlineKeyboardButton("📞 Share Contact", callback_data="share_contact")],
            [InlineKeyboardButton("👥 View Contacts", callback_data="view_contacts")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🔄 Update Database", callback_data="update_db")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    # ==================== QUIZ SYSTEM ====================
async def take_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a quiz"""
    query = update.callback_query
    await query.answer()
    
    text = """🎯 **Take a Quiz**

Choose a subject:"""
    
    keyboard = [
        [InlineKeyboardButton("📖 Bible", callback_data="quiz_bible")],
        [InlineKeyboardButton("🧮 Mathematics", callback_data="quiz_math")],
        [InlineKeyboardButton("📚 English", callback_data="quiz_english")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a specific quiz"""
    query = update.callback_query
    await query.answer()
    
    subject = query.data.replace("quiz_", "")
    user_id = context.user_data.get('user_id')
    
    quiz_id = db.start_quiz(user_id, subject)
    if not quiz_id:
        await query.edit_message_text("❌ No questions available for this subject.")
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
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz answer"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data.replace("answer_", "")
    quiz_id = context.user_data.get('current_quiz')
    
    if not quiz_id:
        await query.edit_message_text("❌ Quiz session expired. Please start again.")
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        result = db.get_quiz_result(quiz_id)
        
        if result:
            text = f"""🏆 **Quiz Completed!**

📊 **Score:** {result['score']}/{result['total']}
📈 **Percentage:** {result['percentage']:.1f}%
⏱️ **Time:** {result['time_taken']:.1f} seconds

📝 **Review Answers:**
"""
            for i, answer in enumerate(result['answers'], 1):
                text += f"\n{i}. {answer['question']}\n"
                text += f"   Your answer: {answer['user_answer']}\n"
                text += f"   Correct answer: {answer['correct_answer']}\n"
                text += f"   Result: {'✅ Correct' if answer['is_correct'] else '❌ Incorrect'}\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        context.user_data.pop('current_quiz', None)
        # ==================== STUDENT FEATURES ====================
async def student_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    student_class = context.user_data.get('student_class', 'Unknown')
    materials = db.study_materials.get(student_class, [])
    
    if materials:
        text = f"""📚 **Study Materials for {student_class}**

Available materials:
"""
        for i, material in enumerate(materials, 1):
            text += f"{i}. {material}\n"
    else:
        text = "No study materials available for your class."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📅 **Weekly Schedule**

**Sunday:**
9:00-10:00 - Sunday School
10:00-11:00 - Worship Service
11:00-12:00 - Bible Study

**Wednesday:**
5:00-6:00 - Prayer Meeting
6:00-7:00 - Youth Group

**Friday:**
5:00-6:30 - Choir Practice"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

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
        text += "No grades recorded yet."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = context.user_data.get('user_id')
    student = db.get_user(user_id)
    
    text = "📊 **Your Attendance**\n\n"
    
    if student and "attendance" in student:
        for month, percentage in student["attendance"].items():
            text += f"**{month}:** {percentage}%\n"
    else:
        text += "No attendance records yet."
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📝 **Homework Assignments**

**Bible Study:**
- Read John Chapter 3
- Memorize John 3:16
- Due: Next Sunday

**Mathematics:**
- Complete exercises 1-10
- Practice multiplication tables
- Due: Wednesday

**English:**
- Write a prayer (100 words)
- Learn 10 new vocabulary words
- Due: Friday"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📚 **School Library**

**Available Books:**
1. Holy Bible (Multiple versions)
2. Children's Bible Stories
3. Christian Living Books
4. Prayer Guides
5. Worship Song Books

**Library Hours:**
Sunday: 8:30 AM - 12:30 PM
Wednesday: 4:30 PM - 7:00 PM"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """👨‍🏫 **Your Teachers**

1. **ወንድም ገብረመድህን** - Bible Study
   - Available: Sundays after service
   
2. **Ms. Helen Brown** - English & Music
   - Available: Wednesdays 6-7 PM
   
3. **Mr. David Smith** - Mathematics
   - Available: Fridays 5-6 PM"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = context.user_data.get('user_id', 'N/A')
    user_name = context.user_data.get('user_name', 'N/A')
    student_class = context.user_data.get('student_class', 'N/A')
    
    text = f"""ℹ️ **Student Profile**

**ID:** {user_id}
**Name:** {user_name}
**Class:** {student_class}
**Role:** Student
**Status:** Active

**Last Login:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    # ==================== TEACHER FEATURES ====================
async def teacher_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """👨‍🎓 **My Students**

1. **ሚካኤል አለማየሁ** (STS0001)
   - Class: ቀዳማይ
   - Avg Grade: 87%
   - Attendance: 95%
   
2. **Sarah Johnson** (STS0002)
   - Class: ካልኣይ
   - Avg Grade: 90%
   - Attendance: 92%
   
3. **የሻን ገብረመድህን** (STS0003)
   - Class: ሳልሳይ
   - Avg Grade: 82%
   - Attendance: 88%
   
4. **David Smith** (STS0004)
   - Class: ራብዓይ
   - Avg Grade: 90%
   - Attendance: 96%"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def teacher_assign_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📝 **Assign Homework**

Select class to assign homework:"""
    
    keyboard = [
        [InlineKeyboardButton("ቀዳማይ", callback_data="hw_class_1")],
        [InlineKeyboardButton("ካልኣይ", callback_data="hw_class_2")],
        [InlineKeyboardButton("ሳልሳይ", callback_data="hw_class_3")],
        [InlineKeyboardButton("ራብዓይ", callback_data="hw_class_4")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def teacher_record_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📊 **Record Grades**

Select student to record grades:"""
    
    keyboard = [
        [InlineKeyboardButton("ሚካኤል አለማየሁ (STS0001)", callback_data="grade_student_1")],
        [InlineKeyboardButton("Sarah Johnson (STS0002)", callback_data="grade_student_2")],
        [InlineKeyboardButton("የሻን ገብረመድህን (STS0003)", callback_data="grade_student_3")],
        [InlineKeyboardButton("David Smith (STS0004)", callback_data="grade_student_4")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def teacher_take_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """📊 **Take Attendance**

Mark attendance for:"""
    
    keyboard = [
        [InlineKeyboardButton("✅ ሚካኤል አለማየሁ", callback_data="attendance_present_STS0001"),
         InlineKeyboardButton("❌ Absent", callback_data="attendance_absent_STS0001")],
        [InlineKeyboardButton("✅ Sarah Johnson", callback_data="attendance_present_STS0002"),
         InlineKeyboardButton("❌ Absent", callback_data="attendance_absent_STS0002")],
        [InlineKeyboardButton("✅ የሻን ገብረመድህን", callback_data="attendance_present_STS0003"),
         InlineKeyboardButton("❌ Absent", callback_data="attendance_absent_STS0003")],
        [InlineKeyboardButton("✅ David Smith", callback_data="attendance_present_STS0004"),
         InlineKeyboardButton("❌ Absent", callback_data="attendance_absent_STS0004")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    # ==================== ADMIN FEATURES ====================
async def admin_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    total_students = sum(1 for user in db.users.values() if user["role"] == "student")
    total_teachers = sum(1 for user in db.users.values() if user["role"] == "teacher")
    
    text = f"""📊 **System Analytics**

👨‍🎓 **Students:** {total_students}
👨‍🏫 **Teachers:** {total_teachers}
🏫 **Classes:** 4
📅 **Academic Year:** 2024

**System Status:** ✅ Operational
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def admin_update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """🔄 **Update Database**

**Available Actions:**
1. Add new student
2. Update student information
3. Add new teacher
4. Update teacher information
5. Reset passwords

Please contact system administrator for database updates."""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    # ==================== SETTINGS ====================
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """⚙️ **Settings**

Choose option:"""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")],
        [InlineKeyboardButton("🔐 Change Password", callback_data="change_pass")],
        [InlineKeyboardButton("📞 Update Contact", callback_data="update_contact")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data="set_en")],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="set_am")],
        [InlineKeyboardButton("Oromiffa 🇪🇹", callback_data="set_or")],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select language:", reply_markup=reply_markup)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang_map = {"set_en": "en", "set_am": "am", "set_or": "or"}
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

async def handle_change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_pass = update.message.text.strip()
    if len(new_pass) < 6:
        await update.message.reply_text("❌ Too short! Min 6 chars:")
        return
    
    user_id = context.user_data.get('user_id')
    db.update_password(user_id, new_pass)
    
    await update.message.reply_text("✅ Password changed!")
    await show_main_menu_callback_from_message(update, context)
    context.user_data.pop('expecting', None)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """ℹ️ **Help & Support**

**Available Commands:**
/start - Start the bot and login

**Features:**
• Student portal with grades, attendance
• Teacher portal with student management
• Admin portal with analytics
• Contact sharing system
• Automatic quizzes
• Multi-language support

**Need Help?**
Contact school administration."""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    # ==================== CALLBACK HANDLER ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Language selection
    if data.startswith("lang_"):
        await handle_language_selection(update, context)
        return
    
    # Set language
    if data in ["set_en", "set_am", "set_or"]:
        await set_language(update, context)
        return
    
    # Quiz handling
    if data.startswith("quiz_"):
        await start_quiz(update, context)
        return
    
    if data.startswith("answer_"):
        await handle_quiz_answer(update, context)
        return
    
    # Attendance handling
    if data.startswith("attendance_"):
        parts = data.split("_")
        if len(parts) >= 3:
            status = parts[1]
            student_id = parts[2]
            await query.edit_message_text(f"✅ Attendance marked: {student_id} - {status}")
            await show_main_menu_callback(update, context)
        return
    
    # Check login for protected routes
    protected_routes = [
        "materials", "schedule", "grades", "attendance", "homework",
        "library", "teachers", "profile", "my_students", "assign_hw", 
        "record_grades", "take_attendance", "teaching_materials", 
        "teacher_schedule", "analytics", "manage_students", "manage_teachers", 
        "curriculum", "manage_classes", "update_db", "share_contact", 
        "view_contacts", "settings", "take_quiz", "help"
    ]
    
    if data in protected_routes and not context.user_data.get('logged_in'):
        await query.edit_message_text("❌ Please login with /start")
        return
    
    # Main routes
    if data == "main_menu":
        await show_main_menu_callback(update, context)
    
    elif data == "logout":
        context.user_data.clear()
        await query.edit_message_text("✅ Logged out. Use /start to login again.")
    
    # Contact
    elif data == "share_contact":
        await share_contact(update, context)
    elif data == "request_contact":
        await request_contact(update, context)
    elif data == "enter_contact":
        await enter_contact(update, context)
    elif data == "view_contacts":
        await view_contacts(update, context)
    elif data == "update_contact":
        await request_contact(update, context)
    
    # Settings
    elif data == "settings":
        await show_settings(update, context)
    elif data == "change_lang":
        await change_lang(update, context)
    elif data == "change_pass":
        await change_pass(update, context)
    elif data == "help":
        await help_command(update, context)
    
    # Student features
    elif data == "materials":
        await student_materials(update, context)
    elif data == "schedule":
        await student_schedule(update, context)
    elif data == "grades":
        await student_grades(update, context)
    elif data == "attendance":
        await student_attendance(update, context)
    elif data == "homework":
        await student_homework(update, context)
    elif data == "take_quiz":
        await take_quiz(update, context)
    elif data == "library":
        await student_library(update, context)
    elif data == "teachers":
        await student_teachers(update, context)
    elif data == "profile":
        await student_profile(update, context)
    
    # Teacher features
    elif data == "my_students":
        await teacher_students(update, context)
    elif data == "assign_hw":
        await teacher_assign_hw(update, context)
    elif data == "record_grades":
        await teacher_record_grades(update, context)
    elif data == "take_attendance":
        await teacher_take_attendance(update, context)
    elif data in ["teaching_materials", "teacher_schedule"]:
        await query.edit_message_text(f"✅ {data.replace('_', ' ').title()} feature")
        await show_main_menu_callback(update, context)
    
    # Admin features
    elif data == "analytics":
        await admin_analytics(update, context)
    elif data == "manage_students":
        await query.edit_message_text("✅ Student management portal")
        await show_main_menu_callback(update, context)
    elif data == "update_db":
        await admin_update_db(update, context)
    elif data in ["manage_teachers", "curriculum", "manage_classes"]:
        await query.edit_message_text(f"✅ {data.replace('_', ' ').title()} feature")
        await show_main_menu_callback(update, context)
    
    else:
        await query.edit_message_text("❌ Unknown command")
        # ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        await handle_contact(update, context)
        return
    
    if not update.message.text:
        return
    
    expecting = context.user_data.get('expecting')
    
    if expecting == 'user_id':
        await handle_user_id(update, context)
    elif expecting == 'password':
        await handle_password(update, context)
    elif expecting == 'new_password':
        await handle_new_password(update, context)
    elif expecting == 'manual_contact':
        await handle_manual_contact(update, context)
    elif expecting == 'change_password':
        await handle_change_password(update, context)
    elif expecting == 'initial_contact':
        pass
    else:
        await update.message.reply_text("Please use /start to begin or use the menu buttons.")

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or use /start to restart."
            )
    except:
        pass

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("ℹ️  Set it: export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("ℹ️  Or create .env file with TELEGRAM_BOT_TOKEN")
        return
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Error handler
        app.add_error_handler(error_handler)
        
        # Command handlers
        app.add_handler(CommandHandler("start", start_command))
        
        # Callback query handler
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        print("=" * 50)
        print("✅ Sunday School Telegram Bot Started")
        print(f"🤖 Developer: {DEVELOPER_NAME}")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Start polling
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logger.exception("Bot startup failed")

if __name__ == '__main__':
    main()
    