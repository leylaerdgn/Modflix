from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import json
import os
load_dotenv()

# ✅ Senin utils.py'de zaten hazır ve en güçlü fonksiyon bu:
from utils import get_movies_by_semantic_similarity, get_empathetic_response
story_bp = Blueprint("story_bp", __name__)

IMG_BASE = "https://image.tmdb.org/t/p/w500"

def get_local_movie_ids():
    """films.json dosyasındaki güncel film ID'lerini döndürür."""
    try:
        if os.path.exists("films.json"):
            with open("films.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return {m.get("id") for m in data if m.get("id")}
    except:
        pass
    return set()

@story_bp.route("/api/story-recommendations", methods=["POST"])
def story_recommendations():
    data = request.get_json(silent=True) or {}
    user_text = (data.get("text") or "").strip()

    if len(user_text) < 3:
        return jsonify({"error": "Metin çok kısa."}), 400

    # ✅ En iyi eşleştirme: keyword+genre havuzu + BM25 + TFIDF + MMR (exclude_ids'i düzelt)
    # Daha fazla aday çekip (15), silinenleri eledikten sonra 6 tanesini alalım
    movies = get_movies_by_semantic_similarity(user_text, top_k=15)

    # films.json'dan silinenleri filtrele
    valid_ids = get_local_movie_ids()
    if valid_ids:
        movies = [m for m in movies if m.get("id") in valid_ids]

    response_msg = get_empathetic_response(user_text)

    results = []
    for m in movies[:6]:
        results.append({
            "tmdbId": m.get("id"),
            "title": m.get("title"),
            "overview": m.get("overview"),
            "release_date": m.get("release_date"),
            "vote_average": m.get("vote_average"),
            "poster": f"{IMG_BASE}{m.get('poster_path')}"
        })

    return jsonify({"results": results, "response_message": response_msg})