from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
import requests
import random
import re
import json
import os
from datetime import datetime
from utils import (
    API_KEY, BASE_URL, GENRE_KEYWORDS, NUMBER_MAPPING, 
    COUNTRY_MAPPING, PLATFORM_MAPPING, get_tmdb_movies, get_movies_by_semantic_similarity,
    get_movies_by_story_tmdb, get_empathetic_response, fetch_poster_from_tmdb
)
from models import db, Favorite, Watched, Watchlist

movie_bp = Blueprint('movie', __name__)

# Editörün seçimi için basit in-memory cache
EDITORS_CHOICE_CACHE = []
POPULAR_MOVIES_CACHE = []

IMG_BASE = "https://image.tmdb.org/t/p/w500"

def add_poster_url(movie):
    """Film objesine poster_url ekler, yoksa TMDB'den çeker."""
    if not movie.get("poster_path"):
        # Poster yoksa TMDB'den çekmeyi dene
        movie["poster_path"] = fetch_poster_from_tmdb(movie.get("id"))

    if movie.get("poster_path"):
        # Eğer tam URL değilse (http ile başlamıyorsa) base url ekle
        path = movie["poster_path"]
        movie["poster_url"] = path if path.startswith("http") else f"{IMG_BASE}{path}"
    else:
        movie["poster_url"] = "https://placehold.co/140x210?text=No+Image"
    return movie

def handle_list_action(model_class, success_msg, remove_msg):
    """Liste ekleme/çıkarma işlemleri için yardımcı fonksiyon."""
    data = request.json
    movie_id = data.get('movie_id')
    title = data.get('title')
    poster_path = data.get('poster_path')
    
    existing = model_class.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    
    if not existing:
        new_item = model_class(user_id=current_user.id, movie_id=movie_id, title=title, poster_path=poster_path)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': success_msg, 'action': 'added'})
    else:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': remove_msg, 'action': 'removed'})

# Mood'a göre hazır parametreler
MOOD_PARAMS = {
  "romantik": {
    "with_genres": "10749",
    "without_genres": "28,12,27,53,80,878"
  },
  "heyecan": {
    "with_genres": "28|12|53|878",
    "without_genres": "18,10751,10402"
  },
  "gurur": {
    "with_genres": "36|10752",
    "without_genres": "10749,35,16,27,53"
  },
  "uzgun": {
    "with_genres": "18",
    "without_genres": "28,12,35,16,10751,14,878"
  },
  "mutlu": {
  "with_genres": "35",
  "without_genres": "27,53,80"
},
  "ofkeli": {
    "with_genres": "28",
    "without_genres": "10751,16,10402,35"
  },
  "sikilmis": {
    "with_genres": "12|35|878|28",
    "without_genres": "18,99"
  },
  "yalnizlik": {
    "with_genres": "18",
    "without_genres": "10749,28,12,35,16,10751,53"
  },
  "hayalkirikligi": {
    "with_genres": "18",
    "without_genres": "10749,35,16,28,12,878"
  },
  "stresli": {
    "with_genres": "35|10751|16",
    "without_genres": "27,53,80,28,9648,18"
}
}

@movie_bp.route('/api/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    return handle_list_action(Favorite, "Film favorilere eklendi! ❤️", "Film favorilerden çıkarıldı.")

@movie_bp.route('/api/add_watched', methods=['POST'])
@login_required
def add_watched():
    return handle_list_action(Watched, "Film izlediklerim listesine eklendi! ✅", "Film izlediklerimden çıkarıldı.")

@movie_bp.route('/api/add_watchlist', methods=['POST'])
@login_required
def add_watchlist():
    return handle_list_action(Watchlist, "Film izleme listesine eklendi! 📅", "Film izleme listesinden çıkarıldı.")

@movie_bp.route('/favorites')
@login_required
def favorites_page():
    user_favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=user_favorites)

@movie_bp.route('/watched')
@login_required
def watched_page():
    # İzlenen filmleri tarihe göre (en yeni en üstte) getir
    watched_movies = Watched.query.filter_by(user_id=current_user.id).order_by(Watched.watched_at.desc()).all()
    return render_template('watched.html', watched_movies=watched_movies)

