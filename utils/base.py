from abc import abstractmethod
import logging

from utils.metabase import MetaBase

class LoggingBase(metaclass=MetaBase):
    """Base class with logger.
    """

    @property
    def log(self) -> logging.Logger:
        """
        A logger using the class name as name
        """
        return self.__log

    def __init__(self, *args, **kwargs):
        super(LoggingBase, self).__init__()
        self.setup(*args, **kwargs)

    def __del__(self):
        self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


    @abstractmethod
    def setup(self, *args, **kwargs):
        """initial object
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """cleanup object
        """
        pass
