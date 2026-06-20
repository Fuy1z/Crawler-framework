from bald_spider import Request


class Spider:
    def __init__(self):
        if not hasattr(self, 'start_urls'):
            self.start_urls = []
        self.crawler = None

    @classmethod
    def create_instance(cls, crawler):
        o = cls()
        o.crawler = crawler
        return o

    def start_requests(self) :
        if isinstance(self.start_urls, str):
            yield Request(url=self.start_urls,dont_filter=True)
        else:
            for url in self.start_urls:
                yield Request(url=url,dont_filter=True)

    def parse(self, response):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__

    async def spider_opened(self):
        pass

    async def spider_closed(self):
        pass

    async def spider_error(self):
        pass
