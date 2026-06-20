from bald_spider import Request, Response


class BaseMiddleware:


    def process_request(self, request, spider) -> None | Request | Response:
        pass

    def process_response(self, request, response, spider) -> Request | Response:
        pass

    def process_exception(self, request, exc, spider) -> None | Request | Response | bool:
        """
          :return:
          - None: 不处理，继续交给后续异常中间件
          - True: 异常已处理，停止异常链，当前请求无产出
          - Request: 异常已处理，重新调度该请求
          - Response: 异常已处理，返回响应继续后续流程
          """
        pass

    @classmethod
    def create_instance(cls, crawler):
        return cls()