@movie_bp.route('/watchlist')
@login_required
def watchlist_page():
    watchlist_movies = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.added_at.desc()).all()
    return render_template('watchlist.html', watchlist_movies=watchlist_movies)

@movie_bp.route('/api/popular')
def popular():
    """En çok izlenen (Hasılat Rekortmeni) 40 filmi getirir."""
    global POPULAR_MOVIES_CACHE
    if POPULAR_MOVIES_CACHE:
        return jsonify(POPULAR_MOVIES_CACHE)

    # Kullanıcının istediği özel liste (Türkiye'de en çok izlenenler)
    items = [
        {"title": "Titanic", "year": 1997},
        {"title": "Hızlı ve Öfkeli 7", "year": 2015},
        {"title": "Örümcek-Adam: Eve Dönüş Yok", "year": 2021},
        {"title": "Avatar: Suyun Yolu", "year": 2022},
        {"title": "Hızlı ve Öfkeli 8", "year": 2017},
        {"title": "Avatar", "year": 2009},
        {"title": "Avengers: Endgame", "year": 2019},
        {"title": "Ters Yüz 2", "year": 2024},
        {"title": "Avengers: Sonsuzluk Savaşı", "year": 2018},
        {"title": "Joker", "year": 2019},
        {"title": "Buz Devri 4: Kıtalar Ayrılıyor", "year": 2012},
        {"title": "Yüzüklerin Efendisi: Yüzük Kardeşliği", "year": 2001},
        {"title": "Oppenheimer", "year": 2023},
        {"title": "Truva", "year": 2004},
        {"title": "Hobbit: Beş Ordunun Savaşı", "year": 2014},
        {"title": "Zootropolis 2", "year": 2025},
        {"title": "Hızlı ve Öfkeli 10", "year": 2023},
        {"title": "Doktor Strange Çoklu Evren Çılgınlığında", "year": 2022},
        {"title": "Karayip Korsanları: Salazar'ın İntikamı", "year": 2017},
        {"title": "Yüzüklerin Efendisi: İki Kule", "year": 2002},
        {"title": "2012", "year": 2009},
        {"title": "Matrix Reloaded", "year": 2003},
        {"title": "Batman v Superman: Adaletin Şafağı", "year": 2016},
        {"title": "Deadpool & Wolverine", "year": 2024},
        {"title": "Hızlı ve Öfkeli: Hobbs ve Shaw", "year": 2019},
        {"title": "Buz Devri 3: Dinozorların Şafağı", "year": 2009},
        {"title": "Alacakaranlık Efsanesi: Şafak Vakti Bölüm 2", "year": 2012},
        {"title": "Altıncı His", "year": 2000},
        {"title": "Barbie", "year": 2023},
        {"title": "Alacakaranlık Efsanesi: Şafak Vakti Bölüm 1", "year": 2011},
        {"title": "Avatar: Ateş ve Kül", "year": 2025},
        {"title": "Deadpool 2", "year": 2018},
        {"title": "Matrix", "year": 1999},
        {"title": "Moana", "year": 2017},
        {"title": "Buz Devri 5: Büyük Çarpışma", "year": 2016},
        {"title": "Yüzüklerin Efendisi: Kral'ın Dönüşü", "year": 2003},
        {"title": "Yenilmezler: Ultron Çağı", "year": 2015},
        {"title": "Karlar Ülkesi II", "year": 2019},
        {"title": "Son Umut", "year": 2014},
        {"title": "İnanılmaz Aile 2", "year": 2018}
    ]

    selected_movies = []
    for item in items:
        # Özel karakter düzeltmesi ve arama
        query_title = item['title'].replace('–', '-')
        params = {'api_key': API_KEY, 'language': 'tr-TR',
                  'query': query_title, 'year': item['year']}
        try:
            response = requests.get(f"{BASE_URL}/search/movie", params=params, timeout=3)
            results = response.json().get('results', [])
            if results:
                selected_movies.append(results[0])
        except:
             continue

    POPULAR_MOVIES_CACHE = selected_movies
    return jsonify(selected_movies)

