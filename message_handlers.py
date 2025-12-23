import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import settings, CRISIS_CONTACTS
from database import db_manager, User, MoodLog
from nlp_analyzer import nlp_analyzer
from deepseek_chat import deepseek_chat
from keyboards.main import (
    get_main_menu, get_mood_keyboard, get_ai_chat_menu,
    get_exercises_menu, get_settings_menu, get_statistics_menu,
    get_crisis_help_keyboard, get_confirmation_keyboard, get_back_keyboard
)
from utils import format_date, generate_mood_chart

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
MOOD_INPUT, AI_CHAT, EXERCISE_SESSION, SETTINGS = range(4)

class MessageHandlers:
    """Обработчики сообщений бота."""
    
    def __init__(self):
        self.user_sessions = {}  # Временное хранилище сессий пользователей
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        user = update.effective_user
        
        # Получаем или создаем пользователя
        db_user = db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Приветственное сообщение
        welcome_text = f"""
        🧠 *Добро пожаловать в MindMate, {user.first_name}!* 🧠

Я твой персональный помощник для заботы о ментальном здоровье.

*Что я умею:*
📊 *Отслеживать настроение* — записывай и анализируй свои эмоции
💬 *Поговорить с ИИ* — поддерживающий диалог с искусственным интеллектом
🧘 *Практики и упражнения* — техники для снижения тревоги и стресса
📈 *Аналитика и статистика* — понимание своих эмоциональных паттернов
⚙️ *Персональные настройки* — настрой бота под себя

*Важно:* Я не заменяю профессионального психолога, но могу быть первой линией поддержки.

Выбери действие в меню ниже:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Новый пользователь: {user.id} - {user.username}")
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик главного меню."""
        text = update.message.text
        
        if text == "📊 Записать настроение":
            await self.ask_mood(update, context)
            
        elif text == "💬 Поговорить с ИИ":
            await self.show_ai_menu(update, context)
            
        elif text == "🧘 Упражнения":
            await self.show_exercises_menu(update, context)
            
        elif text == "📈 Статистика":
            await self.show_statistics_menu(update, context)
            
        elif text == "⚙️ Настройки":
            await self.show_settings_menu(update, context)
            
        elif text == "❓ Помощь":
            await self.show_help(update, context)
            
        else:
            await update.message.reply_text(
                "Используй меню для навигации 👆",
                reply_markup=get_main_menu()
            )
    
    async def ask_mood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Спросить о настроении."""
        question = """
        *Как твое настроение сегодня?*

Оцени от 1 до 10, где:
1 — совсем плохо 😢
5 — нейтрально 😐  
10 — отлично! 🤩

