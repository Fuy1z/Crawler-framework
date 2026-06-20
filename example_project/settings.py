# ============================================================
# bald_spider 项目配置文件
# ============================================================

PROJECT_NAME = "example_project"

# ── 并发 ──────────────────────────────────────────────
CONCURRENCY = 2          # 同时发出的请求数

# ── 日志 ──────────────────────────────────────────────
LOG_LEVEL = "INFO"       # DEBUG | INFO | WARNING

# ── 下载器 ────────────────────────────────────────────
# 可选: bald_spider.core.downloader.aiohttp_downloader.AioDownloader
#       bald_spider.core.downloader.httpx_downloader.HTTPXDownloader
DOWNLOADER = "bald_spider.core.downloader.aiohttp_downloader.AioDownloader"
USE_SESSION = True       # 复用 HTTP 会话（减少连接开销）
REQUEST_TIMEOUT = 30     # 请求超时秒数
VERIFY_SSL = True        # SSL 证书验证

# ── 中间件（推荐顺序：延迟 → 请求头 → 重试 → 过滤 → 统计 → 兜底）─
MIDDLEWARES = [
    "example_project.middleware.LoggingMiddleware",         # ① 自定义：日志
    "bald_spider.middleware.download_delay.DownloadDelay",  # ② 速率控制
    "bald_spider.middleware.default_header.DefaultHeader",  # ③ 请求头注入
    "bald_spider.middleware.retry.Retry",                   # ④ 自动重试
    "bald_spider.middleware.response_filter.ResponseFilter",# ⑤ 过滤非 200
    "bald_spider.middleware.response_code.ResponseCodeStats",#⑥ 状态码统计
    "bald_spider.middleware.request_ignore.RequestIgnore",  # ⑦ 兜底统计
]

# ── 管道 ──────────────────────────────────────────────
PIPELINES = [
    "bald_spider.pipeline.debug_pipeline.DebugPipeline",  # DEBUG 打印
    "example_project.pipeline.JsonlPipeline",             # JSONL 写入
]

# ── 扩展 ──────────────────────────────────────────────
EXTENSIONS = [
    "bald_spider.extension.log_stats.LogStats",    # 统计汇总
]
# INTERVAL = 10   # 速率日志间隔（秒），默认 60

# ── 去重 ──────────────────────────────────────────────
FILTER_CLS = "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
# REQUEST_DIR = ".."   # 如需文件持久化指纹，取消注释

# ── 下载延迟 ──────────────────────────────────────────
DOWNLOAD_DELAY = 0       # 0 = 禁用延迟
RANDOMNESS = False
# RANDOM_RANGE = (0.75, 1.25)

# ── 重试 ──────────────────────────────────────────────
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504, 522, 524]
IGNORE_HTTP_CODES = [403, 404]
MAX_RETRY_TIMES = 2
ALLOWED_CODES = []       # 重试耗尽后仍放行的状态码

# ── 全局请求头 ────────────────────────────────────────
USER_AGENT = "bald_spider/1.0 (example)"
DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
}

# ── 统计 ──────────────────────────────────────────────
STATS_DUMP = True        # 爬虫关闭时打印统计报告