@movie_bp.route('/api/editors_choice')
def editors_choice():
    """Editörün seçimi olan özel film listesini döndürür."""
    global EDITORS_CHOICE_CACHE
    if EDITORS_CHOICE_CACHE:
        return jsonify(EDITORS_CHOICE_CACHE)

    # İstenen özel film listesi (String veya Dict olabilir)
    items = [
        "No Time to Die",
        "Shoplifters",
        "Manchester by the Sea", 
        {"title": "Extraction", "year": 2020},
        "Train to Busan",
        "Kabin Bagajı",
        "Red Notice",
        "Sihirbazlar Çetesi",
        "Knives Out",
        "Run All Night",
        "Kader Ajanları"
        "Taken",
        "Jack Reacher",
        "The Avengers",
        "I Believe in Santa",
        "B&B Merry",
        "The Amateur",
        "Top Gun: Maverick",
        "Elysium",
        
    ]
    
    selected_movies = []
    
    for item in items:
        if isinstance(item, dict):
            params = {'api_key': API_KEY, 'language': 'tr-TR', 'query': item['title']}
            if 'year' in item:
                params['year'] = item['year']
        else:
            params = {'api_key': API_KEY, 'language': 'tr-TR', 'query': item}
            
        try:
            response = requests.get(f"{BASE_URL}/search/movie", params=params)
            results = response.json().get('results', [])
            if results:
                selected_movies.append(results[0]) # İlk sonucu ekle
        except:
            continue
            
    EDITORS_CHOICE_CACHE = selected_movies
    return jsonify(selected_movies)

@movie_bp.route('/api/top_rated')
def top_rated():
    """En çok beğenilen filmleri getirir (40 adet)."""
    movies = []
    try:
        # İlk 2 sayfayı (40 film) döngü ile çek
        for page in range(1, 3):
            params = {'api_key': API_KEY, 'language': 'tr-TR', 'page': page}
            response = requests.get(f"{BASE_URL}/movie/top_rated", params=params, timeout=5)
            if response.status_code == 200:
                movies.extend(response.json().get('results', []))
    except Exception as e:
        print(f"Top rated API error: {e}")
        # Fallback: API hatası durumunda films.json'dan en yüksek puanlıları çek
        try:
            if os.path.exists("films.json"):
                with open("films.json", "r", encoding="utf-8") as f:
                    local_films = json.load(f)
                    local_films.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                    return jsonify(local_films[:40])
        except:
            pass
        return jsonify([])
    
    return jsonify(movies[:40])

@movie_bp.route('/api/story-recommendations', methods=['POST'])
@login_required
def story_recommendations():
    """Hikaye modunda (Story API) film önerisi döndürür."""
    data = request.json
    user_text = data.get('text', '')
    movies = get_movies_by_story_tmdb(user_text)
    
    # Poster URL'lerini ekle
    for movie in movies:
        add_poster_url(movie)
        
    return jsonify({'results': movies})

@movie_bp.route('/api/recommend', methods=['POST'])
def recommend():
    """Duygu durumuna göre film önerir."""
    data = request.json
    mood = data.get('mood')
    
    m = MOOD_PARAMS.get(mood, {})
    
    current_year = datetime.now().year
    
    params = {
        "sort_by": "popularity.desc",
        "vote_count.gte": 1000,
        "vote_average.gte": 6.5,
        "primary_release_date.gte": f"{current_year - 10}-01-01",
        "page": random.randint(1, 10)
    }
    params.update({k:v for k,v in m.items() if v})
    
    movies = get_tmdb_movies(params)
    return jsonify(movies)

