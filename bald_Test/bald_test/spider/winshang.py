import json
from scrapy import Request
from scrapy_redis.spiders import RedisSpider

class WinshangSpider(RedisSpider):
    name = "winshang"
    allowed_domains = ["winshangdata.com"]
    redis_key = "winshang:start_urls"

    # 公用的 headers（所有请求都用同一套）
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "http://www.winshangdata.com",
        "Pragma": "no-cache",
        "Referer": "http://www.winshangdata.com/projectList",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
        "appType": "bigdata",
        "platform": "pc",
        "pwd": "mobile_regist",
        "uid": "ws305258853",
        "uuid": "123456"
    }

    def make_request_from_data(self, data): # type:ignore
        """
        从 Redis 取出的 data 解析出 url 和请求参数

        """
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        try:
            task = json.loads(data)
        except:
            task = {}
        if task.get("url") or data == "http://www.winshangdata.com/wsapi/project/getBigdataList3_5":
            url = task.get("url", "http://www.winshangdata.com/wsapi/project/getBigdataList3_5")
            # 从 Redis 取出 data 解析出 body ,如果没有就用默认值
            payload = task.get('body',{
                "pageNum": 1,
                "orderBy": "1",
                "pageSize": 60,
                "zsxq_yt1": "",
                "zsxq_yt2": "",
                "qy_p": "",
                "qy_c": "",
                "qy_a": "",
                "xmzt": "",
                "key": "",
                "wuyelx": "",
                "isHaveLink": "",
                "ifdporyt": ""
            })


            return Request(
                url=url,
                method="POST",
                body=json.dumps(payload),
                headers=self.headers,
                dont_filter=True,
                meta={"page": task.get("pageNum", 1)}

            )
        elif task.get("url") == "http://www.winshangdata.com/wsapi/project/getBigdataDetailZhaoShangXuQiu":
            url = task.get("url", "http://www.winshangdata.com/wsapi/project/getBigdataDetailZhaoShangXuQiu")

            payload = task.get('body',{})


            return Request(
                url=url,
                callback=self.parse_zhaoshang,
                method="POST",
                body=json.dumps(payload),
                headers=self.headers,
                dont_filter=True,
                meta=task.get('meta', {})
            )
        elif task.get("url") == "http://www.winshangdata.com/wsapi/project/detailContent":
            url = "http://www.winshangdata.com/wsapi/project/detailContent"
            payload = task.get('body', {})
            return Request(
                url=url,
                callback=self.parse_detail_merge,   
                method="POST",
                body=json.dumps(payload),
                headers=self.headers,
                dont_filter=True,
                meta=task.get('meta', {})
            )

    def parse(self, response):
        page = response.meta["page"]
        print(f"正在处理第 {page} 页")

        # 解析数据...

        if page < 107:
            next_page = page + 1
            # 构造下一页请求（URL 从当前请求里拿，保持一致）
            url = response.request.url
            payload = json.loads(response.request.body)  # 复制当前请求的 body
            payload["pageNum"] = next_page

            yield Request(
                url=url,
                method="POST",
                body=json.dumps(payload),
                headers=self.headers,
                callback=self.parse,
                meta={"page": next_page},
                dont_filter=True
            )
            projectIds = response.json()
            for item in projectIds['data']['list']:
                projectId_json = {'projectId':item.get('projectId')}
                yield Request(
                    url="http://www.winshangdata.com/wsapi/project/getBigdataDetailZhaoShangXuQiu",
                    callback=self.parse_zhaoshang,
                    body=json.dumps(projectId_json),
                    headers=self.headers,
                    dont_filter=True,
                    method="POST",
                    meta={"projectId": item.get('projectId')}  # 将 projectId 传递给 parse_zhaoshang
                )

    def parse_zhaoshang(self, response):
        data1 = response.json()
        projectId = response.meta['projectId']
        # 发第二个请求，将第一个数据带过去
        yield Request(
            url="http://www.winshangdata.com/wsapi/project/detailContent",
            callback=self.parse_detail_merge,
            body=json.dumps({"projectId": projectId}),
            headers=self.headers,
            dont_filter=True,
            method="POST",
            meta={ "zhaoshang_data": data1}  # 携带第一个请求的数据 交给 parse_detail_merge
        )

    def parse_detail_merge(self, response):
        # 拿到2个请求的数据 进行数据合并 存储
        data2 = response.json()
        data1 = response.meta['zhaoshang_data']


        d1 = data1.get('data', {}) or {}
        d2 = data2.get('data', {}) or {}


        xmZhuangTaiName    = d1.get('xmZhuangTaiName', '')
        projectName        = d1.get('projectName', '')
        xmLiangDian        = d1.get('xmLiangDian', '')
        wuYeLx             = d1.get('wuyelx', '')          
        shangYeMianjiRange = d1.get('shangYeMianjiRange', '')
        projectProvinceName = d1.get('projectProvinceName', '')

        address = (d1.get('projectAreaName', '') or '') + (d1.get('address', '') or '')

        kaiFaShang    = d2.get('kaiFaShang', '')
        projectJieShao = d2.get('projectJieShao', '')
        Zhaoshang = '暂无'
        if xmZhuangTaiName == '未开业':
            Zhaoshang = '正在招商'
        merged = {
            "项目名称": projectName,
            "项目状态": xmZhuangTaiName,
            "招商状态": Zhaoshang,
            "项目亮点": xmLiangDian,
            "项目类型": wuYeLx,
            "商业面积": shangYeMianjiRange,
            "开发商": kaiFaShang,
            "省份": projectProvinceName,
            "地址": address,
            "项目介绍": projectJieShao
        }
        yield merged