import re
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import logging

from config import settings

logger = logging.getLogger(__name__)

# Скачиваем необходимые ресурсы NLTK (только при первом запуске)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('sentiment/vader_lexicon')
    nltk.data.find('corpora/stopwords')
except LookupError:
    import nltk.downloader
    nltk.download('punkt')
    nltk.download('vader_lexicon')
    nltk.download('stopwords')
    nltk.download('punkt_tab')

class NLPAnalyzer:
    """Анализатор текста для определения эмоций, тем и уровня стресса."""
    
    def __init__(self, language: str = "russian"):
        self.language = language
        self.sia = SentimentIntensityAnalyzer()
        
        # Стоп-слова
        self.stop_words = set(stopwords.words('russian' if language == 'ru' else 'english'))
        
        # Ключевые слова для определения тем
        self.topic_keywords = {
            'работа': ['работа', 'начальник', 'коллега', 'дедлайн', 'проект', 'офис', 'зарплата', 
                      'совещание', 'задача', 'увольнение', 'карьера'],
            'семья': ['семья', 'родители', 'дети', 'муж', 'жена', 'брат', 'сестра', 'родственники',
                     'отношения', 'развод', 'брак', 'семейный'],
            'здоровье': ['здоровье', 'болезнь', 'боль', 'врач', 'больница', 'лекарство', 'симптом',
                        'усталость', 'сон', 'бессонница', 'диета', 'спорт'],
            'финансы': ['деньги', 'финансы', 'долг', 'кредит', 'зарплата', 'экономия', 'траты',
                       'бюджет', 'накопления', 'инвестиции', 'бедность'],
            'учеба': ['учеба', 'экзамен', 'сессия', 'преподаватель', 'студент', 'зачет', 'курсовая',
                     'диплом', 'лекция', 'образование', 'университет'],
            'одиночество': ['одиночество', 'одинокий', 'покинутый', 'изоляция', 'отвергнутый',
                           'покидать', 'бросить', 'покидать', 'нелюбимый'],
            'тревога': ['тревога', 'паника', 'страх', 'беспокойство', 'нервы', 'стресс', 'напряжение',
                       'волнение', 'испуг', 'фобия'],
            'депрессия': ['депрессия', 'апатия', 'тоска', 'грусть', 'безнадежность', 'отчаяние',
                         'печаль', 'меланхолия', 'подавленность', 'суицид'],
        }
        
        # Кризисные слова (триггеры для активации кризисного протокола)
        self.crisis_keywords = [
            'суицид', 'самоубийство', 'покончить', 'свести счеты', 'не хочу жить',
            'все бессмысленно', 'конец', 'надоело жить', 'устал от жизни',
            'лучше умереть', 'не вижу смысла', 'все плохо', 'нет выхода'
        ]
        
        logger.info(f"NLP анализатор инициализирован для языка: {language}")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Анализирует текст и возвращает результаты.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Словарь с результатами анализа
        """
        if not text or len(text.strip()) < 3:
            return self._empty_result()
        
        try:
            # Очистка текста
            cleaned_text = self._clean_text(text)
            
            # Базовый анализ
            sentiment = self._analyze_sentiment(cleaned_text)
            topics = self._extract_topics(cleaned_text)
            stress_level = self._calculate_stress_level(cleaned_text, sentiment)
            emotions = self._detect_emotions(cleaned_text)
            
            # Проверка на кризисные слова
            is_crisis, crisis_words = self._check_crisis_keywords(cleaned_text)
            
            # Дополнительные метрики
            word_count = len(cleaned_text.split())
            readability = self._calculate_readability(cleaned_text)
            
            result = {
                'text_original': text,
                'text_cleaned': cleaned_text,
                'sentiment': sentiment,
                'topics': topics,
                'stress_level': stress_level,
                'emotions': emotions,
                'is_crisis': is_crisis,
                'crisis_words_found': crisis_words,
                'metrics': {
                    'word_count': word_count,
                    'readability_score': readability,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'recommendations': self._generate_recommendations(
                    sentiment, topics, stress_level, is_crisis
                )
            }
            
            logger.debug(f"NLP анализ завершен: {result['sentiment']['label']}, стресс: {stress_level}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе текста: {e}", exc_info=True)
            return self._error_result(str(e))
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста."""
        # Удаляем ссылки, email, хэштеги
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\S*@\S*\s?', '', text)
        text = re.sub(r'#\S+', '', text)
        
        # Удаляем специальные символы, оставляем буквы, цифры и основные знаки препинания
        text = re.sub(r'[^\w\s.,!?;:()-]', ' ', text)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Приводим к нижнему регистру
        return text.lower()
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Анализ тональности текста."""
        try:
            # Используем TextBlob для русского/английского
            if self.language == 'ru':
                # Для русского используем VADER (работает лучше чем TextBlob)
                scores = self.sia.polarity_scores(text)
                compound = scores['compound']
                
                if compound >= 0.05:
                    label = "POSITIVE"
                elif compound <= -0.05:
                    label = "NEGATIVE"
                else:
                    label = "NEUTRAL"
                    
                return {
                    'label': label,
                    'compound': compound,
                    'positive': scores['pos'],
                    'neutral': scores['neu'],
                    'negative': scores['neg']
                }
            else:
                # Для английского TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
                
                if polarity > 0:
                    label = "POSITIVE"
                elif polarity < 0:
                    label = "NEGATIVE"
                else:
                    label = "NEUTRAL"
                    
                return {
                    'label': label,
                    'polarity': polarity,
                    'subjectivity': subjectivity
                }
                
        except Exception as e:
            logger.warning(f"Ошибка анализа тональности: {e}")
            return {'label': 'NEUTRAL', 'error': str(e)}
    
    def _extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """Извлечение тем из текста."""
        topics = []
        tokens = word_tokenize(text, language='russian' if self.language == 'ru' else 'english')
        
        for topic_name, keywords in self.topic_keywords.items():
            matches = []
            confidence = 0
            
            for keyword in keywords:
                if keyword in text:
                    matches.append(keyword)
                    # Увеличиваем уверенность за каждое совпадение
                    confidence += 0.3
            
            if matches:
                # Нормализуем уверенность
                confidence = min(1.0, confidence)
                topics.append({
                    'name': topic_name,
                    'keywords_found': matches,
                    'confidence': round(confidence, 2)
                })
        
        # Сортируем по уверенности
        topics.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Ограничиваем количество тем
        return topics[:5]
    
    def _calculate_stress_level(self, text: str, sentiment: Dict[str, Any]) -> int:
        """Расчет уровня стресса (1-10)."""
        stress_score = 5  # Нейтральный уровень
        
        # 1. Влияние тональности
        if sentiment.get('label') == 'NEGATIVE':
            compound = abs(sentiment.get('compound', 0) or sentiment.get('polarity', 0))
            if compound > 0.3:
                stress_score += 3
            elif compound > 0.1:
                stress_score += 2
            else:
                stress_score += 1
        
        # 2. Влияние тем
        topics = self._extract_topics(text)
        stress_topics = {'тревога', 'депрессия', 'одиночество', 'финансы'}
        
        for topic in topics:
            if topic['name'] in stress_topics:
                stress_score += 1
        
        # 3. Анализ слов тревоги
        anxiety_words = ['тревож', 'паник', 'страх', 'боюсь', 'нерв', 'стресс']
        anxiety_count = sum(1 for word in anxiety_words if word in text)
        stress_score += min(anxiety_count, 2)
        
        # 4. Длина и структура текста
        words = text.split()
        if len(words) < 10:  # Очень короткие сообщения часто указывают на подавленность
            stress_score += 1
        elif len(words) > 100:  # Очень длинные - на чрезмерное обдумывание
            stress_score += 1
        
        # 5. Использование восклицательных знаков
        if '!' in text and text.count('!') > 3:
            stress_score += 1
        
        # Ограничиваем диапазон 1-10
        return max(1, min(10, stress_score))
    
    def _detect_emotions(self, text: str) -> List[Dict[str, Any]]:
        """Определение эмоций в тексте."""
        emotions = []
        
        # Словарь эмоций и их ключевых слов
        emotion_dict = {
            'радость': ['рад', 'счастлив', 'ура', 'отлично', 'прекрасно', 'замечательно', 'восторг'],
            'грусть': ['грустно', 'печально', 'тоскливо', 'плакать', 'слезы', 'уныние'],
            'гнев': ['злой', 'сердит', 'раздражен', 'бесит', 'ненавижу', 'ярость', 'возмущен'],
            'страх': ['боюсь', 'страшно', 'испуг', 'ужас', 'паника', 'тревога'],
            'удивление': ['удивлен', 'неожиданно', 'ого', 'вау', 'невероятно', 'потрясающе'],
            'спокойствие': ['спокоен', 'умиротворен', 'тишина', 'мир', 'расслаблен', 'гармония'],
        }
        
        for emotion, keywords in emotion_dict.items():
            matches = []
            for keyword in keywords:
                if keyword in text:
                    matches.append(keyword)
            
            if matches:
                confidence = min(1.0, len(matches) * 0.2)
                emotions.append({
                    'name': emotion,
                    'keywords_found': matches,
                    'confidence': round(confidence, 2)
                })
        
        return emotions
    
    def _check_crisis_keywords(self, text: str) -> Tuple[bool, List[str]]:
        """Проверка на наличие кризисных слов."""
        found_words = []
        for keyword in self.crisis_keywords:
            if keyword in text:
                found_words.append(keyword)
        
        return len(found_words) > 0, found_words
    
    def _calculate_readability(self, text: str) -> float:
        """Расчет читабельности текста."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0
        
        words = text.split()
        if not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Простая метрика читабельности
        readability = 100 - (avg_sentence_length * 1.5 + avg_word_length * 10)
        return max(0, min(100, readability))
    
    def _generate_recommendations(self, sentiment: Dict[str, Any], 
                                 topics: List[Dict[str, Any]], 
                                 stress_level: int, 
                                 is_crisis: bool) -> List[str]:
        """Генерация рекомендаций на основе анализа."""
        recommendations = []
        
        if is_crisis:
            recommendations.append("⚠️ **Обнаружены тревожные слова.** Рекомендуется обратиться за профессиональной помощью.")
        
        if stress_level >= 8:
            recommendations.append("🧘 **Высокий уровень стресса.** Попробуйте технику дыхания 4-7-8.")
            
        if stress_level >= 6:
            recommendations.append("📝 **Записывайте мысли.** Ведение дневника помогает структурировать переживания.")
        
        if sentiment.get('label') == 'NEGATIVE':
            if any(topic['name'] in ['работа', 'финансы'] for topic in topics):
                recommendations.append("💼 **Проблемы на работе/с финансами.** Попробуйте технику 'разделение проблемы на части'.")
        
        if any(topic['name'] == 'одиночество' for topic in topics):
            recommendations.append("👥 **Чувство одиночества.** Рассмотрите возможность присоединиться к тематическим группам по интересам.")
        
        if not recommendations:
            recommendations.append("👍 **Продолжайте самонаблюдение.** Регулярная практика ведет к лучшему пониманию себя.")
        
        return recommendations
    
    def _empty_result(self) -> Dict[str, Any]:
        """Пустой результат при пустом тексте."""
        return {
            'text_original': '',
            'text_cleaned': '',
            'sentiment': {'label': 'NEUTRAL', 'compound': 0},
            'topics': [],
            'stress_level': 5,
            'emotions': [],
            'is_crisis': False,
            'crisis_words_found': [],
            'metrics': {
                'word_count': 0,
                'readability_score': 0,
                'timestamp': datetime.utcnow().isoformat()
            },
            'recommendations': ['Текст слишком короткий для анализа']
        }
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Результат при ошибке анализа."""
        return {
            'text_original': '',
            'text_cleaned': '',
            'sentiment': {'label': 'ERROR', 'error': error_msg},
            'topics': [],
            'stress_level': 5,
            'emotions': [],
            'is_crisis': False,
            'crisis_words_found': [],
            'metrics': {
                'word_count': 0,
                'readability_score': 0,
                'timestamp': datetime.utcnow().isoformat()
            },
            'recommendations': ['Произошла ошибка при анализе']
        }
    
    def get_text_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Получить текстовое резюме анализа."""
        if not analysis_result or 'sentiment' not in analysis_result:
            return "Анализ недоступен."
        
        sentiment = analysis_result['sentiment']
        stress = analysis_result.get('stress_level', 5)
        topics = analysis_result.get('topics', [])
        
        summary_parts = []
        
        # Тональность
        if sentiment.get('label') == 'POSITIVE':
            summary_parts.append("📈 **Позитивный настрой**")
        elif sentiment.get('label') == 'NEGATIVE':
            summary_parts.append("📉 **Негативный настрой**")
        else:
            summary_parts.append("📊 **Нейтральный настрой**")
        
        # Уровень стресса
        if stress >= 8:
            summary_parts.append(f"🔴 **Высокий стресс:** {stress}/10")
        elif stress >= 6:
            summary_parts.append(f"🟡 **Повышенный стресс:** {stress}/10")
        elif stress <= 4:
            summary_parts.append(f"🟢 **Низкий стресс:** {stress}/10")
        else:
            summary_parts.append(f"⚪ **Средний стресс:** {stress}/10")
        
        # Темы
        if topics:
            main_topics = [t['name'] for t in topics[:3]]
            summary_parts.append(f"🏷️ **Основные темы:** {', '.join(main_topics)}")
        
        # Кризисный флаг
        if analysis_result.get('is_crisis', False):
            summary_parts.append("🚨 **Обнаружены тревожные сигналы**")
        
        return "\n".join(summary_parts)

# Создаем глобальный экземпляр анализатора
nlp_analyzer = NLPAnalyzer(language=settings.LANGUAGE)