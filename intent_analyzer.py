# intent_analyzer.py
import re
import random
from datetime import datetime

class IntentAnalyzer:
    def __init__(self):
        self.setup_intent_patterns()
        self.setup_spelling_variations()
    
    def setup_spelling_variations(self):
        """إعداد الاختلافات الإملائية الشائعة"""
        self.spelling_variations = {
            'مرحبا': ['مرحبا', 'مرحباً', 'مرحبه', 'مرحبة', 'مروحبا', 'مرحابا'],
            'اهلا': ['اهلا', 'أهلا', 'اهلاً', 'أهلاً', 'اهله', 'اهلاا', 'اهلين'],
            'شكرا': ['شكرا', 'شكراً', 'شكرة', 'شكر', 'ثانك يو', 'ثنكس', 'شكرن'],
            'رحلة': ['رحلة', 'رحله', 'رحلات', 'رحل', 'رحت', 'رحتة', 'رحلي'],
            'طيران': ['طيران', 'طيرن', 'طيران', 'طيارة', 'طياره', 'طير'],
            'مساعدة': ['مساعدة', 'مساعده', 'مساعد', 'مساعدت', 'مساعدتي', 'ساعدني'],
            'سفر': ['سفر', 'سافر', 'اسافر', 'سفري', 'سفرنا'],
            'حجز': ['حجز', 'احجز', 'حجوزات', 'حاجز', 'حجز']
        }
    
    def setup_intent_patterns(self):
        """إعداد أنماط النوايا والردود"""
        
        # أنماط التحيات والردود
        self.greeting_patterns = {
            'patterns': [
                r'مرحبا', r'اهلا', r'السلام عليكم', r'اهلاً', r'مرحباً', r'اهلين',
                r'hello', r'hi\b', r'hey', r'good morning', r'good evening', r'السلام',
                r'صباح الخير', r'مساء الخير'
            ],
            'responses': [
                "مرحباً بك! 🌟 كيف يمكنني مساعدتك في حجز رحلتك اليوم؟",
                "أهلاً وسهلاً! 🎯 أخبرني عن رحلتك القادمة",
                "وعليكم السلام ورحمة الله 🌺 أنا هنا لمساعدتك في البحث عن أفضل الرحلات",
                "أهلاً بك! ✈️ مستعد لمساعدتك في حجز طيرانك"
            ]
        }
        
        # أنماط الشكر والردود
        self.thanks_patterns = {
            'patterns': [
                r'شكرا', r'مشكور', r'يعطيك العافية', r'thank you', r'thanks', r'متشكر',
                r'جزاك الله خيرا', r'تسلم', r'ما قصرت', r'شكراً', r'ثانكس'
            ],
            'responses': [
                "العفو! 😊 سعيد لمساعدتك. هل تحتاج أي شيء آخر؟",
                "دائماً بخدمتك! 🚀 هل تريد البحث عن رحلة أخرى؟",
                "شكراً لك! 🌷 أنا هنا دائماً لمساعدتك في حجوزات الطيران",
                "لا شكر على واجب! 💫 تفضل إذا كان لديك أي استفسار آخر"
            ]
        }
        
        # أنماط الأسئلة العامة
        self.general_questions = {
            'patterns': [
                r'كيف الحال', r'كيفك', r'كيف حالك', r'شلونك', r'how are you',
                r'what\'s up', r'كيف الامور', r'اخبارك', r'شونك'
            ],
            'responses': [
                "الحمدلله بخير! 🌟 مستعد لمساعدتك في البحث عن أفضل عروض الطيران",
                "بخير والحمدلله! 🎯 هل تريد حجز رحلة إلى وجهة معينة؟",
                "كل شيء ممتاز! 🌺 أخبرني عن خطط سفرك",
                "أفضل ما يمكن! ✈️ كيف يمكنني مساعدتك اليوم؟"
            ]
        }
        
        # أنماط طلب المساعدة
        self.help_patterns = {
            'patterns': [
                r'مساعدة', r'help', r'بدي مساعده', r'كيف استخدم', r'شرح',
                r'ما تقدري', r'ماذا تفعل', r'شلون اسوي', r'بدي مساعدة', r'ساعدني'
            ],
            'responses': [
                "أنا مساعدك الذكي لحجز الطيران! ✈️\n\n"
                "يمكنني مساعدتك في:\n"
                "• البحث عن رحلات طيران\n"
                "• مقارنة الأسعار\n"
                "• العثور على أفضل العروض\n\n"
                "📝 مثال: \"أريد رحلة من الرياض إلى دبي يوم 15 ديسمبر\"",
                
                "مساعد الطيران الخاص بك! 🌍\n\n"
                "أخبرني ب:\n"
                "• المدينة الأصل\n"
                "• المدينة الوجهة\n"
                "• تاريخ السفر\n\n"
                "وسأبحث لك عن أفضل الخيارات! 🎯",
                
                "سأكون سعيداً بمساعدتك! 😊\n\n"
                "ما عليك سوى إخباري:\n"
                "📍 من أي مدينة تريد السفر؟\n"
                "📍 إلى أي مدينة تريد الذهاب؟\n"
                "📅 متى تريد السفر؟\n\n"
                "وسأعثر لك على أفضل الرحلات!"
            ]
        }
        
        # أنماط الرحلات (تتطلب Amadeus)
        self.flight_intent_patterns = [
            r'رحلة', r'طيران', r'سفر', r'سافر', r'حجز', r'رحله', r'طياره', r'سفره',
            r'flight', r'travel', r'book', r'trip', r'fly', r'flying',
            r'اريد اروح', r'بدي اسافر', r'ابغى رحلة', r'عايز اسافر', r'ابي اروح',
            r'من (.+) الى (.+)', r'من (.+) لـ (.+)', r'من (.+) ل (.+)',
            r'الى (.+) من (.+)', r'لـ (.+) من (.+)',
            r'سفر من', r'رحله من', r'طيران من',
            r'اريد اطير', r'بدي اطير', r'ابغى اطير'
        ]
    
    def normalize_spelling(self, text):
        """توحيد الكتابة للتعامل مع الأخطاء الإملائية"""
        if not text:
            return ""
            
        normalized_text = text.lower()
        
        # استبدال الاختلافات الإملائية
        for correct, variations in self.spelling_variations.items():
            for variation in variations:
                if variation in normalized_text:
                    normalized_text = normalized_text.replace(variation, correct)
        
        return normalized_text
    
    def calculate_text_quality(self, text):
        """حساب جودة النص وتحديد إذا كان غير مفهوم"""
        if not text or len(text.strip()) < 2:
            return {'quality': 'very_low', 'score': 0.1}
        
        text = text.strip()
        
        # حساب نسبة الأحرف العربية/الإنجليزية
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(text) - arabic_chars - english_chars
        
        total_chars = len(text)
        
        # إذا كانت معظم الأحرف غير عربية/إنجليزية
        if other_chars / total_chars > 0.7:
            return {'quality': 'gibberish', 'score': 0.1}
        
        # إذا كان النص قصير جداً ويحتوي على أحرف عشوائية
        if total_chars < 4 and re.search(r'[^a-zA-Z\u0600-\u06FF\s]', text):
            return {'quality': 'random', 'score': 0.2}
        
        # إذا كان النص يحتوي على تكرارات عشوائية
        if self._has_random_repetition(text):
            return {'quality': 'repetitive', 'score': 0.3}
        
        # إذا كان النص مزيج عشوائي
        if self._is_random_mix(text):
            return {'quality': 'mixed_gibberish', 'score': 0.4}
        
        # نص مقبول
        return {'quality': 'acceptable', 'score': 0.8}
    
    def _has_random_repetition(self, text):
        """الكشف عن التكرارات العشوائية"""
        patterns = [
            r'(.)\1{4,}',  # تكرار حرف 5 مرات أو أكثر
            r'([a-z])\1{4,}',  # تكرار حرف إنجليزي
            r'(\d)\1{4,}',  # تكرار رقم
        ]
        
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                return True
        return False
    
    def _is_random_mix(self, text):
        """الكشف عن المزج العشوائي"""
        # إذا كان النص مزيج من أحرف وارقام بدون معنى
        if len(text) < 8:
            return False
            
        random_patterns = [
            r'^[a-z0-9]{3,15}$',  # فقط أحرف إنجليزية وأرقام
            r'^[^a-zA-Z\u0600-\u06FF\s]{5,}$',  # لا يحتوي على أحرف عربية/إنجليزية
        ]
        
        for pattern in random_patterns:
            if re.match(pattern, text.lower()):
                return True
        
        # إذا كانت نسبة المسافات قليلة والنص طويل
        space_ratio = text.count(' ') / len(text)
        if len(text) > 20 and space_ratio < 0.1:
            return True
            
        return False
    
    def detect_gibberish_response(self, text_quality):
        """تحديد الرد المناسب للنص غير المفهوم"""
        quality = text_quality['quality']
        
        responses = {
            'very_low': "🤔 يبدو أن الرسالة فارغة أو قصيرة جداً. هل يمكنك إعادة كتابتها؟",
            'gibberish': "❌ لم أفهم هذه الرسالة. يبدو أنها تحتوي على رموز غير مفهومة.",
            'random': "⌨️ أعتقد أن هناك خطأ في الكتابة. هل يمكنك إعادة إرسال طلبك؟",
            'repetitive': "🔄 لاحظت تكراراً في النص. هل تقصد شيئاً محدداً؟",
            'mixed_gibberish': "📝 لم أتمكن من فهم رسالتك. جرب صياغتها بطريقة أخرى."
        }
        
        return responses.get(quality, "🤔 لم أفهم طلبك بشكل كامل. هل يمكنك توضيحه؟")
    
    def _check_patterns(self, text, patterns):
        """التحقق من وجود أنماط في النص"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def analyze_intent(self, text):
        """تحليل نية النص مع التعامل مع الأخطاء"""
        if not text or not text.strip():
            return {
                'intent': 'gibberish', 
                'confidence': 0.1,
                'response': "📝 يبدو أن الرسالة فارغة. هل يمكنك كتابة طلبك؟",
                'text_quality': {'quality': 'very_low', 'score': 0.1}
            }
        
        original_text = text.strip()
        
        # تحليل جودة النص أولاً
        text_quality = self.calculate_text_quality(original_text)
        
        # إذا كان النص غير مفهوم تماماً
        if text_quality['score'] < 0.3:
            return {
                'intent': 'gibberish',
                'confidence': text_quality['score'],
                'response': self.detect_gibberish_response(text_quality),
                'text_quality': text_quality
            }
        
        normalized_text = self.normalize_spelling(original_text)
        
        # التحقق من التحيات أولاً (أعلى أولوية)
        if self._check_patterns(normalized_text, self.greeting_patterns['patterns']):
            return {
                'intent': 'greeting',
                'confidence': 0.95,
                'response': random.choice(self.greeting_patterns['responses']),
                'text_quality': text_quality
            }
        
        # التحقق من الشكر
        if self._check_patterns(normalized_text, self.thanks_patterns['patterns']):
            return {
                'intent': 'thanks',
                'confidence': 0.90,
                'response': random.choice(self.thanks_patterns['responses']),
                'text_quality': text_quality
            }
        
        # التحقق من الأسئلة العامة
        if self._check_patterns(normalized_text, self.general_questions['patterns']):
            return {
                'intent': 'general_question',
                'confidence': 0.85,
                'response': random.choice(self.general_questions['responses']),
                'text_quality': text_quality
            }
        
        # التحقق من طلب المساعدة
        if self._check_patterns(normalized_text, self.help_patterns['patterns']):
            return {
                'intent': 'help',
                'confidence': 0.88,
                'response': random.choice(self.help_patterns['responses']),
                'text_quality': text_quality
            }
        
        # التحقق من نية البحث عن رحلة (أقل أولوية)
        if self._check_patterns(normalized_text, self.flight_intent_patterns):
            return {
                'intent': 'flight_search',
                'confidence': 0.80,
                'response': None,  # سيعالجها NLP العادي
                'text_quality': text_quality
            }
        
        # إذا لم يتطابق مع أي نمط ولكن النص مقبول
        # نعطي فرصة لـ NLP لمعالجته
        if text_quality['score'] >= 0.5:
            return {
                'intent': 'unknown_but_acceptable',
                'confidence': 0.4,
                'response': None,  # نترك لـ NLP المعالجة
                'text_quality': text_quality
            }
        
        # إذا كان النص غير مقبول ولم يتطابق مع أي نمط
        return {
            'intent': 'unclear',
            'confidence': 0.3,
            'response': "🤔 لم أفهم طلبك بشكل كامل. هل يمكنك إعادة صياغته؟\n\n"
                       "💡 يمكنني مساعدتك في:\n"
                       "• حجز الرحلات ✈️\n"
                       "• البحث عن عروض الطيران\n"
                       "• مقارنة الأسعار\n\n"
                       "📝 مثال: \"رحلة من الرياض إلى دبي يوم 20 ديسمبر\"",
            'text_quality': text_quality
        }
    
    def should_use_amadeus(self, intent_result, nlp_result):
        """تحديد ما إذا كان يجب استخدام Amadeus"""
        # لا تستخدم Amadeus إذا كان النص غير مفهوم
        if intent_result.get('intent') in ['gibberish', 'unclear']:
            return False
        
        # استخدام Amadeus إذا كانت النية بحث عن رحلة و NLP نجح
        if (intent_result.get('intent') == 'flight_search' and 
            nlp_result.get('success', False) and 
            nlp_result.get('query')):
            return True
            
        # أو إذا كان النص مقبولاً و NLP استطاع استخراج معلومات رحلة
        if (intent_result.get('intent') == 'unknown_but_acceptable' and 
            nlp_result.get('success', False) and 
            nlp_result.get('query')):
            return True
            
        return False