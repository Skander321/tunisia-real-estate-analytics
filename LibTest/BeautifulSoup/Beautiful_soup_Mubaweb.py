# +
import time
import re
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup


LIST_URL = "https://www.mubawab.tn/fr/sc/appartements-a-vendre"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean_text(element):
    if element is None:
        return None
    text = element.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_reference(url):
    match = re.search(r"/a/(\d+)/", url)
    return match.group(1) if match else None


def extract_surface(text):
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", text)

    if match:
        return f"{match.group(1)} m²"

    return None


def scrape_mubawab_first_page(url):
    start = time.time()

    response = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    ads = []

    # Chaque annonce contient généralement un lien vers /fr/a/
    ad_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/fr/a/" in href:
            full_url = urljoin(url, href)

            if full_url not in ad_links:
                ad_links.append(full_url)

    for ad_url in ad_links[:10]:
        ad_response = requests.get(ad_url, headers=HEADERS, timeout=20)
        ad_soup = BeautifulSoup(ad_response.text, "html.parser")

        page_text = ad_soup.get_text(" ", strip=True)

        title = clean_text(ad_soup.find("h1"))

        price = clean_text(ad_soup.find(class_="fullPicturesPrice"))

        description = clean_text(ad_soup.find(class_="adDetails"))

        location = clean_text(ad_soup.find(class_="greyTit"))

        surface = extract_surface(page_text)

        ads.append({
            "reference": extract_reference(ad_url),
            "title": title,
            "price": price,
            "location": location,
            "surface": surface,
            "description": description,
            "url_source": ad_url,
        })

    df = pd.DataFrame(ads)

    # Supprimer les colonnes complètement vides
    df = df.dropna(axis=1, how="all")

    execution_time = round(time.time() - start, 3)

    print(f"Nombre d'annonces extraites : {len(df)}")
    print(f"Temps d'exécution : {execution_time} secondes")

    df["execution_time_sec"] = execution_time

    return df


df = scrape_mubawab_first_page(LIST_URL)

print(df.head())

df.to_csv("mubawab_first_page_beautifulsoup.csv", index=False, encoding="utf-8-sig")

# +
import time
import re
from urllib.parse import urljoin
import psutil
import os

import requests
import pandas as pd
from bs4 import BeautifulSoup


LIST_URL = "https://www.mubawab.tn/fr/sc/appartements-a-vendre"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean_text(element):
    if element is None:
        return None

    text = element.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def extract_reference(url):
    match = re.search(r"/a/(\d+)/", url)
    return match.group(1) if match else None


def extract_surface(text):
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", text)
    return f"{match.group(1)} m²" if match else None


def get_ad_links(limit=10):
    response = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/fr/a/" in href:
            full_url = urljoin(LIST_URL, href)

            if full_url not in links:
                links.append(full_url)

        if len(links) >= limit:
            break

    return links


def extract_description(soup, title):

    description = clean_text(soup.select_one(".blockProp"))

    if description and title:
        description = description.replace(title, "", 1).strip()

    return description

def extract_mubawab_ad(url):
    start = time.time()

    response = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = clean_text(soup)

    title = clean_text(soup.find("h1"))

    return {
        "Reference": extract_reference(url),
        "Title": title,
        "Price": clean_text(soup.find(class_="fullPicturesPrice")),
        "Location": clean_text(soup.find(class_="greyTit")),
        "Surface": extract_surface(page_text),
        "Description": extract_description(soup, title),
        "Url_annonce": url,
        "Execution_time_sec": round(time.time() - start, 3),
    }


def scrape_mubawab_first_page(limit=10):
    process = psutil.Process(os.getpid())
    ram_before = process.memory_info().rss / 1024 / 1024
    start = time.time()
    links = get_ad_links(limit)

    results = [extract_mubawab_ad(link) for link in links]
    df = pd.DataFrame(results)
    ram_after = process.memory_info().rss / 1024 / 1024
    ram_used = ram_after - ram_before

    print(f"Nombre de liens récupérés : {len(links)}")
    print(f"Nombre d'annonces extraites : {len(df)}")
    print(f"Temps total d'exécution : {round(time.time() - start, 3)} secondes")
    print(f"RAM utilisée : {ram_used:.2f} MB")

    return df


df = scrape_mubawab_first_page(limit=10)

display(df)

df.to_csv(
    "mubawab_beautifulsoup_details_clean.csv",
    index=False,
    encoding="utf-8-sig"
)
# -


