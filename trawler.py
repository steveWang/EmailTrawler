from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import sys
import re

class Scraper():
    def __init__(self):
        self.s = requests.Session()

    def go(self, url):
        return BeautifulSoup(self.s.get(url).text, 'html.parser')

# This doesn't override existing schemes.
start_url = sys.argv[1]
if start_url.find('://') == -1:
    start_url = 'http://%s' % start_url

origin = urlparse(start_url).netloc

scraper = Scraper()

queue = [start_url]
seen_pages = set(queue)

# DFS to explore unseen URLs. [].append and [].pop implement this for us.
while len(queue):
    url = queue.pop()
    text = scraper.go(url)

    for a in text.findAll('a'):
        if not a.has_attr('href'):
            continue
        linked_url = urljoin(url, a['href'])
        # Only add each item to queue once, to reduce outer loop iterations.
        linked_origin = urlparse(linked_url).netloc
        if linked_url not in seen_pages and linked_origin == origin:
            seen_pages.add(linked_url)
            queue.append(linked_url)

print(seen_pages)
