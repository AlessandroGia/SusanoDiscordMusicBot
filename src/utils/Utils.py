import wavelink
from bs4 import BeautifulSoup as bs
import requests


def search_url(url: str) -> str:
    if url.startswith('https://'):
        soup = bs(requests.get(url).text, "html.parser")
        url = soup.find("title").text
    return url


