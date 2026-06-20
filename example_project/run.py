"""
bald_spider 示例项目入口

使用方式：
    1. 确保已将 bald_spider 框架放入 Python 路径
    2. python run.py

本示例演示了：
    - POST + GET 请求
    - 链式回调（parse_post → parse_json）
    - Item 产出与管道入库
    - 中间件 + 管道 + 扩展全启用
"""

import asyncio
import sys
from pathlib import Path

# 将桌面目录加入 sys.path，确保 example_project 可被导入
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from bald_spider.crawler import CrawlerProcess
from bald_spider.utils.project import get_settings
from example_project.spiders.httpbin_spider import HttpbinSpider


async def main():
    settings = get_settings()          # 自动加载 settings.py
    process = CrawlerProcess(settings)
    await process.crawl(HttpbinSpider)  # 可多次 crawl 启动多个爬虫
    await process.start()              # 等待所有爬虫完成


if __name__ == "__main__":
    asyncio.run(main())
