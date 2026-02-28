import requests
import os
import json
import re
import random
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.themoviedb.org/3'

# GENRE HARİTALARI
GENRE_KEYWORDS = {
    "aksiyon": 28, "komedi": 35, "romantik": 10749, "drama": 18, "dram": 18,
    "korku": 27, "bilim kurgu": 878, "macera": 12, "animasyon": 16,
    "aile": 10751, "gerilim": 53, "belgesel": 99, "suç": 80,
    "tarih": 36, "müzik": 10402, "gizem": 9648, "savaş": 10752,
    "fantastik": 14
}

NUMBER_MAPPING = {
    'bir': '1', 'iki': '2', 'üç': '3', 'dört': '4', 'beş': '5',
    'altı': '6', 'yedi': '7', 'sekiz': '8', 'dokuz': '9', 'on': '10'
}

COUNTRY_MAPPING = {
    'türkiye': 'TR', 'yerli': 'TR', 'türk': 'TR',
    'abd': 'US', 'amerika': 'US', 'hollywood': 'US',
    'ingiltere': 'GB', 'fransa': 'FR', 'almanya': 'DE',
    'kore': 'KR', 'güney kore': 'KR', 'japonya': 'JP',
    'hindistan': 'IN', 'hint': 'IN'
}

PLATFORM_MAPPING = {
    'netflix': 8,
    'disney': 337, 'disney+': 337,
    'amazon': 119, 'prime': 119, 'amazon prime': 119,
    'apple': 350, 'apple tv': 350,
    'mubi': 11,
    'blutv': 329,
    'exxen': 597,
    'tod': 1923 
}

# YARDIMCI FONKSİYONLAR
def get_tmdb_movies(params):
    """TMDB API'sine istek atar ve film listesi döndürür."""
    final_params = params.copy()
    final_params['api_key'] = API_KEY
    final_params.setdefault('language', 'tr-TR')
    
    url = f"{BASE_URL}/discover/movie"
    if 'query' in final_params:
        url = f"{BASE_URL}/search/movie"
        
    try:
        response = requests.get(url, params=final_params)
        results = response.json().get('results', []) if response.status_code == 200 else []
        # Posteri olmayanları filtrele
        return [m for m in results if m.get('poster_path')]
    except:
        return []

def fetch_poster_from_tmdb(movie_id):
    """Film ID'sine göre TMDB'den poster yolunu çeker."""
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        return data.get("poster_path")
    except:
        return None

# GERİYE DÖNÜK UYUMLULUK (WRAPPER)
def get_movies_by_story_tmdb(user_text, exclude_ids=None, last_n_years=None):
    """Artık doğrudan semantik arama (embedding) kullanıyor."""
    return get_movies_by_semantic_similarity(user_text, top_k=5, exclude_ids=exclude_ids, exclude_animation=True)

def get_empathetic_response(user_text):
    """Kullanıcı metnindeki anahtar kelimelere göre empatik bir cevap döndürür."""
    text = user_text.lower()
    
    # Öncelik sırasına göre anahtar kelime - mesaj eşleşmeleri
    responses = {
        "deprem": "Çok geçmiş olsun, umarım güvendesindir. Yaşadığın bu zorlu süreci anlamlandırmana yardımcı olabilecek, dayanışma ve umut dolu filmler seçtim:",
        "gelecek kaygısı": "Geleceğin belirsizliği bazen ağır gelebilir. İşte bu kaygılarla yüzleşen ve kendi yolunu çizen karakterlerin hikayeleri:",
        "varoluş": "Hayatın anlamını ve kendi yerimizi sorguladığımız o derin anlar... İşte varoluşsal sancılara ayna tutan filmler:",
        "boşluk": "İçindeki boşluğu anlamlandırmaya çalışan karakterlerin yolculukları sana iyi gelebilir. İşte o filmler:",
        "anlamsız": "Bazen her şey anlamsız gelebilir. Bu duyguyu ve yeniden anlam bulma çabasını işleyen filmler:",
        "afet": "Çok geçmiş olsun. Bazen felaket filmleri izlemek, insanın içindeki hayatta kalma gücünü hatırlatır. İşte senin için seçtiklerim:",
        "enkaz": "Çok geçmiş olsun. Umut her zaman vardır. İşte hayata tutunma hikayeleri:",
        "aldat": "Kalp kırıklığı zor bir süreç, biliyorum. Ama yalnız değilsin. İşte ihanet, yüzleşme ve yeniden ayağa kalkma üzerine filmler:",
        "ihanet": "Güvenin kırılması ağırdır. Bu duygularla başa çıkmana yardımcı olabilecek hikayeler:",
        "ayrıl": "Ayrılıklar yeni başlangıçların habercisidir. Kendini bulma yolculuğunda sana eşlik edecek filmler:",
        "terk": "Bazen gitmek gerekir, bazen de kalan olmak zordur. İşte bu duyguları işleyen filmler:",
        "boşan": "Hayat bazen planladığımız gibi gitmeyebilir. Bu süreçte sana güç verecek ve yalnız olmadığını hissettirecek hikayeler:",
        "kovul": "Kariyer yolculuğunda bazen duraklamalar olur. Bu durumu bir fırsata çeviren karakterlerin hikayeleri sana ilham verebilir:",
        "işsiz": "Her son yeni bir başlangıçtır. Umudunu kaybetme, işte mücadele ruhunu tazeleyecek filmler:",
        "istifa": "Cesur bir karar almışsın! Yeni bir yola çıkarken motivasyonunu artıracak filmler burada:",
        "yalnız": "Yalnızlık bazen en iyi öğretmendir. Kendi kendine yetebilmenin ve içsel yolculuğun güzelliğini anlatan filmler:",
        "mutsuz": "Bazen sadece durup hissetmek gerekir. Ruhuna dokunacak ve belki de sana umut olacak filmler:",
        "kork": "Korkularının üzerine gitmek cesaret ister. İşte gerilimi yüksek ama sonunda rahatlayacağın filmler:",
        "sınav": "Sınav stresi geçicidir, ama kazandığın tecrübeler kalıcı. Biraz mola verip kafanı dağıtman için seçtiklerim:",
        "aşk": "Aşkın her hali güzeldir. Kalbini ısıtacak romantik hikayeler senin için:",
        "sevgi": "Sevgi dünyayı kurtarır derler. İşte içini ısıtacak sevgi dolu filmler:",
        "aile": "Aile bağları karmaşıktır ama köklerimizdir. Aile ilişkilerine dair derinlikli filmler:",
        "yeni bir şehre": "Taşınmak büyük bir cesaret ister! Yeni sokaklar, yeni yüzler... Bu adaptasyon sürecinde sana iyi gelecek, yalnız olmadığını hissettirecek filmler seçtim:",
        "taşın": "Yeni bir yer, yeni bir hayat... Bu değişim sürecinde sana ilham verecek yolculuk hikayeleri:",
        "yeni şehir": "Şehirler değişir, hikayeler başlar. Adaptasyon sürecini anlatan filmler:",
        "motivasyon": "Bazen ihtiyacımız olan tek şey küçük bir kıvılcımdır. İçindeki ateşi yakacak filmler:",
        "başarı": "Zirveye giden yol dikenlidir ama manzarası güzeldir. İşte ilham veren başarı hikayeleri:",
        "yolculuk": "Yollar sadece mesafeleri değil, insanı kendine de götürür. İşte harika yol hikayeleri:",
        "dost": "Gerçek dostluklar hayatın en büyük hazinesidir. İşte sıkı dostlukları anlatan filmler:",
        "gizem": "Merak kediyi öldürür derler ama bu filmleri izlemeden duramayacaksın. İşte zihnini zorlayacak gizemler:",
    }
    
    for key, msg in responses.items():
        if key in text:
            return msg
            
    return "Anlattıklarına uygun bu harika filmleri buldum senin için:"

