import cloudscraper
from bs4 import BeautifulSoup


class HtmlParserService:
  def __init__(self):
    self._scraper = cloudscraper.create_scraper()

  def parse(self, url: str) -> BeautifulSoup:
    html_text = self._scraper.get(url).text
    return BeautifulSoup(html_text, "lxml")
