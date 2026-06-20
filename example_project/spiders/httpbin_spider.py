from bald_spider import Spider, Request
from bald_spider.utils.log import get_logger
from example_project.items import BookItem


class HttpbinSpider(Spider):
    """演示：GET/POST 请求 + 链式回调 + Item 产出"""

    # 可在 Spider 上直接声明 headers，优先级高于 settings 中的 DEFAULT_HEADERS
    headers = {
        "User-Agent": "bald_spider/1.0",
        "Accept": "application/json",
    }

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    # ── 入口 ────────────────────────────────────────────

    def start_requests(self):
        """初始请求：POST 到 httpbin"""
        yield Request(
            url="https://httpbin.org/post",
            method="POST",
            body='{"page": 1, "source": "bald_spider"}',
            headers=self.headers,
            callback=self.parse_post,
            dont_filter=True,
            meta={"source": "start_requests"},
        )

    # ── 回调 1：处理 POST 响应 ──────────────────────────

    def parse_post(self, response):
        data = response.json()
        self.logger.info(f"POST 返回 origin: {data.get('origin', 'unknown')}")

        # 产出 Item
        yield BookItem(
            title="POST 响应",
            author=data.get("origin", ""),
            url=response.url,
        )

        # 链式请求：再去 GET 一个 JSON 接口
        yield Request(
            url="https://httpbin.org/json",
            method="GET",
            callback=self.parse_json,
            dont_filter=True,
            meta={"source": "parse_post"},
        )

    # ── 回调 2：处理 GET 响应 ───────────────────────────

    def parse_json(self, response):
        data = response.json()
        slides = data.get("slideshow", {}).get("slides", [])

        for slide in slides:
            yield BookItem(
                title=slide.get("title", "无标题"),
                author="httpbin.org",
                url=response.url,
            )

        self.logger.info(f"共解析 {len(slides)} 条数据")
