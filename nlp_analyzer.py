import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SimpleNLPAnalyzer:
    """Упрощенный NLP анализатор без тяжелых зависимостей для Render"""
    
    def __init__(self):
        # Эмоциональные словари
        self.positive_words = [
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'рад', 'счастлив',
            'доволен', 'удовлетворен', 'восторг', 'восхищение', 'люблю', 'нравится',
            'успех', 'победа', 'достижение', 'горжусь', 'весело', 'интересно',
            'спокойно', 'умиротворен', 'гармония', 'благодарен', 'спасибо'
        ]
        
        self.negative_words = [
            'плохо', 'ужасно', 'отвратительно', 'грустно', 'печально', 'тоскливо',
            'злой', 'сердит', 'раздражен', 'бесит', 'ненавижу', 'разочарован',
            'устал', 'утомлен', 'измотан', 'выгорел', 'стресс', 'тревога',
            'беспокойство', 'страх', 'боюсь', 'паника', 'депрессия', 'апатия',
            'одиночество', 'покинутый', 'брошенный', 'неудача', 'провал', 'стыдно'
        ]
        
        # Темы и ключевые слова
        self.topics = {
            'работа': ['работа', 'начальник', 'коллега', 'дедлайн', 'проект', 'офис', 'зарплата'],
            'семья': ['семья', 'родители', 'дети', 'муж', 'жена', 'отношения', 'брак'],
            'здоровье': ['здоровье', 'болезнь', 'боль', 'врач', 'больница', 'симптом', 'лекарство'],
            'финансы': ['деньги', 'финансы', 'долг', 'кредит', 'зарплата', 'бюджет', 'бедный'],
            'учеба': ['учеба', 'экзамен', 'сессия', 'преподаватель', 'студент', 'зачет'],
            'отношения': ['друг', 'подруга', 'любовь', 'расставание', 'ссора', 'измена']
        }
        
        # Кризисные слова (триггеры)
        self.crisis_keywords = [
            'суицид', 'самоубийство', 'покончить', 'свести счеты', 'не хочу жить',
            'все бессмысленно', 'конец', 'надоело жить', 'устал от жизни'
        ]
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Простой анализ текста без ML моделей.
        Подходит для Render (не требует torch/transformers).
        """
        if not text or len(text.strip()) < 3:
            return self._get_empty_result()
        
        try:
            text_lower = text.lower()
            
            # 1. Анализ тональности
            sentiment = self._analyze_sentiment(text_lower)
            
            # 2. Определение тем
            topics = self._extract_topics(text_lower)
            
            # 3. Уровень стресса
            stress_level = self._calculate_stress_level(text_lower, sentiment)
            
            # 4. Проверка на кризис
            is_crisis, crisis_words = self._check_crisis(text_lower)
            
            # 5. Эмоции
            emotions = self._detect_emotions(text_lower)
            
            result = {
                'success': True,
                'text_original': text,
                'sentiment': sentiment,
                'topics': topics,
                'stress_level': stress_level,
                'is_crisis': is_crisis,
                'crisis_words': crisis_words,
                'emotions': emotions,
                'word_count': len(text.split()),
                'analysis_time': datetime.utcnow().isoformat(),
                'model': 'simple_render_analyzer_v1'
            }
            
            logger.debug(f"NLP анализ: {sentiment['label']}, стресс: {stress_level}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка NLP анализа: {e}")
            return self._get_error_result(str(e))
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Простой анализ тональности"""
        positive_matches = sum(1 for word in self.positive_words if word in text)
        negative_matches = sum(1 for word in self.negative_words if word in text)
        
        total_matches = positive_matches + negative_matches
        
        if total_matches == 0:
            return {'label': 'NEUTRAL', 'score': 0.5, 'positive': 0, 'negative': 0}
        
        positive_score = positive_matches / total_matches
        negative_score = negative_matches / total_matches
        
        if positive_score > negative_score:
            label = 'POSITIVE'
            score = positive_score
        elif negative_score > positive_score:
            label = 'NEGATIVE'
            score = negative_score
        else:
            label = 'NEUTRAL'
            score = 0.5
        
        return {
            'label': label,
            'score': round(score, 2),
            'positive': positive_matches,
            'negative': negative_matches
        }
    
    def _extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """Извлечение тем"""
        topics_found = []
        
        for topic_name, keywords in self.topics.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                confidence = min(1.0, len(found_keywords) * 0.3)
                topics_found.append({
                    'name': topic_name,
                    'keywords_found': found_keywords,
                    'confidence': round(confidence, 2)
                })
        
        # Сортируем по уверенности
        topics_found.sort(key=lambda x: x['confidence'], reverse=True)
        return topics_found[:3]  # Возвращаем только 3 основные темы
    
    def _calculate_stress_level(self, text: str, sentiment: Dict[str, Any]) -> int:
        """Расчет уровня стресса (1-10)"""
        base_level = 5
        
        # Влияние тональности
        if sentiment['label'] == 'NEGATIVE':
            base_level += 2
            if sentiment['score'] > 0.7:
                base_level += 1
        
        # Влияние кризисных слов
        is_crisis, crisis_words = self._check_crisis(text)
        if is_crisis:
            base_level += 3
        
        # Влияние отрицательных слов
        negative_count = sentiment['negative']
        if negative_count > 3:
            base_level += 1
        if negative_count > 5:
            base_level += 1
        
        # Влияние восклицательных знаков
        if text.count('!') > 2:
            base_level += 1
        
        # Ограничиваем диапазон 1-10
        return max(1, min(10, base_level))
    
    def _check_crisis(self, text: str) -> tuple:
        """Проверка на кризисные слова"""
        found_words = []
        for word in self.crisis_keywords:
            if word in text:
                found_words.append(word)
        
        return len(found_words) > 0, found_words
    
    def _detect_emotions(self, text: str) -> List[str]:
        """Определение основных эмоций"""
        emotions_map = {
            'радость': ['рад', 'счастлив', 'восторг', 'восхищение', 'весело'],
            'грусть': ['грустно', 'печально', 'тоскливо', 'плакать', 'слезы'],
            'гнев': ['злой', 'сердит', 'раздражен', 'бесит', 'ненавижу'],
            'страх': ['боюсь', 'страшно', 'испуг', 'ужас', 'паника'],
            'спокойствие': ['спокоен', 'умиротворен', 'тишина', 'мир', 'расслаблен']
        }
        
        detected = []
        for emotion, keywords in emotions_map.items():
            for keyword in keywords:
                if keyword in text and emotion not in detected:
                    detected.append(emotion)
                    break
        
        return detected
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Пустой результат"""
        return {
            'success': False,
            'error': 'Текст слишком короткий',
            'sentiment': {'label': 'NEUTRAL', 'score': 0.5},
            'topics': [],
            'stress_level': 5,
            'is_crisis': False,
            'crisis_words': [],
            'emotions': []
        }
    
    def _get_error_result(self, error: str) -> Dict[str, Any]:
        """Результат с ошибкой"""
        return {
            'success': False,
            'error': error,
            'sentiment': {'label': 'ERROR', 'score': 0},
            'topics': [],
            'stress_level': 5,
            'is_crisis': False,
            'crisis_words': [],
            'emotions': []
        }
    
    def get_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Текстовое резюме анализа"""
        if not analysis_result.get('success'):
            return "Анализ не выполнен."
        
        parts = []
        
        # Тональность
        sentiment = analysis_result['sentiment']
        if sentiment['label'] == 'POSITIVE':
            parts.append("📈 **Позитивный настрой**")
        elif sentiment['label'] == 'NEGATIVE':
            parts.append("📉 **Негативный настрой**")
        else:
            parts.append("📊 **Нейтральный настрой**")
        
        # Стресс
        stress = analysis_result.get('stress_level', 5)
        if stress >= 8:
            parts.append(f"🔴 **Высокий стресс:** {stress}/10")
        elif stress >= 6:
            parts.append(f"🟡 **Средний стресс:** {stress}/10")
        else:
            parts.append(f"🟢 **Низкий стресс:** {stress}/10")
        
        # Темы
        topics = analysis_result.get('topics', [])
        if topics:
            topic_names = [t['name'] for t in topics[:2]]
            parts.append(f"🏷️ **Темы:** {', '.join(topic_names)}")
        
        # Кризис
        if analysis_result.get('is_crisis'):
            parts.append("🚨 **Обнаружены тревожные слова**")
        
        return "\n".join(parts)

# Создаем глобальный экземпляр
nlp_analyzer = SimpleNLPAnalyzer()