Или выбери «Описать текстом» чтобы подробнее рассказать о своем дне.
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                question,
                reply_markup=get_mood_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                question,
                reply_markup=get_mood_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return MOOD_INPUT
    
    async def handle_mood_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик оценки настроения."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("mood_"):
            if query.data == "mood_text":
                await query.edit_message_text(
                    "✍️ *Опиши свой день и настроение своими словами:*\n\n"
                    "Что произошло сегодня? Что ты чувствуешь?",
                    parse_mode=ParseMode.MARKDOWN
                )
                context.user_data['awaiting_mood_text'] = True
                return MOOD_INPUT
            
            # Извлекаем оценку
            score = int(query.data.split("_")[1])
            user_id = update.effective_user.id
            
            # Сохраняем оценку
            mood_log = db_manager.add_mood_log(
                user_id=user_id,
                mood_score=score,
                user_message=f"Оценка настроения: {score}/10"
            )
            
            # Формируем ответ
            emoji = self._get_mood_emoji(score)
            response = f"{emoji} *Записал твою оценку: {score}/10*\n\n"
            
            if score <= 3:
                response += "Похоже, сегодня непростой день. Помни, что тяжелые эмоции — это нормально. 💙\n\n"
                response += "Хочешь попробовать успокаивающее упражнение?"
            elif score <= 6:
                response += "Спасибо, что поделился! Каждый день — это возможность для роста. 🌱\n\n"
                response += "Можешь добавить описание дня для более детального анализа."
            else:
                response += "Отлично! Рад, что у тебя хороший день! 😊\n\n"
                response += "Записывай и хорошие дни — это поможет понять, что приносит тебе радость."
            
            await query.edit_message_text(
                response,
                reply_markup=get_main_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_mood_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстового описания настроения."""
        if not context.user_data.get('awaiting_mood_text'):
            return
        
        user_text = update.message.text
        user_id = update.effective_user.id
        
        # Анализируем текст
        analysis = nlp_analyzer.analyze_text(user_text)
        
        # Проверяем на кризисные слова
        if analysis.get('is_crisis', False):
            await self.handle_crisis_situation(update, context, user_text, analysis)
            return
        
        # Сохраняем в БД
        mood_score = analysis.get('stress_level', 5)  # Используем стресс как индикатор
        if mood_score >= 8:
            mood_score = 3  # Высокий стресс = плохое настроение
        elif mood_score <= 3:
            mood_score = 8  # Низкий стресс = хорошее настроение
        
        db_manager.add_mood_log(
            user_id=user_id,
            mood_score=mood_score,
            user_message=user_text,
            ai_analysis=analysis
        )
        
        # Формируем ответ
        response = nlp_analyzer.get_text_summary(analysis)
        response += "\n\n"
        
        # Добавляем рекомендации
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            response += "*Рекомендации:*\n"
            for rec in recommendations[:3]:  # Ограничиваем 3 рекомендациями
                response += f"• {rec}\n"
        
        response += "\nЗаписал твои мысли! Возвращайся в главное меню."
        
        await update.message.reply_text(
            response,
            reply_markup=get_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Сбрасываем флаг
        context.user_data.pop('awaiting_mood_text', None)
    
    async def handle_crisis_situation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     user_text: str, analysis: Dict[str, Any]) -> None:
        """Обработка кризисной ситуации."""
        crisis_response = """
        🚨 *Обнаружены тревожные слова в твоем сообщении*
        
        Важно понимать: ты не один, и помощь доступна.
        
        *Немедленная помощь:*
        """
        
        # Добавляем контакты
        for category, contacts in CRISIS_CONTACTS.items():
            crisis_response += f"\n*{category.upper()}:*\n"
            for contact in contacts[:2]:  # Ограничиваем 2 контактами на категорию
                crisis_response += f"{contact}\n"
        
        crisis_response += "\n*Пожалуйста, обратись за помощью.* Ты важен и заслуживаешь поддержки. 💙"
        
        # Отправляем кризисное сообщение
        if update.message:
            await update.message.reply_text(
                crisis_response,
                reply_markup=get_crisis_help_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                crisis_response,
                reply_markup=get_crisis_help_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Логируем кризисную ситуацию
        logger.warning(f"Кризисная ситуация у пользователя {update.effective_user.id}: {user_text[:100]}")
        
        # Оповещаем администраторов
        await self.notify_admins(update, context, user_text)
    
    async def notify_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           user_text: str) -> None:
        """Уведомить администраторов о кризисной ситуации."""
        user = update.effective_user
        admin_message = f"""
        ⚠️ *КРИЗИСНАЯ СИТУАЦИЯ*
        
        Пользователь: {user.first_name} (@{user.username})
        ID: {user.id}
        
        Сообщение: {user_text[:200]}
        
        Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        for admin_id in settings.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
    
    async def show_ai_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать меню чата с ИИ."""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "💬 *Поговорить с ИИ*\n\n"
                "Выбери режим общения:\n\n"
                "🧠 *Психолог* — профессиональная поддержка и консультация\n"
                "🎯 *Коуч* — помощь в постановке целей и развитии\n"
                "👥 *Друг* — просто поговорить и выговориться",
                reply_markup=get_ai_chat_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "💬 *Поговорить с ИИ*\n\n"
                "Выбери режим общения:",
                reply_markup=get_ai_chat_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def start_ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Начать чат с ИИ."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("ai_mode_"):
            mode = query.data.split("_")[2]  # psychologist/coach/friend
            user_id = update.effective_user.id
            
            # Создаем сессию
            session_id = await deepseek_chat.create_session(user_id, mode)
            
            if not session_id:
                await query.edit_message_text(
                    "⚠️ *Сервис ИИ временно недоступен*\n\n"
                    "Попробуйте позже или используйте другие функции бота.",
                    reply_markup=get_back_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Сохраняем session_id в контекст пользователя
            context.user_data['ai_session_id'] = session_id
            context.user_data['ai_mode'] = mode
            
            # Формируем приветствие в зависимости от режима
            greetings = {
                "psychologist": "🧠 *Привет! Я твой виртуальный психолог.*\n\nЯ здесь, чтобы выслушать, поддержать и помочь разобраться в твоих переживаниях.\n\nРасскажи, что у тебя на душе?",
                "coach": "🎯 *Привет! Я твой лайф-коуч.*\n\nПомогу с постановкой целей, преодолением препятствий и личностным ростом.\n\nНад чем хочешь поработать?",
                "friend": "👥 *Привет! Я готов выслушать тебя.*\n\nИногда просто поговорить — уже большая помощь.\n\nРасскажи, как твои дела?"
            }
            
            await query.edit_message_text(
                greetings.get(mode, greetings["psychologist"]),
                reply_markup=get_back_keyboard("ai_end_session"),
                parse_mode=ParseMode.MARKDOWN
            )
            
            return AI_CHAT
    
    async def handle_ai_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик сообщений в чате с ИИ."""
        if not context.user_data.get('ai_session_id'):
            await update.message.reply_text(
                "Сессия завершена. Начни новую в меню.",
                reply_markup=get_main_menu()
            )
            return
        
        user_message = update.message.text
        session_id = context.user_data['ai_session_id']
        
        # Показываем индикатор набора
        typing_msg = await update.message.reply_text("🤔 Думаю...")
        
        try:
            # Отправляем сообщение в DeepSeek
            response = await deepseek_chat.send_message(session_id, user_message)
            
            if response.get('success'):
                await typing_msg.edit_text(
                    response['response'],
                    parse_mode=ParseMode.HTML
                )
            else:
                await typing_msg.edit_text(
                    f"⚠️ {response.get('error', 'Произошла ошибка')}\n\n"
                    "Попробуйте позже или используйте другие функции бота.",
                    reply_markup=get_back_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Ошибка в AI чате: {e}")
            await typing_msg.edit_text(
                "⚠️ Произошла ошибка при обработке запроса.\n"
                "Попробуйте позже.",
                reply_markup=get_back_keyboard()
            )
    
    async def end_ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Завершить чат с ИИ."""
        query = update.callback_query
        await query.answer()
        
        session_id = context.user_data.get('ai_session_id')
        if session_id:
            deepseek_chat.end_session(session_id)
            context.user_data.pop('ai_session_id', None)
            context.user_data.pop('ai_mode', None)
        
        await query.edit_message_text(
            "💬 *Чат завершен*\n\n"
            "Надеюсь, наш разговор был полезен для тебя!\n"
            "Возвращайся в любое время.",
            reply_markup=get_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_exercises_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать меню упражнений."""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🧘 *Упражнения и практики*\n\n"
                "Выбери категорию:\n\n"
                "🌬️ *Дыхание* — техники для успокоения нервной системы\n"
                "🧠 *Осознанность* — практики присутствия в моменте\n"
                "💭 *КПТ техники* — работа с мыслями и убеждениями\n"
                "📝 *Дневник* — упражнения для самопознания\n"
                "🎵 *Медитация* — аудио-практики\n"
                "🏃 *Тело* — телесные практики",
                reply_markup=get_exercises_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "🧘 *Упражнения и практики*",
                reply_markup=get_exercises_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_exercise(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать конкретное упражнение."""
        query = update.callback_query
        await query.answer()
        
        exercise_type = query.data.split("_")[1]
        
        exercises = {
            "breathing": {
                "title": "🌬️ Техника дыхания 4-7-8",
                "description": "Простая техника для быстрого снижения тревоги и улучшения сна.",
                "steps": [
                    "1. Сядьте удобно, спина прямая",
                    "2. Вдохните через нос на 4 счета",
                    "3. Задержите дыхание на 7 счетов",
                    "4. Медленно выдохните через рот на 8 счетов",
                    "5. Повторите 4-5 раз"
                ],
                "tips": [
                    "• Делайте утром и вечером",
                    "• Можно делать лежа перед сном",
                    "• Не форсируйте, если чувствуете дискомфорт"
                ]
            },
            # ... другие упражнения
        }
        
        exercise = exercises.get(exercise_type, exercises["breathing"])
        
        response = f"*{exercise['title']}*\n\n"
        response += f"{exercise['description']}\n\n"
        response += "*Шаги:*\n" + "\n".join(exercise['steps']) + "\n\n"
        response += "*Советы:*\n" + "\n".join(exercise['tips'])
        
        await query.edit_message_text(
            response,
            reply_markup=get_back_keyboard("back_to_exercises"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_statistics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать меню статистики."""
        user_id = update.effective_user.id
        
        # Получаем базовую статистику
        stats = db_manager.get_user_mood_stats(user_id, days=30)
        
        stats_text = f"""
        📊 *Твоя статистика*

        *За последние 30 дней:*
        • Всего записей: {stats['total_records']}
        • Среднее настроение: {stats['avg_mood']:.1f}/10
        """
        
        if stats['recent_logs']:
            stats_text += "\n*Последние записи:*\n"
            for log in stats['recent_logs'][:3]:
                date = format_date(log['created_at'])
                score = log['mood_score'] or "?"
                stats_text += f"• {date}: {score}/10\n"
        
        stats_text += "\nВыбери период для детальной статистики:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                stats_text,
                reply_markup=get_statistics_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                stats_text,
                reply_markup=get_statistics_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать меню настроек."""
        settings_text = """
        ⚙️ *Настройки*

        Настрой бота под себя:

        🔔 *Напоминания* — время ежедневных чек-инов
        🌙 *Тема* — светлая/темная (в будущем)
        🗣️ *Язык* — русский/английский
        📊 *Данные* — управление твоей информацией
        👤 *Профиль* — информация о тебе
        🛡️ *Безопасность* — настройки приватности
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                settings_text,
                reply_markup=get_settings_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                settings_text,
                reply_markup=get_settings_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать помощь."""
        help_text = """
        ❓ *Помощь и поддержка*

        *Частые вопросы:*

        🤔 *Как работает бот?*
        — Бот помогает отслеживать настроение, дает упражнения для ментального здоровья и предоставляет возможность поговорить с ИИ.

        🔒 *Конфиденциальность*
        — Все данные шифруются и хранятся анонимно. Мы не передаем информацию третьим лицам.

        🆘 *Кризисная помощь*
        — Если ты в кризисной ситуации, используй кнопку "Помощь" или напиши /crisis

        💰 *Стоимость*
        — Базовые функции бесплатны. Расширенные возможности доступны по подписке.

        *Команды:*
        /start — Начать работу с ботом
        /help — Эта справка
        /crisis — Кризисная помощь
        /stats — Быстрая статистика
        /settings — Настройки

        *Поддержка:* @support_username
        """
        
        await update.message.reply_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback запросов."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            await query.edit_message_text(
                "Возвращаемся в главное меню...",
                reply_markup=get_main_menu()
            )
            
        elif query.data == "back_to_exercises":
            await self.show_exercises_menu(update, context)
            
        elif query.data.startswith("exercise_"):
            await self.show_exercise(update, context)
            
        elif query.data.startswith("ai_mode_"):
            await self.start_ai_chat(update, context)
            
        elif query.data == "ai_end_session":
            await self.end_ai_chat(update, context)
            
        elif query.data.startswith("mood_"):
            await self.handle_mood_score(update, context)
            
        elif query.data.startswith("stats_"):
            await self.show_statistics_detail(update, context)
            
        elif query.data.startswith("settings_"):
            await self.show_settings_detail(update, context)
            
        elif query.data.startswith("crisis_"):
            await self.handle_crisis_callback(update, context)
            
        elif query.data == "crisis_ok":
            await query.edit_message_text(
                "Хорошо, что ты в порядке! 💙\n\n"
                "Помни, я всегда здесь, если понадобится помощь.",
                reply_markup=get_main_menu()
            )
    
    async def show_statistics_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать детальную статистику."""
        query = update.callback_query
        period = query.data.split("_")[1]
        
        user_id = update.effective_user.id
        days_map = {"week": 7, "month": 30, "all": 365}
        days = days_map.get(period, 30)
        
        stats = db_manager.get_user_mood_stats(user_id, days)
        
        response = f"📊 *Статистика за {period}*\n\n"
        
        if stats['avg_mood']:
            response += f"• Среднее настроение: *{stats['avg_mood']:.1f}/10*\n"
        response += f"• Всего записей: *{stats['total_records']}*\n\n"
        
        if stats['recent_logs']:
            response += "*Последние оценки:*\n"
            for log in stats['recent_logs'][:5]:
                date = format_date(log['created_at'])
                score = log['mood_score'] or "?"
                message = log['user_message'][:30] + "..." if log['user_message'] and len(log['user_message']) > 30 else log['user_message'] or ""
                response += f"• {date}: {score}/10 {message}\n"
        
        # Генерируем график (в будущем)
        # chart_url = await generate_mood_chart(user_id, days)
        # if chart_url:
        #     response += f"\n[График настроения]({chart_url})"
        
        await query.edit_message_text(
            response,
            reply_markup=get_back_keyboard("back_to_stats"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_settings_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать детальные настройки."""
        query = update.callback_query
        setting = query.data.split("_")[1]
        
        settings_texts = {
            "reminders": "🔔 *Напоминания*\n\nУстанови время для ежедневных чек-инов настроения.",
            "theme": "🌙 *Тема*\n\nВыбери светлую или темную тему (в будущих обновлениях).",
            "language": "🗣️ *Язык*\n\nВыбери язык интерфейса.",
            "data": "📊 *Данные*\n\nУправляй своей информацией: экспорт, удаление.",
            "profile": "👤 *Профиль*\n\nИнформация о твоем аккаунте.",
            "security": "🛡️ *Безопасность*\n\nНастройки приватности и безопасности."
        }
        
        response = settings_texts.get(setting, "Настройка не найдена")
        response += "\n\n*Эта функция в разработке* 🚧"
        
        await query.edit_message_text(
            response,
            reply_markup=get_back_keyboard("back_to_settings"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_crisis_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback для кризисной помощи."""
        query = update.callback_query
        crisis_type = query.data.split("_")[1]
        
        crisis_responses = {
            "phones": "📞 *Телефоны доверия:*\n\n" + "\n".join(CRISIS_CONTACTS['telephone']),
            "online": "🌐 *Онлайн помощь:*\n\n" + "\n".join(CRISIS_CONTACTS['online']),
            "emergency": "🚨 *Экстренные службы:*\n\n" + "\n".join(CRISIS_CONTACTS['emergency']),
            "find_help": "🏥 *Как найти психолога:*\n\n1. Обратись в поликлинику по месту жительства\n2. Используй сервисы: Яндекс.Здоровье, DocDoc\n3. Ищи специалистов на платформах: B17, Change"
        }
        
        response = crisis_responses.get(crisis_type, "Информация не найдена")
        response += "\n\n💙 *Ты не один. Помощь рядом.*"
        
        await query.edit_message_text(
            response,
            reply_markup=get_crisis_help_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик неизвестных команд."""
        await update.message.reply_text(
            "Я не понял эту команду. Используй меню для навигации 👆",
            reply_markup=get_main_menu()
        )
    
    def _get_mood_emoji(self, score: int) -> str:
        """Получить эмодзи для оценки настроения."""
        if score <= 3:
            return "😢"
        elif score <= 5:
            return "😔"
        elif score <= 7:
            return "😐"
        elif score <= 9:
            return "😊"
        else:
            return "🤩"

# Создаем экземпляр обработчиков
handlers = MessageHandlers()