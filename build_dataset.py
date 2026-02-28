import os, json, time, requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
LANG = "tr-TR"

def tmdb_get(path, params=None, timeout=10):
    params = params or {}
    params["api_key"] = API_KEY
    r = requests.get(f"{BASE_URL}{path}", params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def fetch_keywords(movie_id: int):
    # keywords genelde EN döner; sorun değil, tema sinyali verir
    try:
        data = tmdb_get(f"/movie/{movie_id}/keywords")
        kws = data.get("keywords", []) or []
        return [k.get("name","").strip() for k in kws if k.get("name")]
    except Exception:
        return []

def main(out_path="films.json", pages=40, min_vote=300):
    """
    pages=40 -> yaklaşık 800 film (her sayfa ~20)
    daha büyük istersen pages'i artırırsın (örn 200 -> ~4000 film)
    """
    films = []
    seen = set()

    for page in range(1, pages + 1):
        print(f"Page {page}/{pages} ...")
        data = tmdb_get("/discover/movie", {
            "language": LANG,
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "vote_count.gte": min_vote,
            "primary_release_date.gte": "1990-01-01",
            "page": page
        })

        for m in data.get("results", []):
            mid = m.get("id")
            if not mid or mid in seen:
                continue
            seen.add(mid)

            title = (m.get("title") or "").strip()
            overview = (m.get("overview") or "").strip()
            if not overview:
                continue

            kws = fetch_keywords(mid)

            films.append({
                "id": mid,
                "title": title,
                "overview": overview,
                "keywords": kws,
                "poster_path": m.get("poster_path"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
            })

        # TMDB'yi yormamak için küçük bekleme
        time.sleep(0.2)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print("Saved:", out_path, "Count:", len(films))

if __name__ == "__main__":
    main(out_path="films.json", pages=120, min_vote=200)