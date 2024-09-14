import os
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

url_list = {}
try:
    api_key = os.environ["40b7d0605c8bef1c91f32eb3f071ce69e6c010f9"]
except KeyError:
    logger.error("URLSHORTX_API_KEY environment variable is not set")
    api_key = None

def search_movies(query):
    movies_list = []
    try:
        response = requests.get(f"https://185.53.88.104/?s={query.replace(' ', '+')}", timeout=10)
        response.raise_for_status()
        website = BeautifulSoup(response.text, "html.parser")
        movies = website.find_all("a", {'class': 'ml-mask jt'})
        for movie in movies:
            if movie:
                movies_details = {
                    "id": f"link{movies.index(movie)}",
                    "title": movie.find("span", {'class': 'mli-info'}).text
                }
                url_list[movies_details["id"]] = movie['href']
                movies_list.append(movies_details)
        return movies_list
    except requests.RequestException as e:
        logger.error(f"Error in search_movies: {e}")
        return []

def get_movie(query):
    movie_details = {}
    try:
        response = requests.get(url_list[query], timeout=10)
        response.raise_for_status()
        movie_page_link = BeautifulSoup(response.text, "html.parser")
        if movie_page_link:
            title = movie_page_link.find("div", {'class': 'mvic-desc'}).h3.text
            movie_details["title"] = title
            img = movie_page_link.find("div", {'class': 'mvic-thumb'})['data-bg']
            movie_details["img"] = img
            links = movie_page_link.find_all("a", {'rel': 'noopener', 'data-wpel-link': 'internal'})
            final_links = {}
            for i in links:
                if api_key:
                    url = f"https://urlshortx.com/api?api={api_key}&url={i['href']}"
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        link = response.json()
                        final_links[f"{i.text}"] = link['shortenedUrl']
                    except requests.RequestException as e:
                        logger.error(f"Error shortening URL: {e}")
                        final_links[f"{i.text}"] = i['href']  # Use original link if shortening fails
                else:
                    final_links[f"{i.text}"] = i['href']
            movie_details["links"] = final_links
        return movie_details
    except requests.RequestException as e:
        logger.error(f"Error in get_movie: {e}")
        return {}
