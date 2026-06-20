from bald_spider import Item
from bald_spider.items import Field


class BookItem(Item):
    """示例：图书数据模型"""
    title = Field()
    author = Field()
    url = Field()
