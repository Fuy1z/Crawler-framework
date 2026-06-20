"""
default config
"""
VERSION = 1.0

# 并发默认 1
CONCURRENCY = 1

#日志等级
LOG_LEVEL = 'INFO'

# SSL认证
VERIFY_SSL = True

# 请求失败等待时间
REQUEST_TIMEOUT = 60

# 是否session保持
USE_SESSION = True

# 下载器选择 aiohttpx_downloader.AioDownloader or httpx_downloader.HTTPXDownloader
DOWNLOADER = "bald_spider.core.downloader.aiohttp_downloader.AioDownloader"

# 是否开启统计收集器
STATS_DUMP = True
# 每多少秒打印统计内容
INTERVAL = 60


MIDDLEWARES = [
    'bald_spider.middleware.request_ignore.RequestIgnore',
    'bald_spider.middleware.response_code.ResponseCodeStats',
    'bald_spider.middleware.download_delay.DownloadDelay'
]

# 下载延迟
DOWNLOAD_DELAY = 0
# 随机延迟
RANDOMNESS = True
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

# 过滤器日志
FILTER_DEBUG = True

# 过滤器 "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
FILTER_CLS = "bald_spider.duplicate_filter.memory_filter.MemoryFilter"

# redis_filter
REDIS_URL = "redis://localhost/0" # redis://[[username]:[password]]@host:port/db
DECODE_RESPONSES = True
REDIS_KEY = "request_fingerprints"
#持久化存储
SAVE_FP = False

# 重试优先级
TRY_PRIORITY = 0

# 深度优先级 1 深度优先, -1 广度优先
DEPTH_PRIORITY = 1