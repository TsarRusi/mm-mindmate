import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import aiohttp
import asyncio
from datetime import datetime
import uuid

from config import settings
from database import ChatSession, db_manager

logger = logging.getLogger(__name__)

class DeepSeekChat:
    """Клиент для работы с DeepSeek API."""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model = settings.DEEPSEEK_MODEL
        
        if not self.api_key:
            logger.warning("DeepSeek API ключ не указан. Чат с ИИ будет недоступен.")
        
        # Системные промпты для разных режимов
        self.system_prompts = {
            "psychologist": """Ты - эмпатичный психолог-консультант MindMate. Твоя задача - оказывать психологическую поддержку, помогать разбираться в эмоциях и давать практические советы.

ПРАВИЛА:
1. Будь поддерживающим, но профессиональным
2. Не ставь диагнозы
3. Не давай медицинских рекомендаций
4. В кризисных ситуациях направляй к специалистам
5. Используй техники КПТ, осознанности и эмоционального интеллекта
6. Задавай уточняющие вопросы
7. Говори на русском языке

СТИЛЬ:
- Дружелюбный, но не фамильярный
- Используй эмодзи умеренно 😊
- Говори на "ты"
- Будь конкретным в советах

Если пользователь упоминает суицидальные мысли, немедленно предоставь контакты экстренных служб.""",
            
            "coach": """Ты - лайф-коуч и ментор. Помогаешь ставить цели, преодолевать препятствия и развивать навыки.

Фокус на:
- Постановке SMART-целей
- Преодолении прокрастинации
- Развитии привычек
- Управлении временем
- Личностном росте""",
            
            "friend": """Ты - поддерживающий друг, который всегда готов выслушать. Не давай советов, если не просят. В основном слушай, сопереживай и задавашь вопросы.

Твой девиз: "Я здесь, чтобы слушать тебя.""""
        }
    
    async def create_session(self, user_id: int, mode: str = "psychologist") -> Optional[str]:
        """Создать новую сессию чата."""
        if not self.api_key:
            return None
        
        try:
            session_uuid = str(uuid.uuid4())
            system_prompt = self.system_prompts.get(mode, self.system_prompts["psychologist"])
            
            # Создаем сессию в БД
            with db_manager.session_scope() as session:
                chat_session = ChatSession(
                    user_id=user_id,
                    session_uuid=session_uuid,
                    system_prompt=system_prompt,
                    context_messages=[{"role": "system", "content": system_prompt}]
                )
                session.add(chat_session)
                session.flush()
            
            logger.info(f"Создана сессия {session_uuid} для пользователя {user_id}")
            return session_uuid
            
        except Exception as e:
            logger.error(f"Ошибка создания сессии: {e}")
            return None
    
    async def send_message(self, session_uuid: str, user_message: str, 
                          user_id: int = None) -> Dict[str, Any]:
        """Отправить сообщение в DeepSeek и получить ответ."""
        if not self.api_key:
            return self._error_response("DeepSeek API не настроен")
        
        try:
            # Получаем сессию из БД
            with db_manager.session_scope() as session:
                chat_session = session.query(ChatSession)\
                    .filter(ChatSession.session_uuid == session_uuid)\
                    .filter(ChatSession.is_active == True)\
                    .first()
                
                if not chat_session:
                    return self._error_response("Сессия не найдена или завершена")
                
                # Добавляем сообщение пользователя в контекст
                context = chat_session.context_messages or []
                context.append({"role": "user", "content": user_message})
                
                # Обрезаем контекст, если слишком длинный
                if len(context) > 20:
                    context = [context[0]] + context[-19:]  # Сохраняем system prompt
                
                # Отправляем запрос к API
                response_text, usage = await self._call_deepseek_api(context)
                
                # Добавляем ответ ассистента в контекст
                context.append({"role": "assistant", "content": response_text})
                
                # Обновляем сессию
                chat_session.context_messages = context
                chat_session.message_count += 1
                chat_session.token_count += usage.get('total_tokens', 0)
                chat_session.total_cost += self._calculate_cost(usage)
                chat_session.last_message_at = datetime.utcnow()
                
                session.flush()
                
                # Форматируем ответ
                formatted_response = self._format_response(response_text)
                
                logger.info(f"Сообщение обработано для сессии {session_uuid}, токенов: {usage.get('total_tokens', 0)}")
                
                return {
                    "success": True,
                    "session_id": session_uuid,
                    "response": formatted_response,
                    "raw_response": response_text,
                    "usage": usage,
                    "message_count": chat_session.message_count,
                    "estimated_cost": chat_session.total_cost
                }
                
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)
            return self._error_response(f"Ошибка: {str(e)}")
    
    async def _call_deepseek_api(self, messages: List[Dict[str, str]]) -> tuple[str, Dict[str, Any]]:
        """Вызов DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                
                result = await response.json()
                
                response_text = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                
                return response_text, usage
    
    async def stream_response(self, session_uuid: str, user_message: str) -> AsyncGenerator[str, None]:
        """Стриминг ответа от DeepSeek (для более плавного взаимодействия)."""
        if not self.api_key:
            yield "⚠️ DeepSeek API не настроен"
            return
        
        try:
            # Получаем сессию
            with db_manager.session_scope() as session:
                chat_session = session.query(ChatSession)\
                    .filter(ChatSession.session_uuid == session_uuid)\
                    .filter(ChatSession.is_active == True)\
                    .first()
                
                if not chat_session:
                    yield "Сессия не найдена"
                    return
                
                context = chat_session.context_messages or []
                context.append({"role": "user", "content": user_message})
                
                # Вызываем API с stream=True
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": context,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "stream": True
                }
                
                timeout = aiohttp.ClientTimeout(total=60)
                full_response = ""
                
                async with aiohttp.ClientSession(timeout=timeout) as http_session:
                    async with http_session.post(self.api_url, headers=headers, json=data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            yield f"Ошибка API: {response.status}"
                            return
                        
                        async for line in response.content:
                            if line:
                                line_text = line.decode('utf-8').strip()
                                
                                # Пропускаем пустые строки и data: [DONE]
                                if not line_text or line_text == "data: [DONE]":
                                    continue
                                
                                # Обрабатываем JSON
                                if line_text.startswith("data: "):
                                    json_str = line_text[6:]  # Убираем "data: "
                                    try:
                                        data_chunk = json.loads(json_str)
                                        delta = data_chunk.get("choices", [{}])[0].get("delta", {})
                                        
                                        if "content" in delta:
                                            chunk = delta["content"]
                                            full_response += chunk
                                            yield chunk
                                            
                                    except json.JSONDecodeError:
                                        continue
                
                # Сохраняем полный ответ в БД
                context.append({"role": "assistant", "content": full_response})
                
                chat_session.context_messages = context
                chat_session.message_count += 1
                chat_session.last_message_at = datetime.utcnow()
                session.commit()
                
        except Exception as e:
            logger.error(f"Ошибка стриминга: {e}")
            yield f"Ошибка: {str(e)}"
    
    def end_session(self, session_uuid: str) -> bool:
        """Завершить сессию."""
        try:
            with db_manager.session_scope() as session:
                chat_session = session.query(ChatSession)\
                    .filter(ChatSession.session_uuid == session_uuid)\
                    .first()
                
                if chat_session:
                    chat_session.is_active = False
                    chat_session.ended_at = datetime.utcnow()
                    session.flush()
                    logger.info(f"Сессия {session_uuid} завершена")
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка завершения сессии: {e}")
            return False
    
    def get_session_info(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о сессии."""
        try:
            with db_manager.session_scope() as session:
                chat_session = session.query(ChatSession)\
                    .filter(ChatSession.session_uuid == session_uuid)\
                    .first()
                
                if chat_session:
                    return {
                        "session_id": chat_session.session_uuid,
                        "user_id": chat_session.user_id,
                        "message_count": chat_session.message_count,
                        "token_count": chat_session.token_count,
                        "total_cost": chat_session.total_cost,
                        "is_active": chat_session.is_active,
                        "created_at": chat_session.created_at.isoformat() if chat_session.created_at else None,
                        "last_message_at": chat_session.last_message_at.isoformat() if chat_session.last_message_at else None,
                        "duration": chat_session.duration
                    }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о сессии: {e}")
            return None
    
    def _format_response(self, text: str) -> str:
        """Форматирование ответа для Telegram."""
        # Заменяем Markdown на HTML для Telegram
        formatted = text
        
        # Заменяем **жирный** на <b>жирный</b>
        formatted = formatted.replace("**", "<b>").replace("<b>", "</b>", 1)
        
        # Заменяем *курсив* на <i>курсив</i>
        formatted = formatted.replace("*", "<i>").replace("<i>", "</i>", 1)
        
        # Ограничиваем длину (Telegram имеет ограничения)
        if len(formatted) > 4000:
            formatted = formatted[:3900] + "\n\n... (сообщение сокращено)"
        
        return formatted
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Расчет стоимости запроса."""
        # Примерные цены DeepSeek (уточните актуальные)
        # Предположим: $0.14 за 1M токенов ввода, $0.28 за 1M токенов вывода
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        prompt_cost = (prompt_tokens / 1_000_000) * 0.14
        completion_cost = (completion_tokens / 1_000_000) * 0.28
        
        return round(prompt_cost + completion_cost, 6)
    
    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Стандартный ответ при ошибке."""
        return {
            "success": False,
            "error": error_msg,
            "response": f"⚠️ {error_msg}\n\nПопробуйте позже или используйте другие функции бота.",
            "usage": {}
        }
    
    def get_available_modes(self) -> List[Dict[str, str]]:
        """Получить список доступных режимов чата."""
        return [
            {"id": "psychologist", "name": "🧠 Психолог", "description": "Профессиональная поддержка и консультация"},
            {"id": "coach", "name": "🎯 Коуч", "description": "Помощь в постановке целей и развитии"},
            {"id": "friend", "name": "👥 Друг", "description": "Просто поговорить и выговориться"}
        ]

# Создаем глобальный экземпляр клиента DeepSeek
deepseek_chat = DeepSeekChat()