from pprint import pformat
from typing import List
from asyncio import create_task

from bald_spider.execptions import PipelineIntError, ItemDiscard, InvalidOutput
from bald_spider.utils.log import get_logger
from bald_spider.utils.project import load_class, common_call
from bald_spider.event import item_successful, item_discard


class PipelineManager:

    def __init__(self, crawler):
        self.crawler = crawler
        self.pipelines: List = []
        self.methods: List = []

        self.logger = get_logger(self.__class__.__name__, crawler.settings.get("LOG_LEVEL"))
        pipelines = crawler.settings.getlist("PIPELINES")
        self._add_pipelines(pipelines)
        self._add_methods()

    @classmethod
    def create_instance(cls, *args, **kwargs):
        o = cls(*args, **kwargs)
        return o

    def _add_pipelines(self, pipelines):
        for pipeline in pipelines:
            pipeline_cls = load_class(pipeline)
            if not hasattr(pipeline_cls, "create_instance"):
                raise PipelineIntError(
                    f"Pipeline init failed, must inherit from basePipeline or have create_instance method"
                )
            self.pipelines.append(pipeline_cls.create_instance(self.crawler))
        if pipelines:
            self.logger.info(f"enabled pipelines: \n {pformat(pipelines)}")

    def _add_methods(self):
        for pipeline in self.pipelines:
            if hasattr(pipeline, "process_item"):
                self.methods.append(pipeline.process_item)

    async def process_item(self, item):
        try:
            for method in self.methods:
                item = await common_call(method,item, self.crawler.spider)
                if item is None:
                    raise InvalidOutput(f"{method.__qualname__} return None is not supported")
        except ItemDiscard as exc:
            create_task(self.crawler.subscriber.notify(item_discard, item, exc, self.crawler.spider))
        else:
            create_task(self.crawler.subscriber.notify(item_successful, item, self.crawler.spider))




