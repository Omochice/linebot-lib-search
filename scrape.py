from sys import executable
from bs4 import BeautifulSoup
from typing import Dict, Iterable, Tuple
import time
import re

from selenium import webdriver
from selenium.webdriver.support import ui, expected_conditions


class Scraper:
    def __init__(self,
                 local_debug_mode: bool = False,
                 driver_path: str = "",
                 chrome_path: str = "") -> None:
        self.url = "http://opc.ul.hirosaki-u.ac.jp/opc/xc/search/"
        self.debug = local_debug_mode
        if self.debug:
            pass
        else:
            self.driver_path = driver_path
            self.chrome_path = chrome_path

    def _setup(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shim-usage")
        if self.debug:
            self.driver = webdriver.Chrome(options=options)
        else:
            options.add_argument("--headless")
            options.binary_location = self.chrome_path
            self.driver = webdriver.Chrome(executable_path=self.driver_path,
                                           options=options)

    def scrape(self, query: str) -> dict:
        self._setup()
        self.driver.get(self.url + query)
        # ui.WebDriverWait(self.driver,
        #                  10).until(expected_conditions.presence_of_all_elements_located)
        # time.sleep(4)    # 日本語英語切り替えで遅延が必要, 2秒だとloading...になったりする
        ui.WebDriverWait(self.driver, 10).until(lambda driver: driver.execute_script(
            "return document.readyState") == "complete")
        r = self.driver.page_source.encode("utf-8")
        self.soup = BeautifulSoup(r, "html.parser")
        rst = self.find_book_info()
        self.driver.quit()
        return rst

    def find_book_info(self) -> dict:
        if self.driver.current_url.startswith(self.url):
            total_tag = self.soup.select_one(".total")
            if total_tag is None:
                return {"n_books": 0, "books":[]}
            rst = {
                "n_books": int(total_tag.get_text()),
                "books": []
            }
            for book in self.soup.find_all(class_="result-row"):
                title_a_tag = book.find(class_="xc-title")
                include_nobreakspace = title_a_tag.get_text().split(
                    ".", maxsplit=1)[-1].strip()
                book_status = {
                    "title": re.sub(r"\xa0", " ", include_nobreakspace),
                    "url": title_a_tag.find("a").get("href").split("?")[0],
                    "loanable": False,
                    "location": [],
                }
                status = book.find("td", class_="xc-availability")
                if status is None:
                    locate_url = book.find("tr", "xc-series").find("a").get_text()
                    book_status["locate_url"] = locate_url
                # urlを取得
                else:
                    for br in status.select("br"):
                        br.replace_with("\n")
                    condition = re.sub(r"他の [0-9]+ 件を見る隠す", "\n",
                                       status.text).split("\n")
                    for row in condition:
                        try:
                            cond, loc = row.split(",", maxsplit=1)
                        except Exception:
                            # print("loading がはいっている")
                            continue
                        if cond.strip() == "貸出可":
                            book_status["loanable"] = True
                            book_status["location"].append(loc)
                rst["books"].append(book_status)
            return rst
        else:
            return self._for_redirect()

    def _for_redirect(self) -> dict:
        trs = self.soup.select("tr.even")
        loanable = False
        location = []
        for tr in trs:
            book_status_tb = tr.select_one("div.bkAva.normal")
            if book_status_tb is None:
                continue
            elif book_status_tb.find("dd").get_text == "貸出可":
                loanable = True
                location.append(tr.select_one("div.bkLoc").find("a").get_text())
        rst = {
            "n_books": 1,
            "books": [{
                "title": self.soup.find("meta", attrs={"name": "title"}).get("content"), \
                "url": self.soup.find("meta", property="og:url").get("content"),
                "loanable": loanable,
                "location": location
            }]
        }
        return rst


if __name__ == "__main__":
    import sys
    client = Scraper(local_debug_mode=True)
    print(client.scrape(sys.argv[1]))
