from abc import abstractmethod
from utils.base import LoggingBase
from typing import List, Callable, Awaitable

Consumer = Callable[[str], Awaitable[None]]

class Messager(LoggingBase):
    """Messager Base class with logger.
    """
    __slots__ = [
        '_consumers'
    ]

    def __init__(self, *args, **kwargs):
        self._consumers: List[Consumer] = []
        super(Messager, self).__init__(*args, **kwargs)

    @abstractmethod
    async def send(self, msg: str):
        """Add command handler to bot

        Args:
            msg (str): Message body
        """
        pass
    
    def addConsumer(self, callback: Consumer):
        """Add message callback to bot

        Args:
            callback (Callable[[str], None]): Async Message Handler
        """
        self._consumers.append(callback)

    async def onMessage(self, msg: str):
        """Messager should call this function when a message received

        Args:
            msg (str): Message body
        """
        for c in self._consumers[:]:
            await c(msg)
