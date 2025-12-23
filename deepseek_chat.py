import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DeepSeekChatRender:
    """Клиент DeepSeek API оптимизированный для Render"""
    
    def __init__(self):
        self.api_key = os.environ.get('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        
        if self.api_key:
            logger.info("✅ DeepSeek API ключ найден")
        else:
            logger.warning("⚠️ DeepSeek API ключ не найден. Чат с ИИ будет недоступен.")
    
    async def get_response(self, user_message: str, context: list = None) -> Dict[str, Any]:
        """
        Получить ответ от DeepSeek API.
        Возвращает словарь с результатом.
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API ключ не настроен',
                'response': 'Функция чата с ИИ временно недоступна. Пожалуйста, настройте API ключ в админ-панели.'
            }
        
        # Подготавливаем сообщения
        messages = []
        
        # Системный промпт
        system_prompt = """Ты - MindMate, поддерживающий психологический помощник. 
Твоя задача - оказывать эмоциональную поддержку, помогать разбираться в чувствах 
и давать практические советы по управлению стрессом.

Будь:
1. Эмпатичным и понимающим
2. Профессиональным, но дружелюбным
3. Конкретным в советах
4. Поддерживающим в трудных ситуациях

Не давай медицинских диагнозов. В кризисных ситуациях направляй к профессионалам.
Говори на русском языке."""
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Добавляем контекст если есть
        if context:
            messages.extend(context[-5:])  # Берем последние 5 сообщений
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": user_message})
        
        # Подготавливаем запрос
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            # Используем aiohttp для асинхронного запроса
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        response_text = result["choices"][0]["message"]["content"]
                        
                        # Форматируем для Telegram
                        formatted_response = self._format_for_telegram(response_text)
                        
                        return {
                            'success': True,
                            'response': formatted_response,
                            'raw_response': response_text,
                            'usage': result.get("usage", {}),
                            'model': result.get("model", self.model)
                        }
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API ошибка {response.status}: {error_text}")
                        
                        return {
                            'success': False,
                            'error': f"API ошибка {response.status}",
                            'response': "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
                        }
                        
        except asyncio.TimeoutError:
            logger.error("Таймаут запроса к DeepSeek API")
            return {
                'success': False,
                'error': 'Timeout',
                'response': "Извините, сервис отвечает слишком долго. Попробуйте позже."
            }
            
        except Exception as e:
            logger.error(f"Ошибка DeepSeek API: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Извините, произошла техническая ошибка. Пожалуйста, попробуйте позже."
            }
    
    def _format_for_telegram(self, text: str) -> str:
        """Форматирование текста для Telegram"""
        if not text:
            return ""
        
        # Ограничиваем длину
        if len(text) > 4000:
            text = text[:3900] + "\n\n... (сообщение сокращено)"
        
        # Заменяем Markdown на HTML для Telegram
        # Telegram поддерживает подмножество HTML
        formatted = text
        
        # Заменяем **жирный** на <b>жирный</b>
        import re
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted)
        
        # Заменяем *курсив* на <i>курсив</i>
        formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted)
        
        # Заменяем `код` на <code>код</code>
        formatted = re.sub(r'`(.*?)`', r'<code>\1</code>', formatted)
        
        # Экранируем специальные символы HTML
        formatted = formatted.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Восстанавливаем теги
        formatted = formatted.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        formatted = formatted.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        formatted = formatted.replace('&lt;code&gt;', '<code>').replace('&lt;/code&gt;', '</code>')
        
        return formatted
    
    async def stream_response(self, user_message: str) -> str:
        """Упрощенный streaming (для будущих улучшений)"""
        result = await self.get_response(user_message)
        
        if result['success']:
            return result['response']
        else:
            return result['response']  # Уже содержит сообщение об ошибке
    
    def is_available(self) -> bool:
        """Проверка доступности API"""
        return bool(self.api_key)

# Создаем глобальный экземпляр
deepseek_chat = DeepSeekChatRender()
