
PROJECT_NAME = "bald_test"

# 并发数量
CONCURRENCY = 1

# 日志等级
LOG_LEVEL = 'DEBUG'

# 是否session保持
USE_SESSION = True

# 下载器 ...aiohttp_downloader.AioDownloader or ...httpx_downloader.HTTPXDownloader
DOWNLOADER = "bald_spider.core.downloader.aiohttp_downloader.AioDownloader"

# 下载速度日志 秒
INTERVAL = 5

# 统计器
STATS_DUMP = True

# 中间件 请求越前越先处理, 响应  错误 越后越先处理
MIDDLEWARES = [
    #'baidu_spider.middleware.TestMiddleware',
    #'baidu_spider.middleware.TestMiddleware2',
    'bald_spider.middleware.download_delay.DownloadDelay',
    'bald_spider.middleware.default_header.DefaultHeader',
    'bald_spider.middleware.response_filter.ResponseFilter',
    'bald_spider.middleware.retry.Retry',
    'bald_spider.middleware.response_code.ResponseCodeStats',
    'bald_spider.middleware.request_ignore.RequestIgnore',
]

# 拓展
EXTENSIONS = [
    'bald_spider.extension.log_interval.LogInterval',
    'bald_spider.extension.log_stats.LogStats'
]

# # 入库
# PIPELINES = [
#     'bald_spider.pipeline.debug_pipeline.DebugPipeline',
#     'baidu_spider.pipeline.TestPipeline'
# ]

# 下载延迟
DOWNLOAD_DELAY = 0
# 随机延迟
RANDOMNESS = False
# 随机延迟倍数 为DOWNLOAD_DELAY * 最小值 --- DOWNLOAD_DELAY * 最大值之间
RANDOM_RANGE = (0.75, 1.25)

# 请求重试
# 允许重试的状态
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504, 522, 524]
# 不允许重试的状态
IGNORE_HTTP_CODES = [403, 404]
# 重试次数
MAX_RETRY_TIMES = 2
# 允许重试的状态通过,比如 408 在重试多次失败后,他不会再进入你的callback,而是直接抛弃,填入后不会抛弃,继续进入你的处理函数
ALLOWED_CODES = []

# UA头 优先级高会覆盖请求头的UA
USER_AGENT = "Mozilla/7.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
# 请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/6.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}


DB_NAME = "bald_spider"


# 过滤器 "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
#FILTER_CLS = "bald_spider.duplicate_filter.redis_filter.RedisFilter"

# REQUEST_DIR 当使用内存过滤器时,添加该关键字改为基于文件过滤
REQUEST_DIR = ".."  # 文件路径


# redis 过滤器
REDIS_URL = "redis://localhost/0" # redis://[[username]:[password]]@host:port/db
DECODE_RESPONSES = True
REDIS_KEY = "request_fingerprints"
#持久化存储 URL指纹
SAVE_FP = False
