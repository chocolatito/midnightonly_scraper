from concurrent.futures import ThreadPoolExecutor
import re
from src import constants
from src.parser_mixin import ParserMixin
from src.scraper import Scraper
from src import utils


class Crawler(ParserMixin):

    SITEMAP_URL = "https://www.midnightonly.com/wp-sitemap.xml"

    def __init__(self) -> None:
        self.base_logger = utils.init__logger(constants.LOG_NAME)
        self.logger = utils.adapter_log(self.base_logger, {"worker_id": 'MAIN'})
        if constants.PROXY is None:
            self.proxies = {}
        else:
            self.proxies = {"http": constants.PROXY, "https": constants.PROXY}
        self.configure_parser(proxies=self.proxies)
        self.all_item_urls = []
        self.all_results = []

    def parallel_scrape(self, thread_id, item: dict) -> dict:
        try:
            scraper = Scraper(thread_id, self.logger)
            scraper.scrape(item["url"])
        except Exception as e:
            self.logger.warning(f"ERROR_SCRAPE: {thread_id} - {e}")
        else:
            scraper.result["lastmod"] = item["lastmod"]
            self.all_results.append(scraper.result.copy())

    def main(self):
        def f_url(u): return bool(re.search(r"wp-sitemap-posts-post-\d+.xml", u))

        def m_item(item): return {"url": item.find('sm:loc', self.ns).text,
                                  "lastmod": item.find('sm:lastmod', self.ns).text, }

        self.logger.info("START CRAWLER")
        main_root = self.get_root(self.SITEMAP_URL, init_ns=True)
        gen = (loc.text for loc in main_root.findall('sm:sitemap/sm:loc', self.ns))
        urls = list(filter(f_url, gen))
        self.logger.info(f"Sitemap urls ::: {len(urls)}")
        for url in urls:
            self.logger.info(f"Proccessing {url}")
            root = self.get_root(url)
            self.all_item_urls += list(map(m_item, root.findall('sm:url', self.ns)))

        total = len(self.all_item_urls)
        with ThreadPoolExecutor(max_workers=constants.MAX_WORKERS) as executor:
            for idx, item in enumerate(self.all_item_urls, 1):
                executor.submit(self.parallel_scrape, f"[{1}/{total}]", item)

        self.logger.info("Saving <all_results>")
        utils.save_json('all_results.json', self.all_results)
        self.logger.info("END CRAWLER")
