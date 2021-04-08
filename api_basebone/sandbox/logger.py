import logging

class LogCollector(object):
    
    def __init__(self, name, logger_type="function"):
        self.messages = []
        self.name = name
        self.logger_type = logger_type
    
    @property
    def logger(self):
        if not getattr(self, '_logger', None):
            prefix = {
                'function': 'lightning_cloud_function',
                'trigger': 'lightning_trigger_script'
            }[self.logger_type]
            self._logger = logging.getLogger(f'{prefix}.{self.name}')
        return self._logger
    
    def log(self, level, message):
        level_func = {
            logging.DEBUG: self.logger.debug,
            logging.INFO: self.logger.info,
            logging.WARN: self.logger.warn,
            logging.ERROR: self.logger.error,
            logging.CRITICAL: self.logger.critical
        }
        self.messages.append((level, f'【Server-{self.logger_type}】{self.name}: {message}'))
        level_func[level](f'{self.name} {message}')

    def info(self, message):
        self.log(logging.INFO, message)

    def error(self, message):
        self.log(logging.ERROR, message)
    
    def warn(self, message):
        self.log(logging.WARN, message)
    
    def debug(self, message):
        self.log(logging.DEBUG, message)
    
    def critical(self, message):
        self.log(logging.CRITICAL, message)

    def collect(self):
        return self.messages