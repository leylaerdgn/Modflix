import json
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
def build_text(f):
    # keyword'leri de ekliyoruz (tema sinyali)
    kws = " ".join(f.get("keywords", [])[:20])
    return f"{f.get('title','')} {f.get('overview','')} {kws}".strip()

def main():
    with open("films.json", "r", encoding="utf-8") as f:
        films = json.load(f)

    texts = [build_text(x) for x in films]

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    np.save("film_embeddings_v3.npy", embeddings)
    print("Saved film_embeddings.npy shape:", embeddings.shape)

if __name__ == "__main__":
    main()