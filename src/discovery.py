import re
import constants
from parser_mixin import ParserMixin
import utils


class Crawler(ParserMixin):

    SITEMAP_URL = "https://www.midnightonly.com/wp-sitemap.xml"

    def __init__(self) -> None:
        self.base_logger = utils.init__logger(constants.LOG_NAME)
        self.logger = utils.adapter_log(self.base_logger, {"worker_id": 'MAIN'})
        self.title_result = []
        if constants.PROXY is None:
            self.proxies = {}
        else:
            self.proxies = {"http": constants.PROXY, "https": constants.PROXY}
        self.configure_parser(proxies=self.proxies)
        self.results_by_title = []
        self.director_dict = {}
        self.all_urls = []

    def main(self):
        def f_url(u): return bool(
            re.search(r"wp-sitemap-posts-post-\d+.xml", u))

        def m_item(item): return {"url": item.find('sm:loc', self.ns).text,
                                  "lastmod": item.find('sm:lastmod', self.ns).text, }

        main_root = self.get_root(self.SITEMAP_URL, init_ns=True)
        gen = (loc.text for loc in main_root.findall('sm:sitemap/sm:loc', self.ns))
        urls = list(filter(f_url, gen))
        self.logger.info(f"urls ::: {len(urls)}")
        for url in urls:
            self.logger.info(f"Proccessing {url}")
            root = self.get_root(url)
            self.all_urls += list(map(m_item, root.findall('sm:url', self.ns)))
        utils.save_json(file_path="results.json", data=self.all_urls)
