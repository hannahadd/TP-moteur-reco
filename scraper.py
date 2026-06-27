import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://www-inf.telecom-sudparis.eu/COURS/CSC4538/Supports/"
STUDENT_ID = "hhaddaou"


def fetch_page(session, page_num):
    params = {
        "page": "exercices/project",
        "id": STUDENT_ID,
        "p": page_num,
    }
    response = session.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.text


def extract_salary(text):
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if any(kw in lower for kw in ["rémunération", "remuneration", "salaire"]):
            # Corrige la duplication "Rémunération : Rémunération : ..."
            prefix = "Rémunération : "
            if stripped.startswith(prefix) and stripped[len(prefix):].startswith(prefix):
                stripped = stripped[len(prefix):]
            return stripped
    return ""


def parse_jobs(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Cherche tous les éléments portant un attribut data-ref
    job_elements = soup.find_all(attrs={"data-ref": True})

    for elem in job_elements:
        id_offre = elem.get("data-ref", "").strip()

        # Le titre : premier élément de type heading ou strong
        titre_elem = elem.find(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"])
        titre = titre_elem.get_text(strip=True) if titre_elem else ""

        # Texte complet de l'offre (toutes balises)
        full_text = elem.get_text(separator="\n", strip=True)

        # Le salaire est la ligne contenant "Rémunération"
        salaire_brut = extract_salary(full_text)

        # Description = texte intégral brut
        description = full_text

        jobs.append({
            "id_offre": id_offre,
            "titre": titre,
            "description": description,
            "salaire_brut": salaire_brut,
        })

    return jobs


def has_next_page(html, current_page):
    soup = BeautifulSoup(html, "html.parser")
    # Cherche un lien vers la page suivante
    next_link = soup.find("a", href=lambda h: h and f"p={current_page + 1}" in h)
    return next_link is not None


def scrape_all():
    session = requests.Session()
    all_jobs = []
    page_num = 1

    while True:
        print(f"[page {page_num}] Téléchargement...", flush=True)
        html = fetch_page(session, page_num)
        jobs = parse_jobs(html)

        if not jobs:
            print(f"[page {page_num}] Aucune offre trouvée — fin du scraping.")
            break

        all_jobs.extend(jobs)
        print(f"[page {page_num}] {len(jobs)} offres extraites (total : {len(all_jobs)})")

        if not has_next_page(html, page_num):
            print("Plus de page suivante — fin du scraping.")
            break

        page_num += 1

    return all_jobs


if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)

    jobs = scrape_all()

    output_path = os.path.join("outputs", "raw_jobs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\nTerminé : {len(jobs)} offres sauvegardées dans {output_path}")
