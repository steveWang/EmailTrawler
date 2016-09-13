As detailed in requirements.txt, this script relies on Selenium Webdriver
(using the Chrome webdriver).

Command-line usage is fairly simple: just invoke as follows:

	python trawler.py [--pages=M] [--results=N] ycombinator.com

(or any other valid url you can access via CURL)

Optional arguments limit the scope of crawling by placing limits on the
number of pages visited and the number of emails desired.