_EMB_MODEL = None
_FILMS = None
_FILM_EMBS = None

def _ensure_embeddings_loaded():
    """Embedding dosyası yoksa veya film sayısı değişmişse yeniden oluşturur."""
    global _FILM_EMBS
    
    embedding_file = "film_embeddings_v3.npy"
    
    # Dosya var mı ve güncel mi kontrol et
    needs_update = False
    if not os.path.exists(embedding_file):
        needs_update = True
    else:
        temp_embs = np.load(embedding_file)
        if len(temp_embs) != len(_FILMS):
            needs_update = True
        else:
            _FILM_EMBS = temp_embs

    if needs_update:
        print(f"Embeddingler oluşturuluyor ({len(_FILMS)} film)... Bu işlem biraz sürebilir.")
        
        # Başlık, özet ve anahtar kelimeleri birleştirerek daha zengin bir içerik oluştur
        texts = []
        for m in _FILMS:
            # Türleri dahil etmiyoruz. Sadece Başlık, Özet ve Keywords.
            # Model çok dilli (multilingual) olduğu için İngilizce keywordler Türkçe aramalarla eşleşebilir.
            content = f"{m.get('title', '')} {m.get('overview', '')} {' '.join(m.get('keywords', []))}"
            texts.append(content.strip())
            
        _FILM_EMBS = _EMB_MODEL.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        np.save(embedding_file, _FILM_EMBS)
        print(f"Embeddingler kaydedildi: {embedding_file}")

def _load_semantic_assets():
    global _EMB_MODEL, _FILMS
    if _EMB_MODEL is None:
        _EMB_MODEL = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Veri güncelliği için her seferinde dosyadan oku
    with open("films.json", "r", encoding="utf-8") as f:
        _FILMS = json.load(f)
    
    # Embeddingleri kontrol et: Yüklü değilse veya sayı uyuşmuyorsa yenile
    if _FILM_EMBS is None or len(_FILM_EMBS) != len(_FILMS):
        _ensure_embeddings_loaded()

def get_movies_by_semantic_similarity(user_text: str, top_k=5, exclude_ids=None, exclude_animation=False):
    _load_semantic_assets()
    q = (user_text or "").strip()
    if len(q) < 3:
        return []

    # Kullanıcı metnini vektöre çevir
    q_emb = _EMB_MODEL.encode([q], convert_to_numpy=True, normalize_embeddings=True)[0]

    # Cosine similarity: normalize olduğu için dot product = cosine
    sims = _FILM_EMBS @ q_emb

    # Daha fazla aday al (filtre sonrası top_k kalması için)
    candidate_idx = sims.argsort()[-50:][::-1]

    exclude_set = set()
    if exclude_ids:
        for x in exclude_ids:
            try:
                exclude_set.add(int(x))
            except:
                pass

    results = []
    for i in candidate_idx:
        # Benzerlik eşiği kontrolü (0.35 altı alakasız olabilir)
        if sims[int(i)] < 0.35:
            break
            
        film = _FILMS[int(i)]

        if film.get('id') in exclude_set:
            continue
        
        results.append(film)

        if len(results) >= top_k:
            break
            
    return results
