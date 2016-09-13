from selenium import webdriver
from urllib.parse import urlparse, urljoin
import sys
import re

class Scraper():
    def __init__(self):
        self.s = webdriver.Chrome()

    def go(self, url):
        self.s.get(url)
        return self.s.page_source

# Filter out various downloadable files that probably don't have emails in
# metadata. regex is probably overkill and can lead to poor performance,
# but network io is likely a larger bottleneck.
def is_web_page(url):
    return not re.search('(?i)\.(?:jpe?g|tiff?|bmp|rar|gif|png|zip|torrent|gz|bz2|gzip|docx?|xlsx?|pptx?|pdf|tex|dvi|ps|au|tar|ics)$', url)

def is_same_origin(o1, o2):
    # Pretend www.X is the same origin as X.
    if len(o1) == len(o2) - 4:
        o1, o2 = o2, o1
    return o1 == o2 or o1 == "www." + o2

LOCAL_HELPER = r'[a-zA-Z+\-_]{,250}'
LOCALPART = r'(?:(?:%s\.)*%s|"(?:[a-zA-Z+\-_\.]+)")' % (LOCAL_HELPER, LOCAL_HELPER)
LABEL = r'(?!-)[a-zA-Z0-9\-]{1,63}(?<!-)'
DOMAINPART = r'(?:%s\.)+%s' % (LABEL, LABEL)

# Ignore IP address literals and non-canonicalized addresses.

# To cut down on false positives, this regex deviates a bit from the email
# address specification by creating more false negatives -- for instance,
# it requires at least two labels in a domain name, and braces (i.e. {})
# are not valid characters in an email address.
EMAIL_PATTERN = re.compile('%s@%s' % (LOCALPART, DOMAINPART))

if len(sys.argv) < 2:
    # abort with informative message.
    print("Usage: python trawler.py example.com")
    sys.exit()

scraper = Scraper()

# Don't override specified schemes.
start_url = sys.argv[1]
if start_url.find('://') == -1:
    start_url = 'http://%s' % start_url

# Set start_url and consequently origin based on redirects.
scraper.go(start_url)
start_url = scraper.s.current_url

origin = urlparse(start_url).netloc

queue = [start_url]
seen_pages = set(queue)
seen_emails = set()

# DFS to explore unseen URLs. [].append and [].pop implement this for us.
while len(queue):
    url = queue.pop()
    text = scraper.go(url)
    url = scraper.s.current_url

    # Debatable whether to add these if url changed from a redirect.
    curr_origin = urlparse(url).netloc
    if not is_same_origin(origin, curr_origin):
        continue
    
    seen_emails |= set(EMAIL_PATTERN.findall(text))

    for a in scraper.s.find_elements_by_tag_name('a'):
        try:
            href = a.get_attribute('href')
        except:
            continue
        if href == None:
            continue
        linked_url = urljoin(url, href).rsplit('#', 1)[0]
        linked_origin = urlparse(linked_url).netloc
        # Only add each item to queue once, to reduce outer loop iterations.
        if linked_url not in seen_pages and is_same_origin(origin, linked_origin) and is_web_page(linked_url):
            seen_pages.add(linked_url)
            queue.append(linked_url)

print('\n'.join(seen_emails))
