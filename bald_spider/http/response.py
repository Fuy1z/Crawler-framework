import ujson, re
from parsel import Selector
from typing import Dict
from urllib.parse import urljoin as _urljoin

from bald_spider import Request
from bald_spider.execptions import DecodeError


class Response:

    def __init__(
            self,url: str,
            *,
            request: Request,
            headers: Dict,
            body: bytes = b"",
            status: int = 200,
    ):
        self.url = url
        self.request = request
        self.headers = headers
        self.body = body
        self.status = status
        self.encoding = request.encoding
        self._text_cache = None
        self._json_cache = None
        self._selector = None



    @property
    def text(self):
        if self._text_cache:
            return self._text_cache
        try:
            self._text_cache = self.body.decode(self.encoding)
        except UnicodeDecodeError:
            try:
                _encoding_re = re.compile(r"charset=([\w-]+)",flags=re.I)
                encoding_string = self.headers.get("Content-Type",'') or self.headers.get("content-type","")
                _encoding = _encoding_re.search(encoding_string)
                if _encoding:
                    self.encoding = _encoding.group(1)
                    self._text_cache = self.body.decode(self.encoding)
                else:
                    raise DecodeError(f"{self.request} {self.request.encoding} error")
            except UnicodeDecodeError as exc:
                raise UnicodeDecodeError(
                    exc.encoding, exc.object, exc.start, exc.end, f"{self.request}"
                )
        return self._text_cache
    def xpath(self,xpath_string):
        if self._selector is None:
            self._selector = Selector(self.text)
        return self._selector.xpath(xpath_string)

    def json(self):
        return ujson.loads(self.text)

    def urljoin(self, url):
        if self._json_cache:
            return self._json_cache
        self._json_cache = _urljoin(self.url, url)
        return self._json_cache

    def __str__(self):
        return f"<{self.status}> {self.url}"

    @property
    def meta(self):
        return self.request.meta
