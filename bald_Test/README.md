# 🕷️ bald_spider

> 基于 Python asyncio 的轻量异步爬虫框架，API 风格致敬 Scrapy，内部全异步驱动。

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
  - [Spider（爬虫）](#spider爬虫)
  - [Request & Response](#request--response)
  - [Item（数据条目）](#item数据条目)
- [配置系统](#配置系统)
  - [Spider.custom_settings](#spidercustom_settings)
  - [深度优先 vs 广度优先](#depth_priority--深度优先-vs-广度优先)
- [异常体系](#异常体系)
- [自定义下载器](#自定义下载器)
- [中间件](#中间件)
- [管道](#管道)
- [去重过滤器](#去重过滤器)
  - [自定义过滤器](#自定义过滤器)
- [扩展系统](#扩展系统)
- [事件系统](#事件系统)
- [架构概览](#架构概览)
- [内置模块速查](#内置模块速查)
- [示例项目](#示例项目)

---

## 特性

- ⚡ **全异步**：Engine → Scheduler → Downloader → Processor 全链路 `async/await`
- 🧱 **组件化**：Spider / Middleware / Pipeline / Extension 均可插拔
- 🔄 **中间件链**：请求/响应/异常三阶段中间件，顺序可配
- 📦 **Pipeline 体系**：支持多管道链式处理，内置 Debug 输出
- 🔍 **去重过滤**：内存过滤 / Redis 过滤 / 文件持久化，开箱即用
- 📊 **统计收集**：请求数、响应码、入库量、耗时自动统计
- 📡 **事件订阅**：发布/订阅模式，扩展与核心解耦
- 🧵 **并发控制**：Semaphore 信号量精确控制并发数

---

## 安装

```bash
pip install aiohttp parsel ujson w3lib
```

然后将 `bald_spider` 目录放到你的项目路径下（或 `pip install -e .` 以可编辑模式安装）。

> 依赖：`aiohttp`（下载器）、`parsel`（xpath 解析）、`ujson`（快速 JSON）、`w3lib`（URL 规范化）

---

## 快速开始

### 1. 创建项目结构

```
my_project/
├── run.py            # 入口
├── settings.py       # 配置
├── items.py          # 数据模型
├── pipeline.py       # 入库逻辑
├── middleware.py     # 自定义中间件（可选）
└── spider/
    └── demo.py       # 爬虫
```

### 2. 定义 Item

```python
# items.py
from bald_spider import Item
from bald_spider.items import Field

class DemoItem(Item):
    title = Field()
    url = Field()
```

### 3. 编写 Spider

```python
# spider/demo.py
import json
from bald_spider import Spider, Request
from my_project.items import DemoItem

class DemoSpider(Spider):

    def start_requests(self):
        yield Request(
            url="https://httpbin.org/post",
            method="POST",
            body=json.dumps({"page": 1}),
            meta={"page": 1},
            dont_filter=True,
        )

    def parse(self, response):
        data = response.json()
        yield DemoItem(
            title=f"page-{response.meta['page']}",
            url=response.url,
        )
```

### 4. 编写 Pipeline

```python
# pipeline.py
import json
from bald_spider.pipeline import BasePipeline

class JsonlPipeline(BasePipeline):

    @classmethod
    def create_instance(cls, crawler):
        fd = open("output.jsonl", "a+", encoding="utf-8")
        return cls(fd)

    def __init__(self, fd):
        self.fd = fd

    async def process_item(self, item, spider):
        self.fd.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        self.fd.flush()
        return item
```

### 5. 配置文件

```python
# settings.py
PROJECT_NAME = "my_project"
CONCURRENCY = 2
LOG_LEVEL = "DEBUG"

DOWNLOADER = "bald_spider.core.downloader.aiohttp_downloader.AioDownloader"

MIDDLEWARES = [
    "bald_spider.middleware.default_header.DefaultHeader",
    "bald_spider.middleware.retry.Retry",
]

PIPELINES = [
    "my_project.pipeline.JsonlPipeline",
]

EXTENSIONS = [
    "bald_spider.extension.log_stats.LogStats",
]

FILTER_CLS = "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
```

### 6. 启动

```python
# run.py
import asyncio
from bald_spider.crawler import CrawlerProcess
from bald_spider.utils.project import get_settings
from my_project.spider.demo import DemoSpider

async def main():
    settings = get_settings()
    process = CrawlerProcess(settings)
    await process.crawl(DemoSpider)
    await process.start()

asyncio.run(main())
```

```bash
python run.py
```

---

## 核心概念

### Spider（爬虫）

所有爬虫继承 `bald_spider.Spider`，核心方法：

| 方法 | 说明 |
|---|---|
| `start_requests()` | 生成初始请求，必须 `yield Request(...)` |
| `parse(response)` | 默认回调，处理响应并 `yield Request` 或 `yield Item` |
| `spider_opened()` | 爬虫启动时调用（可选） |
| `spider_closed()` | 爬虫关闭时调用（可选） |

```python
class MySpider(Spider):
    custom_settings = {"CONCURRENCY": 3}  # 覆盖全局配置

    def start_requests(self):
        for url in ["https://example.com/page/1", ...]:
            yield Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        for href in response.xpath("//a/@href").getall():
            yield Request(url=response.urljoin(href), callback=self.parse_detail)

    def parse_detail(self, response):
        yield MyItem(title=response.xpath("//h1/text()").get())
```

### Request & Response

#### Request

```python
Request(
    url: str,                    # 请求地址
    method: str = "GET",         # GET / POST
    headers: dict = None,        # 请求头
    body: str = None,            # POST 请求体（JSON 字符串）
    cookies: dict = None,        # Cookie
    callback: callable = None,   # 响应回调（默认 self.parse）
    meta: dict = None,           # 跨请求传递数据
    dont_filter: bool = False,   # True 跳过去重
    priority: int = 0,           # 优先级（越大越优先）
    proxy: str = None,           # 代理
)
```

#### Response

| 属性/方法 | 说明 |
|---|---|
| `response.url` | 最终 URL |
| `response.status` | HTTP 状态码 |
| `response.headers` | 响应头 dict |
| `response.body` | 原始 bytes |
| `response.text` | 自动解码的文本（缓存） |
| `response.json()` | JSON 解析 |
| `response.xpath(xpath_str)` | xpath 选择器 |
| `response.urljoin(url)` | URL 拼接 |
| `response.meta` | → `response.request.meta` 快捷访问 |
| `response.request` | 对应的 Request 对象 |

### Item（数据条目）

Item 是类型安全的数据容器，字段通过 `Field()` 声明：

```python
from bald_spider import Item
from bald_spider.items import Field

class BookItem(Item):
    title = Field()
    author = Field()
    price = Field()

# 写入
item = BookItem(title="三体", author="刘慈欣", price="68")

# 读取
print(item["title"])        # 必须用 [] 访问
print(dict(item))           # 转普通字典
print(item.to_dict())       # 深拷贝为字典
```

> ⚠️ Item 字段只能用 `item["key"]` 读写，`item.key` 会抛异常。这是为了避免字段名与实例方法冲突。

---

## 配置系统

配置加载优先级：**Spider.custom_settings > 项目 settings.py > 框架默认值**

### 完整配置项

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `CONCURRENCY` | int | 1 | 并发请求数 |
| `LOG_LEVEL` | str | INFO | 日志级别：DEBUG / INFO / WARNING |
| `DOWNLOADER` | str | `aiohttp_downloader.AioDownloader` | 下载器类路径 |
| `USE_SESSION` | bool | True | 是否复用 HTTP 会话 |
| `REQUEST_TIMEOUT` | int | 60 | 请求超时（秒） |
| `VERIFY_SSL` | bool | True | SSL 证书验证 |
| `DOWNLOAD_DELAY` | float | 0 | 下载延迟（秒） |
| `RANDOMNESS` | bool | True | 是否启用随机延迟 |
| `RANDOM_RANGE` | tuple | (0.75, 1.25) | 随机延迟倍数范围 |
| `RETRY_HTTP_CODES` | list | [408,429,500,502,503,504,522,524] | 触发重试的状态码 |
| `IGNORE_HTTP_CODES` | list | [403,404] | 直接忽略的状态码 |
| `MAX_RETRY_TIMES` | int | 2 | 最大重试次数 |
| `ALLOWED_CODES` | list | [] | 重试失败仍进入回调的状态码 |
| `FILTER_CLS` | str | `memory_filter.MemoryFilter` | 去重过滤器类路径 |
| `FILTER_DEBUG` | bool | True | 去重日志开关 |
| `REQUEST_DIR` | str | None | 文件过滤器的持久化目录 |
| `DEPTH_PRIORITY` | int | 1 | 1=深度优先，-1=广度优先 |
| `MIDDLEWARES` | list | [...] | 中间件列表 |
| `PIPELINES` | list | [] | 管道列表 |
| `EXTENSIONS` | list | [] | 扩展列表 |
| `STATS_DUMP` | bool | True | 爬虫关闭时打印统计 |
| `INTERVAL` | int | 60 | 统计/日志间隔（秒） |
| `USER_AGENT` | str | None | 全局 UA（优先于 DEFAULT_HEADERS） |
| `DEFAULT_HEADERS` | dict | None | 全局默认请求头 |

### SettingsManager API

```python
settings.get("KEY")           # 获取字符串
settings.getint("KEY")        # 获取整数
settings.getfloat("KEY")      # 获取浮点数
settings.getbool("KEY")       # 获取布尔值（支持 0/1/True/False/true/false）
settings.getlist("KEY")       # 获取列表（字符串自动按逗号分割）
settings.getdict("KEY")       # 获取字典（字符串自动 JSON 解析）
```

### Spider.custom_settings

每个 Spider 可以通过 `custom_settings` 覆盖全局配置，常用于调节单个爬虫的并发、延迟等：

```python
class MySpider(Spider):
    custom_settings = {
        "CONCURRENCY": 4,          # 该爬虫专用并发数
        "DOWNLOAD_DELAY": 1,       # 该爬虫专用延迟
        "MAX_RETRY_TIMES": 5,      # 该爬虫专用重试次数
    }
```

> 优先级链：`Spider.custom_settings` > `settings.py` > `default_settings.py`

### DEPTH_PRIORITY — 深度优先 vs 广度优先

`DEPTH_PRIORITY` 控制请求队列的排序策略：

| 值 | 策略 | 行为 | 适用场景 |
|---|---|---|---|
| `1`（默认） | 深度优先 | 新产出的请求优先级逐渐降低，先深入一条链路 | 翻页、链式 API |
| `-1` | 广度优先 | 先处理完当前层所有请求，再进入下一层 | 列表页 → 详情页 |

```python
# 深度优先（默认）：翻页请求优先于详情请求
DEPTH_PRIORITY = 1

# 广度优先：先把当前页所有详情处理完，再翻页
DEPTH_PRIORITY = -1
```

原理：每次请求经过 Scheduler 时，`request.meta["depth"]` 自动 +1。优先级 = `request.priority - depth * DEPTH_PRIORITY`，值越小越先出队。

---

## 异常体系

框架定义了一套异常类，方便中间件和管道精确控制行为：

| 异常 | 用途 | 抛出位置 |
|---|---|---|
| `IgnoreRequest(msg)` | 丢弃当前请求（中间件返回 True 吞掉） | 中间件 `process_request` / `process_response` |
| `ItemDiscard(msg)` | 丢弃当前 Item（Pipeline 内部捕获） | 管道 `process_item` |
| `NotConfigured` | 中间件/组件自禁用（无日志静默跳过） | 中间件 `create_instance` |
| `InvalidOutput` | 回调/中间件返回值类型错误 | 框架内部 |
| `MiddlewareIntError` | 中间件未实现 `create_instance` | 框架内部 |
| `PipelineIntError` | 管道未实现 `create_instance` | 框架内部 |
| `TransformTypeError` | 回调返回值不是 generator | 框架内部 |
| `OutputError` | 回调 yield 了非 Request/Item | 框架内部 |
| `DecodeError` | Response.text 解码失败 | 框架内部 |

**常用场景**：

```python
# 中间件中丢弃请求
from bald_spider.execptions import IgnoreRequest
raise IgnoreRequest("IP 被封，丢弃请求")

# 管道中丢弃数据
from bald_spider.execptions import ItemDiscard
if not item["title"]:
    raise ItemDiscard("缺少标题")

# 中间件自禁用
from bald_spider.execptions import NotConfigured
if not settings.get("MY_FEATURE"):
    raise NotConfigured
```

---

## 自定义下载器

框架内置了 `AioDownloader`（aiohttp）和 `HTTPXDownloader`（httpx），你也可以实现自己的下载器。

### 基类约定

所有下载器必须继承 `DownloaderBase`，实现以下方法：

```python
from bald_spider.core.downloader import DownloaderBase
from bald_spider import Response

class MyDownloader(DownloaderBase):

    def __init__(self, crawler):
        super().__init__(crawler)
        # 初始化你的 HTTP 客户端

    def open(self):
        super().open()   # ← 必须调用，初始化中间件管理器
        # 连接池、会话等一次性准备工作

    async def download(self, request) -> Response:
        """核心：执行 HTTP 请求，返回 Response"""
        # 用你的 HTTP 库发送请求
        # 返回 Response(url=..., status=..., headers=..., body=..., request=request)

    async def close(self):
        # 清理资源：关闭连接池、释放会话等
```

### 完整示例：基于 aiohttp 实现

```python
from typing import Optional
from aiohttp import ClientSession, TCPConnector, ClientTimeout

from bald_spider import Response
from bald_spider.core.downloader import DownloaderBase

class AioDownloader(DownloaderBase):

    def __init__(self, crawler):
        super().__init__(crawler)
        self.session: Optional[ClientSession] = None
        self._timeout: Optional[ClientTimeout] = None
        self._use_session: Optional[bool] = None

        # 方法分发：GET → self._get, POST → self._post
        self.request_method = {
            "get": self._get,
            "post": self._post,
        }

    def open(self):
        super().open()
        self._timeout = ClientTimeout(
            self.crawler.settings.getint("REQUEST_TIMEOUT")
        )
        self._use_session = self.crawler.settings.getbool("USE_SESSION")
        if self._use_session:
            self.session = ClientSession(timeout=self._timeout)

    async def download(self, request) -> Optional[Response]:
        try:
            if self._use_session:
                response = await self.send_request(self.session, request)
                body = await response.content.read()
            else:
                async with ClientSession(timeout=self._timeout) as session:
                    response = await self.send_request(session, request)
                    body = await response.content.read()
        except Exception as exc:
            self.logger.error(f"请求异常: {exc}")
            raise

        return Response(
            url=str(response.url),
            headers=dict(response.headers),
            status=response.status,
            body=body,
            request=request,
        )

    async def send_request(self, session, request):
        method = self.request_method[request.method.lower()]
        return await method(session, request)

    @staticmethod
    async def _get(session, request):
        return await session.get(
            request.url, headers=request.headers,
            cookies=request.cookies, proxy=request.proxy,
        )

    @staticmethod
    async def _post(session, request):
        return await session.post(
            request.url, data=request.body, headers=request.headers,
            cookies=request.cookies, proxy=request.proxy,
        )

    async def close(self):
        if self.session:
            await self.session.close()
```

### 启用

```python
# settings.py
DOWNLOADER = "my_project.downloader.MyDownloader"
```

> **关键点**：`DownloaderBase.fetch()` 已经封装了中间件链调用，你的子类只需实现 `download(request) → Response`。`open()` 中务必调用 `super().open()` 来初始化中间件。

---

## 中间件

中间件按 **列表顺序** 处理请求，**逆序** 处理响应和异常：

```
请求方向：M1 → M2 → M3 → Downloader
响应方向：Downloader → M3 → M2 → M1
异常方向：Downloader → M3 → M2 → M1
```

### 内置中间件详解

#### 1. DefaultHeader — 默认请求头注入

```
路径: bald_spider.middleware.default_header.DefaultHeader
阶段: process_request（请求）
```

自动为每个请求注入全局 UA 和默认 Headers。**优先级**：Spider 实例上的 `user_agent` / `headers` 属性 > 配置文件中的 `USER_AGENT` / `DEFAULT_HEADERS`。

| 关联配置 | 说明 |
|---|---|
| `USER_AGENT` | 全局 UA 字符串 |
| `DEFAULT_HEADERS` | 全局请求头 dict |

```python
# 方式一：全局配置
USER_AGENT = "Mozilla/5.0 ..."
DEFAULT_HEADERS = {"Accept": "application/json"}

# 方式二：Spider 级别覆盖（优先级更高）
class MySpider(Spider):
    user_agent = "Mozilla/5.0 ..."
    headers = {"Accept": "application/json"}
```

实际行为：`request.headers.setdefault(key, value)`，即**不会覆盖**请求中已设置的 header。

---

#### 2. DownloadDelay — 下载延迟

```
路径: bald_spider.middleware.download_delay.DownloadDelay
阶段: process_request（请求）
```

在每次请求前 `asyncio.sleep()`，控制请求间隔。`DOWNLOAD_DELAY=0` 时该中间件**自动禁用**（抛 `NotConfigured`）。

| 关联配置 | 默认值 | 说明 |
|---|---|---|
| `DOWNLOAD_DELAY` | 0 | 固定延迟（秒），0=禁用 |
| `RANDOMNESS` | True | 是否启用随机延迟 |
| `RANDOM_RANGE` | (0.75, 1.25) | 随机倍数范围 |

```python
# 固定 2 秒延迟
DOWNLOAD_DELAY = 2
RANDOMNESS = False

# 随机 1.5~2.5 秒延迟
DOWNLOAD_DELAY = 2
RANDOMNESS = True
RANDOM_RANGE = (0.75, 1.25)   # 实际延迟 = 2 * random(0.75, 1.25)
```

---

#### 3. Retry — 自动重试

```
路径: bald_spider.middleware.retry.Retry
阶段: process_response（响应）+ process_exception（异常）
```

**响应阶段**：状态码命中 `RETRY_HTTP_CODES` 则重试，命中 `IGNORE_HTTP_CODES` 则放行不重试。

**异常阶段**：捕获网络层异常（连接错误、超时、协议错误等），自动重试。

| 关联配置 | 默认值 | 说明 |
|---|---|---|
| `RETRY_HTTP_CODES` | [408,429,500,502,503,504,522,524] | 触发重试的状态码 |
| `IGNORE_HTTP_CODES` | [403,404] | 不重试的状态码 |
| `MAX_RETRY_TIMES` | 2 | 最大重试次数 |
| `RETRY_PRIORITY` | 0 | 重试请求的优先级 |
| `ALLOWED_CODES` | [] | 重试耗尽仍放行的状态码 |
| `RETRY_EXCEPTIONS` | [] | 额外需要重试的异常类 |

重试逻辑：

```
收到响应 → 状态码在 IGNORE 列表？ → 放行
        → 状态码在 RETRY 列表？ → 未达上限？ → 重新调度（dont_filter=True）
                              → 已达上限？ → 返回 None（丢弃）
        → 其他状态码 → 放行

发生异常 → 异常类型可重试？ → 未达上限？ → 重新调度
                        → 已达上限？ → 抛出异常
```

可以通过 `request.meta["dont_retry"] = True` 禁止单个请求重试：

```python
yield Request(url="...", meta={"dont_retry": True})
```

重试的请求会自动设置 `dont_filter=True`，不会因为首次请求的指纹被去重过滤。

---

#### 4. ResponseFilter — 非 200 响应过滤

```
路径: bald_spider.middleware.response_filter.ResponseFilter
阶段: process_response（响应）
```

默认只放行 2xx 响应，其余抛 `IgnoreRequest` 丢弃。

| 关联配置 | 说明 |
|---|---|
| `ALLOWED_CODES` | 除 2xx 外额外放行的状态码列表 |

```python
# 允许 200-299 + 304 + 302
ALLOWED_CODES = [304, 302]
```

---

#### 5. ResponseCodeStats — 响应码统计

```
路径: bald_spider.middleware.response_code.ResponseCodeStats
阶段: process_response（响应）
```

纯统计中间件，不影响请求/响应链路。记录每个响应的状态码到 StatsCollector：

```
stats["response_codes/count/200"] = 156
stats["response_codes/count/404"] = 3
```

---

#### 6. RequestIgnore — 被忽略请求统计

```
路径: bald_spider.middleware.request_ignore.RequestIgnore
阶段: process_exception（异常）
```

当其他中间件抛出 `IgnoreRequest` 时，`RequestIgnore` 会：

1. 统计 `request_ignore_count` 及按原因分类的 `request_ignore_count/{reason}`
2. 返回 `True` 吞掉异常（停止异常链传播）

> ⚠️ 建议将此中间件放在 `MIDDLEWARES` **列表末尾**（异常链的最外层），这样它只捕获前面所有中间件未处理的 `IgnoreRequest`。

---

### 推荐顺序

```
MIDDLEWARES = [
    "DownloadDelay",     # ① 最先：控制请求速率
    "DefaultHeader",     # ② 注入请求头
    "Retry",             # ③ 响应阶段：判断是否需要重试
    "ResponseFilter",    # ④ 过滤非 200 响应
    "ResponseCodeStats", # ⑤ 统计状态码（纯观测）
    "RequestIgnore",     # ⑥ 最后：兜底统计被忽略的请求
]
```

### 自定义中间件

```python
from bald_spider.middleware import BaseMiddleware
from bald_spider.execptions import IgnoreRequest, NotConfigured

class CustomMiddleware(BaseMiddleware):

    @classmethod
    def create_instance(cls, crawler):
        # 返回 None 或抛 NotConfigured 可禁用此中间件
        if not crawler.settings.get("ENABLE_CUSTOM"):
            raise NotConfigured
        return cls()

    async def process_request(self, request, spider):
        # 返回 None → 继续链路
        # 返回 Request → 替换当前请求，重新调度
        # 返回 Response → 跳过下载，直接进入响应链路
        # 抛 IgnoreRequest → 丢弃请求
        pass

    async def process_response(self, request, response, spider):
        # 返回 Response → 继续
        # 返回 Request → 重新调度
        pass

    async def process_exception(self, request, exc, spider):
        # 返回 None → 不处理，交给下一个异常中间件
        # 返回 True → 异常已吞掉，当前请求无产出
        # 返回 Request → 重新调度
        # 返回 Response → 恢复为正常响应
        pass
```

---

## 管道

管道按 **列表顺序** 依次处理 Item，上一个管道的返回值作为下一个的输入。

### 推荐模式：订阅系统管理生命周期

涉及文件、数据库连接等资源时，推荐使用 **事件订阅** 来管理打开/关闭，而非在 `create_instance` 或 `__init__` 中直接操作：

```python
import json
from bald_spider.pipeline import BasePipeline
from bald_spider.event import spider_opened, spider_closed
from bald_spider.execptions import ItemDiscard

class JsonlPipeline(BasePipeline):

    @classmethod
    def create_instance(cls, crawler):
        o = cls()
        # 只订阅事件，不做 IO
        crawler.subscriber.subscribe(o.on_open, event=spider_opened)
        crawler.subscriber.subscribe(o.on_close, event=spider_closed)
        return o

    async def on_open(self):
        """爬虫启动时打开文件"""
        self.fd = open("output.jsonl", "a+", encoding="utf-8")

    async def on_close(self):
        """爬虫关闭时关闭文件"""
        self.fd.close()

    async def process_item(self, item, spider):
        self.fd.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        self.fd.flush()
        return item
```

**为什么这样做？**

| 方式 | 问题 |
|---|---|
| `__init__` 中打开文件 | 如果初始化后爬虫并未真正启动（抛异常），文件句柄泄漏 |
| `create_instance` 中打开 | 同上，且 factory 方法不适合做 IO |
| `spider_opened` 中打开 ✅ | 确保只在爬虫真正启动时才占用资源 |
| `spider_closed` 中关闭 ✅ | 无论正常结束还是 ctrl+c，框架都会触发该事件 |

### 内置 DebugPipeline

```
路径: bald_spider.pipeline.debug_pipeline.DebugPipeline
```

以 DEBUG 级别打印每个 Item 的字典内容，开发调试用。

### 自定义管道（无状态版）

如果管道不需要资源管理，最简单的方式：

```python
from bald_spider.pipeline import BasePipeline

class SimplePipeline(BasePipeline):

    @classmethod
    def create_instance(cls, crawler):
        return cls()

    async def process_item(self, item, spider):
        # 返回 item → 传递给下一个管道
        # 抛 ItemDiscard → 丢弃，不继续传递
        print(dict(item))
        return item
```

---

## 去重过滤器

请求去重基于 **URL + method + body** 的 MD5 指纹。

### MemoryFilter（内存）

```python
FILTER_CLS = "bald_spider.duplicate_filter.memory_filter.MemoryFilter"
REQUEST_DIR = ".."   # 可选：文件持久化指纹
```

### RedisFilter（分布式）

```python
FILTER_CLS = "bald_spider.duplicate_filter.redis_filter.RedisFilter"
REDIS_URL = "redis://localhost/0"
REDIS_KEY = "request_fingerprints"
SAVE_FP = False       # 是否持久化指纹
```

### 跳过去重

```python
Request(url="...", dont_filter=True)
```

### 自定义过滤器

继承 `BaseFilter`，只需实现 `add()` 和 `__contains__()`：

```python
from bald_spider.duplicate_filter import BaseFilter

class MyFilter(BaseFilter):

    def __init__(self, crawler):
        self.fingerprints: set[str] = set()
        logger = get_logger(f"{self}", crawler.settings.get("LOG_LEVEL"))
        super().__init__(logger, crawler.stats, crawler.settings.getbool("FILTER_DEBUG"))

    def add(self, fp: str) -> None:
        """存储指纹"""
        self.fingerprints.add(fp)

    def __contains__(self, fp: str) -> bool:
        """检查指纹是否存在"""
        return fp in self.fingerprints

    async def closed(self):
        """爬虫关闭时的清理（可选）"""
        pass
```

**基类已提供的能力**（无需重写）：

- `requested(request)` — 计算 Request 指纹，检查 → 存储，返回是否重复
- `log_stats(request)` — 记录过滤统计
- `create_instance(crawler)` — 工厂方法

**实现要点**：

| 方法 | 必须？ | 说明 |
|---|---|---|
| `add(fp)` | ✅ 必须 | 将指纹字符串持久化 |
| `__contains__(fp)` | ✅ 必须 | `fp in self` 返回 bool |
| `__init__(crawler)` | 可选 | 初始化存储结构 |
| `closed()` | 可选 | 爬虫关闭时清理资源 |

**示例：基于文件的过滤器**

```python
import os

class FileFilter(BaseFilter):
    def __init__(self, crawler):
        self.fingerprints: set[str] = set()
        logger = get_logger(f"{self}", crawler.settings.get("LOG_LEVEL"))
        super().__init__(logger, crawler.stats, crawler.settings.getbool("FILTER_DEBUG"))

        # 从文件恢复历史指纹
        self.file_path = os.path.join(
            crawler.settings.get("REQUEST_DIR", "."),
            "request_fingerprints.txt",
        )
        if os.path.exists(self.file_path):
            with open(self.file_path) as f:
                self.fingerprints.update(line.strip() for line in f)
        self._fd = open(self.file_path, "a+")

    def add(self, fp: str) -> None:
        self.fingerprints.add(fp)
        self._fd.write(fp + "\n")
        self._fd.flush()

    def __contains__(self, fp: str) -> bool:
        return fp in self.fingerprints

    async def closed(self):
        if self._fd:
            self._fd.close()
```

启用：

```python
# settings.py
FILTER_CLS = "my_project.filter.FileFilter"
REQUEST_DIR = ".."   # 文件存储目录
```

---

## 扩展系统

扩展通过 **事件订阅** 与核心解耦，在爬虫启停时自动回调。

### 内置扩展

| 扩展 | 功能 |
|---|---|
| `LogInterval` | 每隔 `INTERVAL` 秒打印爬取速率 |
| `LogStats` | 统计请求/响应/入库量，关闭时汇总打印 |

### 自定义扩展

```python
from bald_spider.event import spider_opened, spider_closed

class MyExtension:

    @classmethod
    def create_instance(cls, crawler):
        o = cls()
        crawler.subscriber.subscribe(o.on_open, event=spider_opened)
        crawler.subscriber.subscribe(o.on_close, event=spider_closed)
        return o

    async def on_open(self):
        print("爬虫启动了")

    async def on_close(self):
        print("爬虫关闭了")
```

---

## 事件系统

框架内置发布/订阅模式，核心组件通过事件通信：

| 事件常量 | 参数 | 触发时机 |
|---|---|---|
| `spider_opened` | — | 爬虫启动 |
| `spider_closed` | — | 爬虫关闭 |
| `spider_error` | exc, spider | Spider 输出异常 |
| `request_scheduled` | request, spider | 请求入队 |
| `response_receive` | response, spider | 收到响应 |
| `ignore_request` | exc, request, spider | 请求被中间件忽略 |
| `item_successful` | item, spider | Item 入库成功 |
| `item_discard` | item, exc, spider | Item 被丢弃 |

```python
from bald_spider.event import item_successful

crawler.subscriber.subscribe(my_handler, event=item_successful)
crawler.subscriber.unsubscribe(my_handler, event=item_successful)
```

---

## 架构概览

```
                         ┌──────────────┐
                         │  CrawlerProcess │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │    Crawler    │
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
     ┌────────▼──────┐  ┌──────▼──────┐  ┌───────▼───────┐
     │   Extension   │  │   Engine    │  │ StatsCollector │
     │   Manager     │  │             │  └───────────────┘
     └───────────────┘  └──────┬──────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
   ┌──────▼──────┐    ┌───────▼───────┐    ┌───────▼───────┐
   │  Scheduler  │    │  Downloader   │    │   Processor   │
   │  ┌────────┐ │    │  ┌─────────┐  │    │  ┌─────────┐  │
   │  │Filter  │ │    │  │Middleware│  │    │  │Pipeline │  │
   │  │(去重)  │ │    │  │(中间件) │  │    │  │(管道)   │  │
   │  └────────┘ │    │  └─────────┘  │    │  └─────────┘  │
   │  ┌────────┐ │    │  ┌─────────┐  │    └───────────────┘
   │  │Priority│ │    │  │aiohttp/ │  │
   │  │Queue   │ │    │  │httpx    │  │
   │  └────────┘ │    │  └─────────┘  │
   └─────────────┘    └───────────────┘
```

**数据流**：

1. `Spider.start_requests()` → 初始 Request
2. `Engine._get_next_request()` → 从 Scheduler 取出
3. `Downloader.fetch()` → 中间件链 → 网络请求
4. `Engine._fetch()` → 回调 `spider.parse(response)` → 获取产出
5. `Processor.enqueue()` → Request → 回到 Scheduler / Item → Pipeline
6. 循环直到队列空、下载器空闲、所有任务完成

**并发模型**：

- `TaskManager` 用 `asyncio.Semaphore` 控制并发数
- 每获取一个请求就创建 `asyncio.Task`，任务完成后释放信号量
- Scheduler / Processor 各自独立队列，无锁竞争

---

## 内置模块速查

```
bald_spider/
├── __init__.py              # 导出 Request, Response, Item, Spider 等
├── crawler.py               # Crawler / CrawlerProcess 入口
├── event.py                 # 事件常量定义
├── execptions.py            # 所有异常类
├── stats_collector.py       # 统计收集器
├── subscriber.py            # 发布/订阅
├── task_manager.py          # 并发任务管理
├── core/
│   ├── engine.py            # 核心引擎
│   ├── scheduler.py         # 请求调度器
│   ├── processor.py         # 输出处理器
│   └── downloader/
│       ├── __init__.py      # DownloaderBase / ActiveRequestManager
│       ├── aiohttp_downloader.py
│       └── httpx_downloader.py
├── http/
│   ├── request.py           # Request 类
│   └── response.py          # Response 类
├── items/
│   ├── __init__.py          # Field / ItemMeta
│   └── items.py             # Item 类
├── spider/
│   └── __init__.py          # Spider 基类
├── middleware/
│   ├── __init__.py          # BaseMiddleware
│   ├── middleware_manager.py
│   ├── default_header.py
│   ├── download_delay.py
│   ├── request_ignore.py
│   ├── response_code.py
│   ├── response_filter.py
│   └── retry.py
├── pipeline/
│   ├── __init__.py          # BasePipeline
│   ├── pipeline_manager.py
│   └── debug_pipeline.py
├── duplicate_filter/
│   ├── __init__.py          # BaseFilter
│   ├── memory_filter.py
│   ├── redis_filter.py
│   └── aioredis_filter.py
├── extension/
│   ├── __init__.py          # ExtensionManager
│   ├── log_interval.py
│   └── log_stats.py
├── settings/
│   ├── __init__.py
│   ├── default_settings.py
│   └── settings_manager.py
└── utils/
    ├── date.py
    ├── log.py               # LoggerManager
    ├── pqueue.py            # SpiderPriorityQueue
    ├── project.py           # get_settings / load_class / merge_settings
    ├── request.py           # request_fingerprint / set_request
    └── spider.py            # transform()
```

---

## 示例项目

仓库提供两个完整示例，可直接运行：

### 1. `example_project/` — 入门演示

基于 httpbin.org 公开 API，演示框架核心功能：

- POST + GET 请求
- 链式回调（parse_post → parse_json）
- Item 产出 + 自定义 Pipeline
- 自定义中间件
- 全组件启用

```bash
cd example_project
python run.py
# 输出 output.jsonl
```

### 2. `bald_test/` — 真实采集

赢商网（winshangdata.com）项目数据采集：

- 多级 API 链式请求（列表 → 详情 → 内容）
- 翻页控制
- JSONL 本地入库
- 内存去重
- 中间件 / 管道 / 扩展全启用

```bash
cd bald_test
python run.py
# 输出 winshang_data.jsonl
```
