from bald_spider.middleware import BaseMiddleware
from bald_spider.execptions import IgnoreRequest


class LoggingMiddleware(BaseMiddleware):
    """示例：记录每个请求的 URL 和方法"""

    @classmethod
    def create_instance(cls, crawler):
        return cls()

    async def process_request(self, request, spider):
        print(f"[请求] {request.method.upper()} {request.url}")


class BlockSensitiveMiddleware(BaseMiddleware):
    """示例：拦截特定域名的请求"""

    BLOCK_DOMAINS = {"internal.example.com", "admin.example.com"}

    @classmethod
    def create_instance(cls, crawler):
        return cls()

    async def process_request(self, request, spider):
        for domain in self.BLOCK_DOMAINS:
            if domain in request.url:
                raise IgnoreRequest(f"拦截敏感域名: {domain}")
