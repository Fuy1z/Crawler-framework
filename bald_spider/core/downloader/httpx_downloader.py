from typing import Optional
import httpx


from bald_spider import Response
from bald_spider.core.downloader import DownloaderBase


class HTTPXDownloader(DownloaderBase):

    def __init__(self, crawler):
        super().__init__(crawler)

        self._client: Optional[httpx.AsyncClient] = None
        self._timeout: Optional[httpx.Timeout] = None
        self._use_session: Optional[bool] = None


    def open(self):
        super().open()
        request_timeout = self.crawler.settings.getint('REQUEST_TIMEOUT')
        self._timeout = httpx.Timeout(timeout=request_timeout)
        self._use_session = self.crawler.settings.getbool('USE_SESSION')
        if self._use_session:
            self._client = httpx.AsyncClient(timeout=self._timeout)


    async def download(self, request) -> Optional[Response]:
        try:
            if self._use_session and self._client is not None:
                self.logger.debug(f"request downloading: {request.url}, method: {request.method}")
                response = await self._client.request(
                    request.method, request.url, headers=request.headers,
                    cookies=request.cookies, data=request.body
                )
                body = await response.aread()
            else:
                proxy = request.proxy
                async with httpx.AsyncClient(timeout=self._timeout, proxy=proxy) as client:
                    self.logger.debug(f"request downloading: {request.url}, method: {request.method}")
                    response = await client.request(
                        request.method, request.url, headers=request.headers,
                        cookies=request.cookies, data=request.body
                    )
                    body = await response.aread()
        except Exception as exc:
            self.logger.error(f"Error occurred during the request: {exc}")
            # return None
            raise exc
        return self.structure_response(request, response, body)

    @staticmethod
    def structure_response(request, response, body) -> Response:
            return Response(
                url=str(response.url),
                headers=dict(response.headers),
                status=response.status_code,
                body=body,
                request=request
            )

    async def close(self):
        if self._client:
            await self._client.aclose()



