import asyncio
from typing import Optional, Generator,Callable
from inspect import iscoroutine


from bald_spider import Request
from bald_spider.core.downloader import DownloaderBase
from bald_spider.core.scheduler import Scheduler
from bald_spider.execptions import OutputError
from bald_spider.spider import Spider
from bald_spider.utils.spider import transform
from bald_spider.task_manager import TaskManager
from bald_spider.items.items import Item
from bald_spider.core.processor import Processor
from bald_spider.utils.log import get_logger
from bald_spider.utils.project import load_class
from bald_spider.event import spider_opened, spider_error, request_scheduled


class Engine:
    def __init__(self, crawler):
        self.settings = crawler.settings
        self.logger = get_logger(self.__class__.__name__)
        self.crawler = crawler
        self.downloader: Optional[DownloaderBase] = None
        self.scheduler:Optional[Scheduler] = None
        self.processor: Optional[Processor] = None
        self.start_requests: Optional[Generator] = None
        self.spider: Optional[Spider] = None
        self.task_manager: TaskManager = TaskManager(self.settings.getint('CONCURRENCY'))
        self.running = False
        self.normal = True

    def _get_downloader_cls(self):
        downloader_cls = load_class(self.settings.get('DOWNLOADER'))
        if not issubclass(downloader_cls, DownloaderBase):
            raise TypeError(f''
                            f'The downloader class ({self.settings.get("DOWNLOADER")}) '
                            f'does not fully implement required interface'
            )
        return downloader_cls

    def engine_start(self):
        self.running = True
        self.logger.info(
            f"bald_spider(version:{self.settings.get('VERSION')}) started. "
            f"(project name: {self.settings.get('PROJECT_NAME')})"
        )

    async def start_spider(self,spider):
        self.spider = spider
        downloader_cls = self._get_downloader_cls()
        self.downloader = downloader_cls.create_instance(self.crawler)
        self.processor = Processor(self.crawler)
        self.scheduler = Scheduler.create_instance(self.crawler)
        if hasattr(self.scheduler, 'open'):
            self.scheduler.open()
        if hasattr(self.downloader, 'open'):
            self.downloader.open()
        if hasattr(self.processor, 'open'):
            self.processor.open()
        self.start_requests = iter(spider.start_requests()) # noqa
        await self._open_spider()

    async def _open_spider(self):
        asyncio.create_task(self.crawler.subscriber.notify(spider_opened))
        crawling = asyncio.create_task(self.crawl())
        await crawling

    async def crawl(self):
        while self.running:
            if (request := await self._get_next_request()) is not None:
                await self._crawl(request)
            else:
                try:
                    start_request = next(self.start_requests) #取初始URL
                except StopIteration:
                    self.start_requests = None
                except Exception as exc:
                    if await self._exit(): # 检查队列和下载器是否为空
                        if self.start_requests is not None:
                            self.logger.error(f"Initial request error: {exc}")
                        self.running = False #如果为空 引擎停滞运行
                    continue
                else:
                    await self.enqueue_request(start_request)
        if not self.running:
            await self.close_spider()

    async def _crawl(self,request):
        async def crawl_task():
            outputs = await self._fetch(request)
            if outputs:
                await self._handle_spider_output(outputs)
        await self.task_manager.semaphore.acquire()
        self.task_manager.create_task(crawl_task())


    async def _fetch(self,request):
        async def _success(_response):
            callback: Callable = request.callback or self.spider.parse
            if _outputs := callback(_response):
                if iscoroutine(_outputs):
                    _outputs = await _outputs
                    return transform(_outputs, _response)
                else:
                    # 处理异步或普通生成器
                    return transform(_outputs, _response)
            return None
        _response = await self.downloader.fetch(request)
        if _response is None:
            return None
        outputs = await _success(_response)
        return outputs

    async def enqueue_request(self,request):
        await self._schedule_request(request)

    async def _schedule_request(self,request):
        if await self.scheduler.enqueue_request(request):
            asyncio.create_task(self.crawler.subscriber.notify(request_scheduled, request, self.crawler.spider))

    async def _get_next_request(self):
        return await self.scheduler.next_request()

    async def _handle_spider_output(self,outputs):
        async for spider_output in outputs:
            if isinstance(spider_output, (Request, Item)):
                await self.processor.enqueue(spider_output)
            elif isinstance(spider_output, Exception):
                asyncio.create_task(
                    self.crawler.subscriber.notify(spider_error, spider_output, self.spider)
                )
                raise spider_output
            else:
                raise OutputError(f'{type(self.spider)} must return Request or Item')


    async def _exit(self):
        if self.scheduler.idle() and self.downloader.idle() and self.task_manager.all_done() and self.processor.idle():
            return True
        return False

    async def close_spider(self):
        await asyncio.gather(*self.task_manager.current_task)
        await self.scheduler.close()
        await self.downloader.close()
        if self.normal:
            await self.crawler.close()

        




