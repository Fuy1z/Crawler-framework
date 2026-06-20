import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from bald_spider.crawler import CrawlerProcess
from bald_spider.utils.project import get_settings
from bald_test.spider.bald_test import WinshangSpider


async def run():
    settings = get_settings()
    process = CrawlerProcess(settings)
    await process.crawl(WinshangSpider)
    await process.start()


asyncio.run(run())
