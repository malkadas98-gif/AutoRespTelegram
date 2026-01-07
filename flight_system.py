# flight_system.py
import os
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class FlightSystem:
    def __init__(self, app=None, db_session=None):
        self.app = app
        self.db_session = db_session
        self.cities_loaded = False
        self.airlines_loaded = False
        self.months_loaded = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """تهيئة التطبيق"""
        self.app = app
        try:
            from models import db
            self.db_session = db.session
            # سنقوم بتحميل البيانات عند الحاجة بدلاً من تحميلها فوراً
        except ImportError as e:
            print(f"❌ لا يمكن تحميل النماذج من قاعدة البيانات: {e}")
            raise
    
    def ensure_data_loaded(self):
        """التأكد من تحميل البيانات عند الحاجة"""
        if not hasattr(self, 'cities') or not self.cities_loaded:
            self.load_cities_from_db()
        if not hasattr(self, 'airlines') or not self.airlines_loaded:
            self.load_airlines_from_db()
        if not hasattr(self, 'months') or not self.months_loaded:
            self.load_months_from_db()
    
    def load_all_data_from_db(self):
        """تحميل جميع البيانات من قاعدة البيانات"""
        try:
            if not self.db_session:
                raise Exception("لا يوجد اتصال بقاعدة البيانات")
                
            self.load_cities_from_db()
            self.load_airlines_from_db()
            self.load_months_from_db()
            print("✅ تم تحميل البيانات من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات من قاعدة البيانات: {e}")
            raise
    
    def load_cities_from_db(self):
        """تحميل المدن من قاعدة البيانات"""
        try:
            from models import City
            cities = self.db_session.query(City).filter_by(is_active=True).all()
            if not cities:
                raise Exception("لا توجد مدن في قاعدة البيانات")
                
            self.cities = {}
            # also build mapping city_name -> [iata_codes] to help get_all_city_airports
            self.city_name_to_iatas = {}
            for city in cities:
                self.cities[city.iata_code] = {
                    'arabic_name': city.arabic_name,
                    'english_name': city.english_name,
                    'country_arabic': city.country.arabic_name if city.country else 'غير معروف',
                    'country_english': city.country.english_name if city.country else 'Unknown'
                }
                key = (city.arabic_name or '').strip().lower()
                if key:
                    self.city_name_to_iatas.setdefault(key, []).append(city.iata_code)
            self.cities_loaded = True
            print(f"✅ تم تحميل {len(self.cities)} مدينة من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحميل المدن: {e}")
            raise
    
    def load_airlines_from_db(self):
        """تحميل شركات الطيران من قاعدة البيانات"""
        try:
            from models import Airline
            airlines = self.db_session.query(Airline).filter_by(is_active=True).all()
            if not airlines:
                raise Exception("لا توجد شركات طيران في قاعدة البيانات")
                
            self.airlines = {}
            for airline in airlines:
                self.airlines[airline.iata_code] = {
                    'arabic_name': airline.arabic_name,
                    'english_name': airline.english_name,
                    'icao_code': airline.icao_code,
                    'country': airline.country.arabic_name if airline.country else 'غير معروف'
                }
            self.airlines_loaded = True
            print(f"✅ تم تحميل {len(self.airlines)} شركة طيران من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحميل شركات الطيران: {e}")
            raise
    
    def load_months_from_db(self):
        """تحميل الأشهر من قاعدة البيانات"""
        try:
            from models import Month
            months = self.db_session.query(Month).filter_by(is_active=True).all()
            if not months:
                raise Exception("لا توجد أشهر في قاعدة البيانات")
                
            self.months = {month.arabic_name: str(month.month_number).zfill(2) for month in months}
            self.months_loaded = True
            print(f"✅ تم تحميل {len(self.months)} شهر من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحميل الأشهر: {e}")
            raise
    
    def get_city_info(self, iata_code):
        """الحصول على معلومات المدينة من قاعدة البيانات"""
        try:
            self.ensure_data_loaded()
            
            city_info = self.cities.get(iata_code)
            if not city_info:
                # البحث في قاعدة البيانات مباشرة
                from models import City
                city = self.db_session.query(City).filter_by(iata_code=iata_code, is_active=True).first()
                if city:
                    city_info = {
                        'arabic_name': city.arabic_name,
                        'english_name': city.english_name,
                        'country_arabic': city.country.arabic_name if city.country else 'غير معروف',
                        'country_english': city.country.english_name if city.country else 'Unknown'
                    }
                    self.cities[iata_code] = city_info
                else:
                    raise Exception(f"المدينة برمز {iata_code} غير موجودة في قاعدة البيانات")
            
            return city_info
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على معلومات المدينة {iata_code}: {e}")
            raise
    
    def get_airline_info(self, iata_code):
        """الحصول على معلومات شركة الطيران"""
        try:
            self.ensure_data_loaded()
            
            airline_info = self.airlines.get(iata_code)
            if not airline_info:
                # البحث في قاعدة البيانات مباشرة
                from models import Airline
                airline = self.db_session.query(Airline).filter_by(iata_code=iata_code, is_active=True).first()
                if airline:
                    airline_info = {
                        'arabic_name': airline.arabic_name,
                        'english_name': airline.english_name,
                        'icao_code': airline.icao_code,
                        'country': airline.country.arabic_name if airline.country else 'غير معروف'
                    }
                    self.airlines[iata_code] = airline_info
                else:
                    # إرجاع قيمة افتراضيه بدل رفع استثناء حتى لا يتعطل العرض
                    airline_info = {
                        'arabic_name': iata_code,
                        'english_name': iata_code,
                        'icao_code': '',
                        'country': 'غير معروف'
                    }
            return airline_info
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على معلومات الشركة {iata_code}: {e}")
            raise

    def get_all_city_airports(self, city_name_or_iata):
        """
        إرجاع كل مطارات المدينة — حتى لو أرسل المستخدم رمز IATA أو اسم غير دقيق.
        الذكاء هنا: استخراج اسم المدينة الأساسي ثم البحث عن كل المطارات.
        """
        try:
            self.ensure_data_loaded()

            if not city_name_or_iata:
                return []

            search = city_name_or_iata.strip().lower()

            # إذا كان IATA مباشرة
            if len(search) == 3:
                try:
                    city_info = self.get_city_info(search.upper())
                    base_name = self._extract_city_base_name(city_info['arabic_name'])
                except:
                    base_name = search
            else:
                base_name = self._extract_city_base_name(search)

            # البحث عن كل المطارات بالمدينة
            matching = []
            for iata_code, info in self.cities.items():
                city_ar = self._extract_city_base_name(info['arabic_name']).lower()
                city_en = self._extract_city_base_name(info['english_name']).lower()

                if base_name in city_ar or city_ar in base_name:
                    matching.append(iata_code)

                if base_name in city_en or city_en in base_name:
                    matching.append(iata_code)

            # fallback
            if not matching:
                matching = [search.upper()]

            return list(dict.fromkeys(matching))

        except Exception as e:
            print(f"❌ خطأ get_all_city_airports: {e}")
            return [city_name_or_iata.upper()]

    def _find_all_city_airports(self, iata_code):
            """
            إيجاد جميع مطارات المدينة بناءً على رمز IATA معين
            """
            try:
                # الحصول على معلومات المدينة من الرمز
                city_info = self.get_city_info(iata_code)
                if not city_info:
                    return [iata_code]
                
                city_arabic_name = city_info.get('arabic_name', '').strip().lower()
                if not city_arabic_name:
                    return [iata_code]
                
                # البحث عن جميع المطارات التي تحمل نفس اسم المدينة
                all_city_airports = []
                for code, info in self.cities.items():
                    if info.get('arabic_name', '').strip().lower() == city_arabic_name:
                        all_city_airports.append(code)
                
                return all_city_airports if all_city_airports else [iata_code]
                
            except Exception as e:
                print(f"❌ خطأ في إيجاد مطارات المدينة لـ {iata_code}: {e}")
                return [iata_code]
   
   
    def format_date_arabic(self, date_str):
        """تنسيق التاريخ بالعربية"""
        try:
            self.ensure_data_loaded()
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day = date_obj.day
            month_number = date_obj.month
            
            # البحث عن اسم الشهر العربي من قاعدة البيانات
            month_arabic = None
            for arabic_name, month_num in self.months.items():
                if int(month_num) == month_number:
                    month_arabic = arabic_name
                    break
            
            if not month_arabic:
                month_arabic = "غير معروف"
            
            return f"{day} {month_arabic}"
            
        except Exception as e:
            print(f"❌ خطأ في تنسيق التاريخ: {e}")
            return date_str
    
    def get_amadeus_token(self):
        """الحصول على token من Amadeus"""
        try:
            AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
            AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
            AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': AMADEUS_CLIENT_ID,
                'client_secret': AMADEUS_CLIENT_SECRET
            }
            resp = requests.post(AMADEUS_AUTH_URL, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()['access_token']
        except Exception as e:
            raise Exception(f"فشل في الحصول على token: {str(e)}")
    
    def search_flights_safe(self, origin, destination, date, adults=1):
        """
        البحث عن الرحلات مع دعم عدة مطارات لنفس المدينة.
        يرجع أفضل رحلة مباشرة لكل مطار وجهة.
        """
        try:
            token = self.get_amadeus_token()
            headers = {'Authorization': f'Bearer {token}'}

            # اجلب كل المطارات للمدينة الأصل والمدينة الوجهة
            origin_airports = self.get_all_city_airports(origin)
            destination_airports = self.get_all_city_airports(destination)

            print(f"🛫 مطارات المغادرة: {origin_airports}")
            print(f"🛬 مطارات الوصول: {destination_airports}")

            # إذا لم نجد مطارات متعددة للمدينة الوجهة، نحاول البحث بشكل مختلف
            if len(destination_airports) == 1:
                print(f"⚠️ وجدت مطار واحد فقط لـ {destination}، أحاول البحث عن مطارات إضافية...")
                # محاولة إيجاد مطارات إضافية بنفس اسم المدينة
                additional_airports = self._find_additional_airports(destination)
                if additional_airports:
                    destination_airports.extend(additional_airports)
                    print(f"✅ وجدت مطارات إضافية: {additional_airports}")

            all_flights = []

            # التأكد من صلاحية التاريخ
            today = datetime.now().date()
            flight_date = datetime.strptime(date, '%Y-%m-%d').date()
            if flight_date <= today:
                new_date = today + timedelta(days=7)
                date = new_date.strftime('%Y-%m-%d')

            AMADEUS_FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

            # إرسال طلب لكل تركيبة origin x destination
            for org in origin_airports:
                for dest in destination_airports:
                    print(f"🔍 البحث عن الرحلات: {org} → {dest}")

                    params = {
                        'originLocationCode': org,
                        'destinationLocationCode': dest,
                        'departureDate': date,
                        'adults': adults,
                        'max': 10,
                        'currencyCode': 'USD'
                    }

                    try:
                        resp = requests.get(AMADEUS_FLIGHT_SEARCH_URL, headers=headers, params=params, timeout=20)
                        if resp.status_code == 200:
                            flights_chunk = resp.json().get('data', [])
                            print(f"✅ وجدت {len(flights_chunk)} رحلة للمسار {org} → {dest}")
                            
                            for f in flights_chunk:
                                f['_origin_query'] = org
                                f['_destination_query'] = dest
                            all_flights.extend(flights_chunk)
                        else:
                            print(f"⚠️ خطأ API للمسار {org} → {dest}: {resp.status_code}")

                    except Exception as e:
                        print(f"⚠️ فشل الاتصال للمسار {org} → {dest}: {e}")
                        continue

            print(f"📊 إجمالي الرحلات الموجودة: {len(all_flights)}")

            # إرجاع جميع الرحلات التي تم العثور عليها
            final_flights = all_flights

            return {
                'flights_data': final_flights,
                'origin_airports': origin_airports,
                'destination_airports': destination_airports
            }

        except Exception as e:
            print(f"❌ خطأ عام في البحث: {e}")
            return {
                'flights_data': [],
                'origin_airports': [],
                'destination_airports': []
            }

    def _find_additional_airports(self, city_name):
            """
            البحث عن مطارات إضافية لنفس المدينة
            """
            try:
                # قائمة المطارات المعروفة للمدن الرئيسية
                city_airports_map = {
                    'دبي': ['DXB', 'DWC'],
                    'dubai': ['DXB', 'DWC'],
                    'دبي آل مكتوم': ['DWC'],
                    'dubai al maktoum': ['DWC'],
                    'الرياض': ['RUH'],
                    'riyadh': ['RUH'],
                    'جدة': ['JED'],
                    'jeddah': ['JED']
                }
                
                search_name = city_name.strip().lower()
                for city_pattern, airports in city_airports_map.items():
                    if search_name in city_pattern.lower() or city_pattern.lower() in search_name:
                        return airports
                
                return []
                
            except Exception as e:
                print(f"❌ خطأ في البحث عن مطارات إضافية: {e}")
                return []
  
  
    def _extract_city_base_name(self, city_name):
        """
        استخراج اسم المدينة الأساسي من نص قد يحتوي على كلمة مطار أو تفاصيل إضافية.
        مثل:
        - دبي – مطار آل مكتوم
        - مطار دبي الدولي
        - Dubai Al Maktoum Airport
        """
        try:
            if not city_name:
                return city_name

            name = city_name.lower().strip()

            # إزالة كلمة "مطار"
            for remove_word in ["مطار", "airport", "international"]:
                name = name.replace(remove_word, "")

            # تقسيم إذا كان فيه شرطات
            name = name.split("-")[0]
            name = name.split("–")[0]

            return name.strip()

        except:
            return city_name

  
    def _extract_basic_flight_info(self, flight):
        """
        استخلاص معلومات أساسية من كائن flight (من Amadeus) لإعادة استخدامها
        """
        itineraries = flight.get('itineraries', [{}])[0]
        segments = itineraries.get('segments', [])
        if not segments:
            return None

        first_segment = segments[0]
        last_segment = segments[-1]

        dep_iata_code = first_segment.get('departure', {}).get('iataCode', '')
        arr_iata_code = last_segment.get('arrival', {}).get('iataCode', '')

        # determine stops
        stops = max(0, len(segments) - 1)
        is_direct = stops == 0

        # price
        price_info = flight.get('price', {})
        price_str = price_info.get('total', 'غير معروف')
        try:
            price_val = float(price_str) if price_str != 'غير معروف' else float('inf')
        except:
            price_val = float('inf')

        # airline
        airline_codes = flight.get('validatingAirlineCodes', ['Unknown'])
        airline_code = airline_codes[0] if airline_codes else 'Unknown'

        return {
            'raw': flight,
            'departure_airport': dep_iata_code,
            'arrival_airport': arr_iata_code,
            'stops': stops,
            'is_direct': is_direct,
            'price_str': price_str,
            'price_val': price_val,
            'airline_code': airline_code,
            'itineraries': itineraries,
            'segments': segments
        }

    def format_flight_results(self, search_result):
        """
        تنسيق النتائج بطريقة Grouped-By-Destination (الخيار B).
        يستقبل ناتج search_flights_safe (قاموس) أو مصفوفة flights كما في السابق.
        النتيجة: {
            'success': True,
            'grouped_by_destination': {
                'DXB': { 'city_arabic': '...', 'city_english': '...', 'flights': [ ... ] },
                'DWC': { ... }
            },
            'count': total_count
        }
        """
        # التوافق مع الشكل القديم حيث يُمرر له قائمة مباشرة
        if isinstance(search_result, dict):
            flights_data = search_result.get('flights_data', [])
            destination_airports = search_result.get('destination_airports', [])
        else:
            flights_data = search_result or []
            destination_airports = []

        if not flights_data:
            return {
                'success': False,
                'message': '❌ لا توجد رحلات متاحة لهذا المسار والتاريخ.',
                'grouped_by_destination': {},
                'count': 0
            }

        # تجهيز الحقول
        grouped = {}
        total_count = 0

        # نجهز معلومات المدن لكل iata مقصد إن أمكن
        dest_info_cache = {}
        for dest in destination_airports:
            try:
                ci = self.get_city_info(dest)
                dest_info_cache[dest] = {
                    'city_arabic': ci.get('arabic_name'),
                    'city_english': ci.get('english_name')
                }
            except:
                dest_info_cache[dest] = {
                    'city_arabic': dest,
                    'city_english': dest
                }

        # ببساطة: لكل محاولة بحث، سنستخلص الرحلات المرتبطة بكل iata مقصد في destination_airports
        basic_infos = []
        for f in flights_data:
            info = self._extract_basic_flight_info(f)
            if info:
                basic_infos.append(info)

        # الآن قم بتعيين كل رحلة إلى قائمة المطار الوجهة الخاص بها
        for dest in destination_airports:
            # اختر الرحلات التي يصل آخر مقطع لها إلى هذا المطار
            related = [bi for bi in basic_infos if bi['arrival_airport'] == dest]
            formatted_list = []

            # نحول كل عنصر إلى شكل مبسط مستخدماً وظائف موجودة مسبقاً
            for bi in related:
                raw = bi['raw']
                try:
                    airline_info = self.get_airline_info(bi['airline_code'])
                except:
                    airline_info = {'arabic_name': bi['airline_code'], 'english_name': bi['airline_code']}
                # استخلاص المسار التفصيلي لكل مقطع
                route_segments = []
                for seg in bi['segments']:
                    dep = seg.get('departure', {})
                    arr = seg.get('arrival', {})
                    route_segments.append({
                        'segment_id': seg.get('id'),
                        'flight_number': f"{seg.get('carrierCode','')}{seg.get('number','')}",
                        'aircraft': seg.get('aircraft', {}).get('code', 'غير معروف'),
                        'departure_airport': dep.get('iataCode', ''),
                        'arrival_airport': arr.get('iataCode', ''),
                        'departure_time': dep.get('at', ''),
                        'arrival_time': arr.get('at', ''),
                        'duration': seg.get('duration', 'PT0H0M').replace('PT', '').replace('H', 'س ').replace('M', 'د')
                    })
                # نقاط التوقف
                layovers = []
                if len(bi['segments']) > 1:
                    for idx in range(len(bi['segments']) - 1):
                        cur = bi['segments'][idx]
                        nxt = bi['segments'][idx + 1]
                        lay_air = cur.get('arrival', {}).get('iataCode', '')
                        arr_time = cur.get('arrival', {}).get('at')
                        dep_time = nxt.get('departure', {}).get('at')
                        lay_dur = None
                        if arr_time and dep_time:
                            try:
                                t1 = datetime.strptime(arr_time, "%Y-%m-%dT%H:%M:%S")
                                t2 = datetime.strptime(dep_time, "%Y-%m-%dT%H:%M:%S")
                                diff = t2 - t1
                                hours, remainder = divmod(diff.seconds, 3600)
                                minutes = remainder // 60
                                lay_dur = f"{hours}س {minutes}د"
                            except:
                                lay_dur = None
                        try:
                            lay_city = self.get_city_info(lay_air).get('arabic_name')
                        except:
                            lay_city = lay_air
                        layovers.append({
                            'airport': lay_air,
                            'city': lay_city,
                            'duration': lay_dur
                        })

                # الحصول على أسماء المدن للـ departure & arrival
                try:
                    dep_city = self.get_city_info(bi['departure_airport']).get('arabic_name')
                except:
                    dep_city = bi['departure_airport']
                try:
                    arr_city = self.get_city_info(bi['arrival_airport']).get('arabic_name')
                except:
                    arr_city = bi['arrival_airport']

                formatted = {
                    'airline_code': bi['airline_code'],
                    'airline_arabic': airline_info.get('arabic_name'),
                    'airline_english': airline_info.get('english_name'),
                    'departure_airport': bi['departure_airport'],
                    'departure_city_arabic': dep_city,
                    'arrival_airport': bi['arrival_airport'],
                    'arrival_city_arabic': arr_city,
                    'stops': bi['stops'],
                    'is_direct': bi['is_direct'],
                    'price_str': bi['price_str'],
                    'price_val': bi['price_val'],
                    'route_segments': route_segments,
                    'layovers': layovers,
                    'flight_class': self.get_flight_class(bi['raw']),
                    'raw_flight_data': bi['raw']  # إضافة البيانات الخام للرحلة
                }
                formatted_list.append(formatted)

            # ترتيب: أولاً الرحلات المباشرة مرتبة حسب السعر ثم الباقي حسب السعر
            direct = [f for f in formatted_list if f['is_direct']]
            indirect = [f for f in formatted_list if not f['is_direct']]

            direct_sorted = sorted(direct, key=lambda x: x['price_val'])
            indirect_sorted = sorted(indirect, key=lambda x: x['price_val'])

            ordered = direct_sorted + indirect_sorted

            grouped[dest] = {
                'city_arabic': dest_info_cache.get(dest, {}).get('city_arabic', dest),
                'city_english': dest_info_cache.get(dest, {}).get('city_english', dest),
                'flights': ordered,
                'count': len(ordered)
            }
            total_count += len(ordered)

        return {
            'success': True,
            'grouped_by_destination': grouped,
            'origin_airports': destination_airports,  # note: original origin list kept in search_result if needed
            'destination_airports': destination_airports,
            'count': total_count
        }


    def debug_city_data(self):
        """فحص بيانات المدن في قاعدة البيانات للتأكد"""
        try:
            from models import City
            cities = self.db_session.query(City).filter_by(is_active=True).all()
            
            print("🔍 فحص بيانات المدن في قاعدة البيانات:")
            for city in cities:
                print(f"   {city.arabic_name} -> {city.iata_code}")
            
            # فحص مدن دبي تحديداً
            dubai_cities = self.db_session.query(City).filter(
                (City.arabic_name.ilike("%دبي%")) |
                (City.english_name.ilike("%dubai%"))
            ).filter_by(is_active=True).all()
            
            print("🔍 مدن دبي في قاعدة البيانات:")
            for city in dubai_cities:
                print(f"   {city.arabic_name} -> {city.iata_code}")
                
        except Exception as e:
            print(f"❌ خطأ في فحص البيانات: {e}")
            
    def get_flight_class(self, flight):
        """الحصول على فئة الرحلة"""
        try:
            traveler_pricings = flight.get('travelerPricings', [{}])[0]
            fare_details = traveler_pricings.get('fareDetailsBySegment', [{}])[0]
            cabin = fare_details.get('cabin', 'ECONOMY')
            
            cabin_names = {
                'ECONOMY': 'السياحية',
                'PREMIUM_ECONOMY': 'السياحية المميزة',
                'BUSINESS': 'رجال الأعمال',
                'FIRST': 'الأولى'
            }
            
            return cabin_names.get(cabin, 'السياحية')
        except:
            return 'السياحية'
            
            return response

    def get_flight_response_messages(self, query, formatted_results):
        """
        إرجاع قائمة من الرسائل:
        1. رسالة ملخص (المسار والتاريخ)
        2. رسائل الرحلات المباشرة (كل رحلة في رسالة)
        3. رسائل أرخص الرحلات (كل رحلة في رسالة)
        """
        messages = []
        
        if not formatted_results or not formatted_results.get('grouped_by_destination'):
            response = f"❌ **لم أجد رحلات متاحة**\n\n"
            response += f"📍 المسار: {query.get('origin')} → {query.get('destination')}\n"
            response += f"📅 التاريخ: {query.get('date')}\n"
            response += "💡 جرب تاريخاً مختلفاً أو وجهة أخرى"
            messages.append(response)
            return messages

        # Header Message
        formatted_date = self.format_date_arabic(query['date'])
        header = f"🔎 **نتائج البحث**\n"
        header += f"📅 **التاريخ:** {formatted_date}\n"
        header += f"📍 **المسار:** {query.get('origin')} → {query.get('destination')}\n"
        messages.append(header)

        # Flatten all flights from all destinations
        all_flights = []
        grouped = formatted_results['grouped_by_destination']
        for dest_iata, info in grouped.items():
            all_flights.extend(info['flights'])

        if not all_flights:
             messages.append("❌ لا توجد رحلات متاحة.")
             return messages

        # 1. Direct Flights
        direct_flights = [f for f in all_flights if f['is_direct']]
        direct_flights.sort(key=lambda x: x['price_val'])
        
        # Limit to top 5 direct flights
        top_direct = direct_flights[:5]
        
        if top_direct:
            messages.append("🛫 **الرحلات المباشرة:**")
            for f in top_direct:
                msg = self._format_single_flight_message(f)
                messages.append(msg)
        else:
            messages.append("ℹ️ لا توجد رحلات مباشرة.")

        # 2. Cheapest Flights (Top 5 overall)
        cheapest_flights = sorted(all_flights, key=lambda x: x['price_val'])[:5]
        
        if cheapest_flights:
            messages.append("💰 **أرخص الرحلات:**")
            for f in cheapest_flights:
                # Check if we already showed this flight in direct section to avoid exact duplicates
                # We can check by some unique ID or just object identity if it's the same list objects
                if f in top_direct:
                    continue
                    
                msg = self._format_single_flight_message(f)
                messages.append(msg)

        messages.append("⚠️ **الأسعار عرضة للتغيير بحسب التوافر.**")
        return messages

    def _format_single_flight_message(self, flight):
        """تنسيق رسالة لرحلة واحدة"""
        airline_name = flight['airline_arabic']
        price = flight['price_str']
        
        # معلومات الوقت والتاريخ
        dep_time = ""
        arr_time = ""
        dep_date = ""
        arr_date = ""
        
        if flight.get('route_segments'):
            first_seg = flight['route_segments'][0]
            last_seg = flight['route_segments'][-1]
            
            # استخراج التاريخ والوقت للمغادرة
            dep_datetime = first_seg.get('departure_time', '')
            if dep_datetime:
                try:
                    dt = datetime.strptime(dep_datetime[:19], '%Y-%m-%dT%H:%M:%S')
                    dep_date = dt.strftime('%Y-%m-%d')
                    dep_time = dt.strftime('%H:%M')
                except:
                    dep_time = dep_datetime[:16].replace('T', ' ')
            
            # استخراج التاريخ والوقت للوصول
            arr_datetime = last_seg.get('arrival_time', '')
            if arr_datetime:
                try:
                    dt = datetime.strptime(arr_datetime[:19], '%Y-%m-%dT%H:%M:%S')
                    arr_date = dt.strftime('%Y-%m-%d')
                    arr_time = dt.strftime('%H:%M')
                except:
                    arr_time = arr_datetime[:16].replace('T', ' ')
        
        msg = f"✈️ **{airline_name}**\n"
        msg += f"💰 **السعر:** {price} USD\n"
        
        # عرض التاريخ والوقت
        if dep_date and dep_time:
            msg += f"📅 **تاريخ المغادرة:** {dep_date}\n"
            msg += f"🕐 **وقت المغادرة:** {dep_time}\n"
        
        if arr_date and arr_time:
            msg += f"📅 **تاريخ الوصول:** {arr_date}\n"
            msg += f"🕐 **وقت الوصول:** {arr_time}\n"
        
        # معلومات التوقفات
        if not flight['is_direct']:
            stops = flight['stops']
            msg += f"🛑 **التوقفات:** {stops} (غير مباشرة)\n"
            # Add layover info if available
            if flight.get('layovers'):
                layover_txts = []
                for lay in flight['layovers']:
                    dur = lay.get('duration', '')
                    city = lay.get('city', lay.get('airport'))
                    layover_txts.append(f"{city} ({dur})")
                msg += f"   📍 {', '.join(layover_txts)}\n"
        else:
            msg += f"✨ **رحلة مباشرة**\n"
        
        # معلومات الفئة
        msg += f"🏷️ **الفئة:** {flight.get('flight_class', 'السياحية')}\n"
        
        # معلومات الوزن المسموح (Baggage)
        baggage_info = self._extract_baggage_info(flight)
        if baggage_info:
            msg += f"🧳 **الأمتعة:** {baggage_info}"
        
        return msg
    
    def _extract_baggage_info(self, flight):
        """استخراج معلومات الوزن المسموح من بيانات الرحلة"""
        try:
            raw_flight = flight.get('raw_flight_data')
            if not raw_flight:
                return None
            
            traveler_pricings = raw_flight.get('travelerPricings', [])
            if not traveler_pricings:
                return None
            
            # الحصول على معلومات الأمتعة من أول مسافر
            first_traveler = traveler_pricings[0]
            fare_details = first_traveler.get('fareDetailsBySegment', [])
            
            if not fare_details:
                return None
            
            # جمع معلومات الأمتعة
            baggage_parts = []
            
            # الأمتعة المسجلة (Checked Baggage)
            checked_bags = fare_details[0].get('includedCheckedBags', {})
            if checked_bags:
                quantity = checked_bags.get('quantity')
                weight = checked_bags.get('weight')
                weight_unit = checked_bags.get('weightUnit', 'KG')
                
                if quantity:
                    baggage_parts.append(f"{quantity} حقيبة")
                elif weight:
                    baggage_parts.append(f"{weight} {weight_unit}")
            
            # الأمتعة المحمولة (Cabin Baggage)
            cabin_bags = fare_details[0].get('includedCabinBags', {})
            if cabin_bags:
                quantity = cabin_bags.get('quantity')
                weight = cabin_bags.get('weight')
                weight_unit = cabin_bags.get('weightUnit', 'KG')
                
                if quantity:
                    baggage_parts.append(f"حقيبة يد: {quantity}")
                elif weight:
                    baggage_parts.append(f"حقيبة يد: {weight} {weight_unit}")
            
            if baggage_parts:
                return " | ".join(baggage_parts)
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في استخراج معلومات الأمتعة: {e}")
            return None

# إنشاء كائن عام للنظام
flight_system = FlightSystem()

# دوال مساعدة للاستخدام المباشر
def search_flights(origin, destination, date, adults=1, db_session=None):
    """دالة مساعدة للبحث عن الرحلات"""
    if db_session:
        flight_system.db_session = db_session
        flight_system.load_all_data_from_db()
    
    search_result = flight_system.search_flights_safe(origin, destination, date, adults)
    formatted = flight_system.format_flight_results(search_result)
    return formatted

def get_cheapest_flight(query, formatted_results, db_session=None):
    """دالة مساعدة للحصول على أرخص رحلة (تُستخدم لعرض النتيجة بصيغة نصية)"""
    if db_session:
        flight_system.db_session = db_session
        flight_system.load_all_data_from_db()
    
    return flight_system.get_flight_response_messages(query, formatted_results)
