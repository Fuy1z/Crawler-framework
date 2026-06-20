from bald_spider import Item


class BasePipeline:
    def process_item(self, item: Item, spider) -> None:
        raise NotImplementedError

    @classmethod
    def create_instance(cls, crawler):
        return cls()

