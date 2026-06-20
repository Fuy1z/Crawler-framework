import json

from bald_spider import Spider, Request
from bald_spider.utils.log import get_logger
from bald_test.items import WinshangItem


class WinshangSpider(Spider):
    """赢商网项目数据采集"""

    LIST_API = "http://www.winshangdata.com/wsapi/project/getBigdataList3_5"
    DETAIL_API = "http://www.winshangdata.com/wsapi/project/getBigdataDetailZhaoShangXuQiu"
    CONTENT_API = "http://www.winshangdata.com/wsapi/project/detailContent"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "http://www.winshangdata.com",
        "Pragma": "no-cache",
        "Referer": "http://www.winshangdata.com/projectList",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
        ),
        "appType": "bigdata",
        "platform": "pc",
        "pwd": "mobile_regist",
        "uid": "ws305258853",
        "uuid": "123456",
    }


    max_page = 2  # 测试：只采前 2 页，约 120 条

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # 入口
    # ------------------------------------------------------------------

    def start_requests(self):
        """初始请求：列表第一页"""
        yield Request(
            url=self.LIST_API,
            method="POST",
            body=json.dumps(self._list_payload(page=1)),
            headers=self.headers,
            dont_filter=True,
            meta={"page": 1},
        )

    # ------------------------------------------------------------------
    # 列表页 → 翻页 + 分发详情请求
    # ------------------------------------------------------------------

    def parse(self, response):
        page = response.meta["page"]
        self.logger.info(f"列表第 {page} 页")

        if page < self.max_page:
            yield from self._next_list_request(response, page)

        data = response.json()
        for item in data.get("data", {}).get("list", []):
            project_id = item.get("projectId")
            if not project_id:
                continue
            yield Request(
                url=self.DETAIL_API,
                callback=self.parse_detail,
                method="POST",
                body=json.dumps({"projectId": project_id}),
                headers=self.headers,
                meta={"project_id": project_id},
            )

    def _next_list_request(self, response, current_page):
        """生成下一页列表请求"""
        next_page = current_page + 1
        payload = json.loads(response.request.body)
        payload["pageNum"] = next_page
        yield Request(
            url=response.request.url,
            method="POST",
            body=json.dumps(payload),
            headers=self.headers,
            callback=self.parse,
            meta={"page": next_page},
        )

    # ------------------------------------------------------------------
    # 详情 → 内容（二跳合并）
    # ------------------------------------------------------------------

    def parse_detail(self, response):
        data1 = response.json()
        project_id = response.meta["project_id"]
        yield Request(
            url=self.CONTENT_API,
            callback=self.parse_content,
            method="POST",
            body=json.dumps({"projectId": project_id}),
            headers=self.headers,
            meta={"detail_data": data1},
        )

    def parse_content(self, response):
        detail = (response.meta["detail_data"].get("data") or {})
        content = (response.json().get("data") or {})

        is_unopened = detail.get("xmZhuangTaiName") == "未开业"

        yield WinshangItem(
            project_name=detail.get("projectName", ""),
            project_status=detail.get("xmZhuangTaiName", ""),
            zhaoshang_status="正在招商" if is_unopened else "暂无",
            project_highlight=detail.get("xmLiangDian", ""),
            project_type=detail.get("wuyelx", ""),
            business_area=detail.get("shangYeMianjiRange", ""),
            developer=content.get("kaiFaShang", ""),
            province=detail.get("projectProvinceName", ""),
            address=(detail.get("projectAreaName") or "") + (detail.get("address") or ""),
            project_intro=content.get("projectJieShao", ""),
        )

    @staticmethod
    def _list_payload(page=1, page_size=60):
        return {
            "pageNum": page,
            "orderBy": "1",
            "pageSize": page_size,
            "zsxq_yt1": "",
            "zsxq_yt2": "",
            "qy_p": "",
            "qy_c": "",
            "qy_a": "",
            "xmzt": "",
            "key": "",
            "wuyelx": "",
            "isHaveLink": "",
            "ifdporyt": "",
        }
