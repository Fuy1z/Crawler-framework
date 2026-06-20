PROJECT_NAME = "bald_test"

# ── 并发 ──────────────────────────────────────────────
CONCURRENCY = 1

# ── 日志 ──────────────────────────────────────────────
LOG_LEVEL = "DEBUG"

# ── 下载器 ────────────────────────────────────────────
DOWNLOADER = "bald_spider.core.downloader.aiohttp_downloader.AioDownloader"
USE_SESSION = True
REQUEST_TIMEOUT = 60
VERIFY_SSL = True

# ── 中间件（请求从前到后，响应/异常从后到前）──────────
MIDDLEWARES = [
    "bald_spider.middleware.download_delay.DownloadDelay",
    "bald_spider.middleware.default_header.DefaultHeader",
    "bald_spider.middleware.response_filter.ResponseFilter",
    "bald_spider.middleware.retry.Retry",
    "bald_spider.middleware.response_code.ResponseCodeStats",
    "bald_spider.middleware.request_ignore.RequestIgnore",
]

# ── 扩展 ──────────────────────────────────────────────
EXTENSIONS = [
    "bald_spider.extension.log_interval.LogInterval",
    "bald_spider.extension.log_stats.LogStats",
]
INTERVAL = 5  # 统计打印间隔（秒）

# ── 入库 ──────────────────────────────────────────────
PIPELINES = [
    "bald_spider.pipeline.debug_pipeline.DebugPipeline",
    "bald_test.pipeline.JsonlPipeline",
]

# ── 去重 ──────────────────────────────────────────────
FILTER_CLS = "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
REQUEST_DIR = ".."

# ── 下载延迟 ──────────────────────────────────────────
DOWNLOAD_DELAY = 0
RANDOMNESS = False
RANDOM_RANGE = (0.75, 1.25)

# ── 重试 ──────────────────────────────────────────────
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504, 522, 524]
IGNORE_HTTP_CODES = [403, 404]
MAX_RETRY_TIMES = 2
ALLOWED_CODES = []

# ── 请求头 ────────────────────────────────────────────
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
