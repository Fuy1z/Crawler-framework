import json

from bald_spider.event import spider_closed
from bald_spider.pipeline import BasePipeline


class JsonlPipeline(BasePipeline):
    """本地 JSONL 文件入库"""

    def __init__(self, fd):
        self.fd = fd

    @classmethod
    def create_instance(cls, crawler):
        fd = open("winshang_data.jsonl", "a+", encoding="utf-8")
        o = cls(fd)
        crawler.subscriber.subscribe(o.spider_closed, event=spider_closed)
        return o

    async def process_item(self, item, spider):
        self.fd.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        self.fd.flush()
        return item

    async def spider_closed(self):
        self.fd.close()