@movie_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Kullanıcı mesajını analiz eder ve film önerir."""
    data = request.json
    user_text = data.get('message', '').lower()
    exclude_ids = data.get('exclude', []) # Frontend'den gelen hariç tutulacaklar
    
    # Teşekkür/Kapanış Kontrolü
    if any(word in user_text for word in ['teşekkür', 'tesekkur', 'sağ ol', 'sag ol', 'sağol', 'sagol']):
        return jsonify({
            'movies': [],
            'response_message': "Rica ederim, iyi seyirler! 🍿"
        })

    mood = data.get('mood')
    if mood: mood = mood.lower()
    
    # Hikaye modu kontrolü: mood yoksa story-based önerileri kullan
    if not mood:
        try:
            movies = get_movies_by_story_tmdb(user_text, exclude_ids=exclude_ids)
            response_msg = get_empathetic_response(user_text)
            return jsonify({
                'movies': movies,
                'response_message': response_msg
            })
        except Exception as e:
            print(f"Story mode error: {e}") # Daha fazla loglama
            # Fallback to text similarity
            pass
    
    # Kelime bazlı sayıları rakama çevir
    for word, digit in NUMBER_MAPPING.items():
        user_text = re.sub(r'\b' + word + r'\b', digit, user_text)
    
    user_text = re.sub(r'(\d+)\s*(?:buçuk|bucuk)', r'\1.5', user_text)
    user_text = re.sub(r'\b(?:yarım|yarim)\b', '0.5', user_text)

    params = {'page': 1}
    filters_found = False
    
    # 1. Tür Analizi
    selected_genres = []
    for key, value in GENRE_KEYWORDS.items():
        if key in user_text:
            selected_genres.append(str(value))
            
    if selected_genres:
        params['with_genres'] = ",".join(selected_genres)
        filters_found = True
        
    # 2. Puan Analizi
    # Puan regex'i birleştirildi ve düzeltildi
    rating_pattern = r"(?:en az|minimum)?\s*(\d+(?:[.,]\d+)?)\s*(?:puan|imdb)?\s*(?:ve)?\s*(?:üzeri|uzeri|üstü|ustu|yukarı|yukari|fazla|den yüksek)"
    rating_match = re.search(rating_pattern, user_text)
    
    if not rating_match:
        # "7 puan" gibi basit ifadeler için yedek kontrol
        rating_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:puan|imdb)", user_text)

    if rating_match:
        try:
            rating = float(rating_match.group(1).replace(',', '.'))
            if 0 <= rating <= 10:
                params['vote_average.gte'] = rating
                filters_found = True
        except ValueError:
            pass
        
    # 3. Sıralama Analizi
    if "en çok izlenen" in user_text or "popüler" in user_text:
        params['sort_by'] = 'popularity.desc'
        filters_found = True
    elif "yüksek puanlı" in user_text or "en iyi" in user_text or "çok beğenilen" in user_text:
        params['sort_by'] = 'vote_average.desc'
        params['vote_count.gte'] = 1000
        filters_found = True
        
    # 4. Tarih Analizi
    if "son yıllar" in user_text:
        params['primary_release_date.gte'] = '2020-01-01'
        filters_found = True
    elif "eski filmler" in user_text:
        params['primary_release_date.lte'] = '2000-01-01'
        filters_found = True
    elif "en yeni" in user_text or "vizyon" in user_text:
        params['sort_by'] = 'primary_release_date.desc'
        params['primary_release_date.lte'] = datetime.now().strftime('%Y-%m-%d')
        filters_found = True

    # 2021 sonrası
    after_match = re.search(r"\b(19\d{2}|20\d{2})\s*sonrası\b", user_text)
    if after_match:
        y = int(after_match.group(1))
        params["primary_release_date.gte"] = f"{y}-01-01"
        filters_found = True

    # 2010 öncesi
    before_match = re.search(r"\b(19\d{2}|20\d{2})\s*öncesi\b", user_text)
    if before_match:
        y = int(before_match.group(1))
        params["primary_release_date.lte"] = f"{y}-12-31"
        filters_found = True

    # 2020'ler, 90'lar vb. (Decades)
    decade_match = re.search(r"\b(19\d0|20\d0)['’]?l[ae]r\b", user_text)
    if decade_match:
        y = int(decade_match.group(1))
        params["primary_release_date.gte"] = f"{y}-01-01"
        params["primary_release_date.lte"] = f"{y+9}-12-31"
        filters_found = True

    # tek yıl (2023 gibi) — bunu en sona koy ki "sonrası/öncesi" varken ezmesin
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", user_text)
    if year_match and "sonrası" not in user_text and "öncesi" not in user_text and not decade_match:
        y = int(year_match.group(1))
        params["primary_release_date.gte"] = f"{y}-01-01"
        params["primary_release_date.lte"] = f"{y}-12-31"
        filters_found = True

    # 5. Oy Sayısı
    if "çok oy alan" in user_text:
        params['vote_count.gte'] = 1000
        filters_found = True

    # 6. Ülke Analizi
    found_countries = []
    for country, code in COUNTRY_MAPPING.items():
        if country in user_text:
            found_countries.append(code)
    
    if found_countries:
        params['with_origin_country'] = "|".join(list(set(found_countries))) # OR mantığı
        filters_found = True
            
    # 8. Platform Analizi (Genişletilmiş)
    found_platforms = []
    for platform, pid in PLATFORM_MAPPING.items():
        if platform in user_text:
            found_platforms.append(str(pid))
            
    if found_platforms:
        params['with_watch_providers'] = "|".join(list(set(found_platforms))) # OR mantığı
        params['watch_region'] = "TR" # Türkiye bölgesi için
        filters_found = True

    # 9. Süre Analizi
    # "90 dakikadan kısa", "100 dakika altı"
    duration_lte = re.search(r"(\d+)\s*dakika(?:dan)?\s*(?:kısa|az|altı|altında)", user_text)
    if duration_lte:
        params['with_runtime.lte'] = int(duration_lte.group(1))
        filters_found = True
        
    # "90 dakikadan uzun", "120 dakika üzeri"
    duration_gte = re.search(r"(\d+)\s*dakika(?:dan)?\s*(?:uzun|fazla|üzeri|uzeri|üstü|ustu)", user_text)
    if duration_gte:
        params['with_runtime.gte'] = int(duration_gte.group(1))
        filters_found = True
        
    if mood and not selected_genres:
        if filters_found or "başka" in user_text or "beğenmedim" in user_text:
             mood_config = MOOD_PARAMS.get(mood)
             if mood_config:
                 if 'with_genres' in mood_config:
                     params['with_genres'] = mood_config['with_genres']
                 if 'without_genres' in mood_config:
                     params['without_genres'] = mood_config['without_genres']

    # --- ANA MANTIK: Filtre yoksa ve 'baska' denmediyse Basit Arama Yap ---
    if not filters_found and "başka" not in user_text and "beğenmedim" not in user_text:
        movies = get_movies_by_semantic_similarity(user_text, exclude_ids=exclude_ids, top_k=8)

        # hiç film gelmezse fallback
        if not movies:
            fallback_params = {
                "sort_by": "popularity.desc",
                "page": random.randint(1, 5)
            }
            movies = get_tmdb_movies(fallback_params)[:8]
        
        # Filmleri puana göre sırala (Yüksekten düşüğe)
        movies.sort(key=lambda x: x.get('vote_average', 0), reverse=True)

        return jsonify({
            'movies': movies,
            'response_message': "Söylediklerine dayanarak senin için bu filmleri seçtim:"
        })

        
    # Eğer özel bir sıralama belirtilmediyse, puana göre sırala
    if 'sort_by' not in params:
        params['sort_by'] = 'vote_average.desc'
        params['vote_count.gte'] = 300

    movies = get_tmdb_movies(params)[:8]
    
    response_msg = "Harika, işte senin için seçtiğim filmler:"
    if filters_found:
        response_msg = "İstediğin kriterlere göre bu filmleri buldum:"

    # Hem mesajı hem filmleri döndür
    return jsonify({
        'movies': movies,
        'response_message': response_msg
    })

@movie_bp.route('/api/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Film detaylarını getirir."""
    try:
        params = {
            'api_key': API_KEY,
            'language': 'tr-TR',
            'append_to_response': 'credits'
        }
        response = requests.get(f"{BASE_URL}/movie/{movie_id}", params=params, timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        print(f"Movie detail API error: {e}")

    # Fallback: films.json
    try:
        if os.path.exists("films.json"):
            with open("films.json", "r", encoding="utf-8") as f:
                local_films = json.load(f)
                for film in local_films:
                    if film.get('id') == movie_id:
                        # Frontend credits bekliyor olabilir, boş ekleyelim
                        if 'credits' not in film:
                            film['credits'] = {'cast': [], 'crew': []}
                        return jsonify(film)
    except Exception as e:
        print(f"Local fallback error: {e}")

    return jsonify({"error": "Film bulunamadı"}), 404