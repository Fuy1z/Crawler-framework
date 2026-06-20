from abc import ABC, abstractmethod

from bald_spider import Request
from bald_spider.utils.request import request_fingerprint


class BaseFilter(ABC):

    def __init__(self, logger, stats, debug: bool):
        """
        :param logger: 用于记录消息的 Logger 实例。
        :param stats: 用于记录统计信息的 StatsCollector 实例。
        :param debug: 布尔值，指示是否启用了调试模式。
        """
        self.logger = logger
        self.stats = stats
        self.debug = debug

    @classmethod
    def create_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def requested(self, request: Request) -> bool:
        fp = request_fingerprint(request)
        if fp in self:
            return True
        self.add(fp)
        return False

    @abstractmethod
    def add(self, fp: str) -> None:
        pass

    def log_stats(self, request: Request) -> None:
        if self.debug:
            self.logger.debug(f"Filtered duplicate request: {request}")
        self.stats.inc_value(f"{self}/filtered_count")

    def __str__(self):
        return self.__class__.__name__