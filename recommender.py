import json
import math
import os
from collections import Counter

PROFILES = {
    "Profil_A": ["python", "sql", "spark", "hadoop", "scala"],
    "Profil_B": ["python", "transformers", "nlp", "pytorch", "regex"],
    "Profil_C": ["python", "django", "api", "git", "bash"],
}


def build_tfidf_index(jobs):
    N = len(jobs)
    tf = {}
    df = Counter()

    for job in jobs:
        jid = job["id_offre"]
        tokens = job["tokens_description"]
        total = len(tokens)
        if total == 0:
            tf[jid] = {}
            continue
        count = Counter(tokens)
        tf[jid] = {tok: cnt / total for tok, cnt in count.items()}
        for tok in count:
            df[tok] += 1

    idf = {tok: math.log(N / cnt) for tok, cnt in df.items()}

    index = {}
    for jid, tf_scores in tf.items():
        for tok, tf_val in tf_scores.items():
            score = round(tf_val * idf[tok], 6)
            index.setdefault(tok, {})[jid] = score

    return index, idf


def cosine(vec_a, vec_b):
    dot = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in vec_a)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_job_vectors(index, job_ids):
    vecs = {jid: {} for jid in job_ids}
    for tok, doc_scores in index.items():
        for jid, score in doc_scores.items():
            vecs[jid][tok] = score
    return vecs


def recommend(skills, idf, job_vectors, top_k=3):
    p_vec = {skill: idf[skill] for skill in skills if skill in idf}
    scores = [
        {"id_offre": jid, "score": round(cosine(p_vec, jvec), 4)}
        for jid, jvec in job_vectors.items()
    ]
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


def main():
    with open("outputs/cleaned_jobs.json", encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"Chargé : {len(jobs)} offres")

    index, idf = build_tfidf_index(jobs)

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/tfidf_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Index TF-IDF : {len(index)} tokens")

    job_ids = [j["id_offre"] for j in jobs]
    job_vectors = build_job_vectors(index, job_ids)

    recommendations = {}
    for profil, skills in PROFILES.items():
        top = recommend(skills, idf, job_vectors)
        recommendations[profil] = top
        print(f"\n{profil} {skills}")
        for r in top:
            print(f"  {r['id_offre']}  score={r['score']}")

    with open("outputs/recommendations.json", "w", encoding="utf-8") as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    print("\nSauvegardé : outputs/recommendations.json")


if __name__ == "__main__":
    main()
