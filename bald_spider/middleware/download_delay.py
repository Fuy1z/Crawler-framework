from asyncio import sleep
from random import uniform

from bald_spider.execptions import NotConfigured
from bald_spider.utils.log import get_logger


class DownloadDelay:
    def __init__(self, settings, log_level):
        self.dealy = settings.getfloat('DOWNLOAD_DELAY')
        if not self.dealy:
            raise NotConfigured("")
        self.randomness = settings.getbool('RANDOMNESS')
        self.floor, self.upper = settings.getlist("RANDOM_RANGE")

        self.logger = get_logger(self.__class__.__name__, log_level)

    @classmethod
    def create_instance(cls, crawler):
        o = cls(
            settings=crawler.settings,
            log_level=crawler.settings.get('LOG_LEVEL'),
        )
        return o
    async def process_request(self, _request, _spider):
        if self.randomness:
            await sleep(uniform(self.dealy * self.floor, self.dealy * self.upper))
        else:
            await sleep(self.dealy)
