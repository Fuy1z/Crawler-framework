import json

from bald_spider.pipeline import BasePipeline
from bald_spider.event import spider_opened, spider_closed


class JsonlPipeline(BasePipeline):
    """
    推荐模式：用事件订阅管理资源生命周期。

    spider_opened → 打开文件
    spider_closed → 关闭文件

    这样无论爬虫正常结束还是 Ctrl+C 中断，文件都会正确关闭。
    """

    @classmethod
    def create_instance(cls, crawler):
        o = cls()
        # 只做订阅，不做 IO
        crawler.subscriber.subscribe(o.on_open, event=spider_opened)
        crawler.subscriber.subscribe(o.on_close, event=spider_closed)
        return o

    async def on_open(self):
        self.fd = open("output.jsonl", "a+", encoding="utf-8")

    async def on_close(self):
        self.fd.close()

    async def process_item(self, item, spider):
        self.fd.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        self.fd.flush()
        return item
