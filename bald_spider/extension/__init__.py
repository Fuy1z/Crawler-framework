from pprint import pformat
from typing import List

from bald_spider.execptions import ExtensionInitError
from bald_spider.utils.log import get_logger
from bald_spider.utils.project import load_class


class ExtensionManager:

    def __init__(self, crawler):
       self.crawler = crawler
       self.extensions: List = []
       extensions = self.crawler.settings.getlist('EXTENSIONS')
       self.logger = get_logger(self.__class__.__name__, crawler.settings.get('LOG_LEVEL'))
       self._add_extensions(extensions)



    @classmethod
    def create_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def _add_extensions(self, extensions):
        for extension in extensions:
            extension_class = load_class(extension)
            if not hasattr(extension_class, 'create_instance'):
                raise ExtensionInitError(f"extension init failed, Must have' 'create_instance' method")
            self.extensions.append(extension_class.create_instance(self.crawler))
        if extensions:
            self.logger.info(f"enabled extensions: \n {pformat(extensions)})")