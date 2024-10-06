import re
import urllib

import requests
from bs4 import BeautifulSoup


def save_text(text, url):
    if url[-1] == '/': url = url[:-1]
    filename = 'files/wiki_test/' + url.split('/')[-1] + '.txt'
    filename = filename.replace(':', '_')
    with open(filename, 'w', encoding='utf8') as f:
        f.write(text)


def download_tree(url):
    history = set()
    queue = [url]

    while len(history) < 200 and len(queue) >= 1:
        current_url = queue[0]
        queue = queue[1:]

        print(current_url)

        r = requests.get(current_url)
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()

        save_text(text, current_url)

        history.add(current_url)

        next_urls = re.findall(r'href="(/wiki/.*?)"', html)
        next_urls = [urllib.parse.unquote(u) for u in next_urls]
        next_urls = [u for u in next_urls if u not in history and ':' not in u]
        next_urls = ['https://ru.wikipedia.org' + u for u in next_urls]
        
        queue.extend(next_urls)


def main():
    url = 'https://ru.wikipedia.org/wiki/TF-IDF'
    download_tree(url)


if __name__ == '__main__':
    main()
