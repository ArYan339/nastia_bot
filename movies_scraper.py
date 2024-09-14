import os
import requests
from bs4 import BeautifulSoup

API_KEY = os.getenv("40b7d0605c8bef1c91f32eb3f071ce69e6c010f9")
BASE_URL = "https://185.53.88.104"

def search_movies(query):
    try:
        response = requests.get(f"{BASE_URL}/?s={query.replace(' ', '+')}", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        movies = soup.find_all("a", class_="ml-mask jt")
        return [{"id": movie['href'], "title": movie.find("span", class_="mli-info").text} for movie in movies]
    except Exception as e:
        print(f"Error in search_movies: {e}")
        return []

def get_movie(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find("div", class_="mvic-desc").h3.text
        links = soup.find_all("a", {'rel': 'noopener', 'data-wpel-link': 'internal'})
        download_links = {}
        for link in links:
            quality = link.text
            short_link = shorten_url(link['href'])
            download_links[quality] = short_link
        return {"title": title, "links": download_links}
    except Exception as e:
        print(f"Error in get_movie: {e}")
        return None

def shorten_url(url):
    if not API_KEY:
        return url
    try:
        response = requests.get(f"https://urlshortx.com/api?api={API_KEY}&url={url}", timeout=10)
        response.raise_for_status()
        return response.json()['shortenedUrl']
    except Exception as e:
        print(f"Error in shorten_url: {e}")
        return url
