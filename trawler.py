from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
import sys
import re

class Scraper():
    def __init__(self):
        self.s = requests.Session()

    def go(self, url):
        return self.s.get(url).text

# Filter out images and compressed files that probably don't have emails in
# metadata. regex is probably overkill and can lead to poor performance,
# but network io is likely a larger bottleneck.
def is_web_page(url):
    return not re.search('(?i)\.(?:jpe?g|tiff?|bmp|rar|gif|png|zip|torrent|gz|bz2|gzip)$', url)

LOCAL_HELPER = r'[a-zA-Z!#$%&\'*+-/=?^_`|~]+'
LOCALPART = r'(?:(?:%s\.)*%s|"(?:[a-zA-Z!#$%%&\'*+-/=?^_`{|}~.]+)")' % (LOCAL_HELPER, LOCAL_HELPER)
LABEL = r'(?!-)[a-zA-Z0-9\-]{1,63}(?<!-)'
DOMAINPART = r'(?:%s\.)+%s' % (LABEL, LABEL)

# Ignore IP address literals and non-canonicalized addresses.

# To cut down on false positives, this regex deviates a bit from the email
# address specification by creating more false negatives -- for instance,
# it requires at least two labels in a domain name, and braces (i.e. {})
# are not valid characters in an email address.
EMAIL_PATTERN = re.compile('%s@%s' % (LOCALPART, DOMAINPART))

scraper = Scraper()

# Don't override specified schemes.
start_url = sys.argv[1]
if start_url.find('://') == -1:
    start_url = 'http://%s' % start_url

# Set start_url and consequently origin based on redirects.
start_url = scraper.s.get(start_url).url

origin = urlparse(start_url).netloc

queue = [start_url]
seen_pages = set(queue)
seen_emails = set()

# DFS to explore unseen URLs. [].append and [].pop implement this for us.
while len(queue):
    url = queue.pop()
    text = scraper.go(url)

    seen_emails |= set(EMAIL_PATTERN.findall(text))

    soup = BeautifulSoup(text, 'html.parser')
    for a in soup.findAll('a'):
        if not a.has_attr('href'):
            continue
        linked_url = urljoin(url, a['href']).rsplit('#', 1)[0]
        linked_origin = urlparse(linked_url).netloc
        # Only add each item to queue once, to reduce outer loop iterations.
        if linked_url not in seen_pages and linked_origin == origin and is_web_page(linked_url):
            seen_pages.add(linked_url)
            queue.append(linked_url)

print('\n'.join(seen_emails))
