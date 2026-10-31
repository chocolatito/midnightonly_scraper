import random
import re
import time
from curl_cffi import requests
from curl_cffi.requests.impersonate import REAL_TARGET_MAP
from lxml import etree


class ParserMixin:
    NS_REGEX = r'xmlns\s*=\s*"([^"]+)"'

    def configure_parser(self, *, proxies: dict = None, max_attempts: int = 3):
        self.proxies = proxies
        self.max_attempts = max_attempts
        imp_dict = [k for k in REAL_TARGET_MAP
                    if "_android" not in k and "_ios" not in k]

        def gen(): return random.choice(imp_dict)
        self.random_impersonate = gen
        self.ns = None

    def http_client(self, url: str,
                    mothod: str = "GET",
                    impersonate: str = None,
                    kwargs: dict = {}):
        tracker_err = []
        for _ in range(self.max_attempts):
            response = None
            if impersonate is None:
                impersonate = self.random_impersonate()
            try:
                response = requests.get(url,
                                        proxies=self.proxies,
                                        impersonate=impersonate,
                                        **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                print(e)
                tracker_err.append(str(e))
            if response:
                if response.status_code == 404:
                    raise Exception("404_ERROR")
                if response.status_code >= 500:
                    time.sleep(random.uniform(2, 3))
            time.sleep(random.uniform(0.5, 2))
        else:
            raise Exception(f"COULD_NOT_BE_REACHED: {url} -\n{tracker_err}")

    def xml_parser(self, xml_content: bytes):
        return etree.fromstring(xml_content)

    def get_root(self, url, impersonate: str = None, kwargs: str = {}, init_ns: bool = False):
        r = self.http_client(url, impersonate=impersonate, kwargs=kwargs)
        if init_ns:
            self.ns = {'sm': self.get_namespace_url(r.text)}
        return self.xml_parser(r.content)

    def get_namespace_url(self, xml_code: str) -> str:
        if not re.search(self.NS_REGEX, xml_code):
            raise Exception('NAME_SPACE_NOT_FOUND')
        return re.search(self.NS_REGEX, xml_code)[1]
