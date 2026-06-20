from bald_spider import Item
from bald_spider.items import Field


class WinshangItem(Item):
    project_name = Field()
    project_status = Field()
    zhaoshang_status = Field()
    project_highlight = Field()
    project_type = Field()
    business_area = Field()
    developer = Field()
    province = Field()
    address = Field()
    project_intro = Field()
