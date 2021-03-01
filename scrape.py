import requests
from bs4 import BeautifulSoup
from typing import Dict, Iterable, Tuple
import time
import re

from selenium import webdriver
from selenium.webdriver.support import ui, expected_conditions


class Scraper:
    def __init__(self) -> None:
        self.url = "http://opc.ul.hirosaki-u.ac.jp/opc/xc/search/"
        self._setup()

    def _setup(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def scrape(self, query: str) -> Tuple[Dict]:
        self.driver.get(self.url + query)
        # ui.WebDriverWait(self.driver,
        #                  10).until(expected_conditions.presence_of_all_elements_located)
        time.sleep(4)    # 日本語英語切り替えで遅延が必要, 2秒だとloading...になったりする
        r = self.driver.page_source.encode("utf-8")
        self.soup = BeautifulSoup(r)
        return tuple(self.find_book_info())

    def find_book_info(self) -> Iterable[Dict]:
        for book in self.soup.select(".result-row"):
            book_status = {
                "title": book.find(class_="xc-title").get_text().split(".")[-1].strip(),
                "loanable": False,
                "location": [],
            }
            status = book.find("td", class_="xc-availability")
            if status is None:
                continue
            else:
                for br in status.select("br"):
                    br.replace_with("\n")
                condition = re.sub(r"他の [0-9]+ 件を見る隠す", "\n", status.text).split("\n")
                for row in condition:
                    cond, loc = row.split(",", maxsplit=1)
                    if cond.strip() == "貸出可":
                        book_status["loanable"] = True
                        book_status["location"].append(loc)
            yield book_status


if __name__ == "__main__":
    client = Scraper()
    for res in client.scrape("ruby"):
        print(res)
