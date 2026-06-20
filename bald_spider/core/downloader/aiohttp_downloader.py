from typing import  Optional
import aiohttp
from aiohttp import ClientSession, TCPConnector, BaseConnector, ClientTimeout, ClientResponse, TraceConfig
from bald_spider.core.downloader import DownloaderBase

from bald_spider import Response
from bald_spider.utils.log import get_logger


class AioDownloader(DownloaderBase):

    def __init__(self, crawler):
        super().__init__(crawler)
        self.session: Optional[ClientSession] = None
        self.connector: Optional[BaseConnector] = None
        self._verify_ssl: Optional[bool] = None
        self._timeout: Optional[ClientTimeout] = None
        self._use_session: Optional[bool] = None
        self.trace_config: Optional[TraceConfig] = None

        self.logger = get_logger(self.__class__.__name__,crawler.settings.get('LOG_LEVEL'))
        self.request_method = {
            'get': self._get,
            'post': self._post
        }

    def open(self):
        super().open()
        request_timeout = self.crawler.settings.getint('REQUEST_TIMEOUT')
        self._timeout = ClientTimeout(request_timeout)
        self._verify_ssl = self.crawler.settings.getbool('VERIFY_SSL')
        self._use_session = self.crawler.settings.getbool('USE_SESSION')
        self.trace_config = TraceConfig()
        self.trace_config.on_request_start.append(self.request_start)
        if self._use_session:
            self.connector = TCPConnector(verify_ssl=self._verify_ssl)
            self.session = ClientSession(connector=self.connector, timeout=self._timeout, trace_configs=[self.trace_config])



    async def download(self,request) -> Optional[Response]:
        try:
            if self._use_session:
                response = await self.send_request(self.session, request)
                body = await response.content.read()
            else:
                connector = TCPConnector(verify_ssl=self._verify_ssl)
                async with aiohttp.ClientSession(
                        connector=connector, timeout=self._timeout, trace_configs=[self.trace_config]
                ) as session:
                    response = await self.send_request(session, request)
                    body = await response.content.read()

        except Exception as exc:
            self.logger.error(f"Error occurred during the request: {exc}")
            # return None
            raise exc
        return self.structure_response(request, response, body)

    @staticmethod
    def structure_response(request, response, body):
        return Response(
            url = str(response.url),
            headers = dict(response.headers),
            status = response.status,
            body = body,
            request = request
        )

    async def send_request(self, session, request) -> ClientResponse:
        return await self.request_method[request.method.lower()](session, request)

    @staticmethod
    async def _get(session, request) -> ClientResponse:
        response = await session.get(
            request.url, headers=request.headers, cookies=request.cookies, proxy=request.proxy
        )
        return response

    @staticmethod
    async def _post(session, request) -> ClientResponse:
        response = await session.post(
            request.url, data=request.body, headers=request.headers, cookies=request.cookies, proxy=request.proxy
        )
        return response

    async def request_start(self, _session, _trace_config_ctx, params):
        self.logger.debug(f"request downloading: {params.url}, method: {params.method}")


    async def close(self):
        if self.session:
            await self.session.close()
        if self.connector and not self.connector.closed:
            await self.connector.close()


