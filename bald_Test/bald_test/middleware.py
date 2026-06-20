from bald_spider.middleware import BaseMiddleware


class TestMiddleware(BaseMiddleware):
    """示例：请求拦截"""

    def process_request(self, request, spider):
        pass  # 按需添加逻辑

    async def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exc, spider):
        pass


class TestMiddleware2(BaseMiddleware):
    """示例：异常恢复"""

    def process_request(self, request, spider):
        pass

    def process_exception(self, request, exc, spider):
        pass
