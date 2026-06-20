from logging import Formatter, StreamHandler, INFO, Logger
BASIC_FORMAT = F"%(asctime)s [%(name)s] %(levelname)s: %(message)s"

class LoggerManager:

    logger = {}

    @classmethod
    def get_logger(cls,name: str = "default",log_level=None,log_format=BASIC_FORMAT):
        key = (name,log_level)

        def gen_logger():
            logger_formatter = Formatter(log_format)
            handler = StreamHandler()
            handler.setFormatter(logger_formatter)
            handler.setLevel(log_level or INFO)
            _logger = Logger(name)
            _logger.addHandler(handler)
            _logger.setLevel(log_level or INFO)
            cls.logger[key] = _logger
            return _logger
        return cls.logger.get(key,None) or gen_logger()

get_logger = LoggerManager.get_logger

