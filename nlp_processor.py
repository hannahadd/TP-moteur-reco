import json
import re
import os
import nltk

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

FRENCH_STOPWORDS = set(stopwords.words("french"))

RE_K = re.compile(r"(\d+)\s*[kK]", re.IGNORECASE)
RE_NUM = re.compile(r"(\d{4,})")


def parse_salary(salary_str):
    m = RE_K.search(salary_str)
    if m:
        return int(m.group(1)) * 1000
    m = RE_NUM.search(salary_str)
    if m:
        return int(m.group(1))
    return None


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t.isalnum() and t not in FRENCH_STOPWORDS]
    return tokens


def process(raw_path, out_path):
    with open(raw_path, encoding="utf-8") as f:
        jobs = json.load(f)

    cleaned = []
    for job in jobs:
        cleaned.append({
            "id_offre": job["id_offre"],
            "titre": job["titre"],
            "salaire_num": parse_salary(job["salaire_brut"]),
            "tokens_description": normalize_text(job["description"]),
        })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    return cleaned


if __name__ == "__main__":
    cleaned = process("outputs/raw_jobs.json", "outputs/cleaned_jobs.json")
    print(f"Traité : {len(cleaned)} offres → outputs/cleaned_jobs.json")

    none_salary = [j for j in cleaned if j["salaire_num"] is None]
    if none_salary:
        print(f"Salaires non parsés : {len(none_salary)}")
    else:
        print("Tous les salaires ont été parsés.")
