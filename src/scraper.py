from logging import Logger
import re
from src import constants
from src.parser_mixin import ParserMixin
from src import utils


class Scraper(ParserMixin):
    XPATH_DICT = {
        "canon_url": '//div[@id="nav-above"]/div/a[@href]/@href',
        "title": '//div[contains(@id, "post-")]/h1/text()',
        "posted_on": '//div[contains(@id, "post-")]/h1/following-sibling::div[1]/a/span[1]/text()',
        "posted_by": '//div[contains(@id, "post-")]/h1/following-sibling::div[1]/span/a/text()',
        "content": '//div[contains(@id, "post-")]/h1/following-sibling::div[2]',
        "post_content": '//div[contains(@id, "post-")]/h1/following-sibling::div[3]',
    }
    SUB_TAG_DICT = {
        "_": r"</?i>|</?em>",
        "**": "</?b>|</?strong>",
        "": r"</?span>",
        "\n": "<br>",
        "\n\n": r"<iframe\s+.*?>.*?</iframe>",
    }
    IMG_TAG_COMPILE = re.compile(r'<img\b[^>]*?\bsrc=["\']([^"\']*)["\'][^>]*?>')

    def __init__(self, worker_id: str, logger: Logger) -> None:
        self.logger = utils.adapter_log(logger, {"worker_id": worker_id})
        if constants.PROXY is None:
            self.proxies = {}
        else:
            self.proxies = {"http": constants.PROXY, "https": constants.PROXY}
        self.configure_parser(proxies=self.proxies)
        self.result = {}

    def clean_raw_html(self, el, idx=0) -> str:
        if el.tag == 'iframe':
            return "\n"
        raw_html = self.to_string(el)
        # print(f"idx::: {idx}\n{raw_html}\n")
        for k, v in self.SUB_TAG_DICT.items():
            raw_html = re.sub(v, k, raw_html)
        raw_html = re.sub(r"\s\s\s+", " ", raw_html)
        raw_html = raw_html.strip()
        if not raw_html:
            raw_html = '<p></p>'
        raw_html = self.IMG_TAG_COMPILE.sub(r"![](\1)\n", raw_html)
        new_el = self.html_parser(raw_html)
        if new_el.xpath("./a[@href]"):
            for a_element in new_el.xpath("./a[@href]"):
                href = a_element.get('href')
                href_text = a_element.text_content()
                markdown_text = f'[{href_text}]({href})'

                parent = a_element.getparent()
                previous = a_element.getprevious()
                if previous is not None:
                    previous.tail = (previous.tail or '') + markdown_text + (a_element.tail or '')
                else:
                    parent.text = (parent.text or '') + markdown_text + (a_element.tail or '')
                parent.remove(a_element)
        return new_el.text_content()

    def scrape(self, url: str) -> None:
        self.logger.info(f"GET to {url}")
        tree = self.get_tree(url)
        for k in ["canon_url", "title", "posted_on", "posted_by"]:
            try:
                self.result[k] = tree.xpath(self.XPATH_DICT[k])[0]
            except Exception as e:
                raise Exception(f'MISSING VALUE FOR "{k}": {e}')

        content = tree.xpath(self.XPATH_DICT["content"])[0]
        post_content = tree.xpath(self.XPATH_DICT["post_content"])[0]
        paragraphs = [self.clean_raw_html(el, idx) for idx, el in enumerate(content.xpath("./*"), 1)]
        footers = [self.clean_raw_html(el, idx) for idx, el in enumerate(post_content.xpath("./*"), 1)]

        text = f'# {self.result["title"]}\n'
        text += "\n".join([p.strip() for p in paragraphs if p.strip()])
        text += "\n---\n"
        text += "\n".join([p.strip() for p in footers if p.strip()])
        self.result["markdown"] = text
        self.logger.info("Success")
