import asyncio

from message.base import Messager


class SimpleMessager(Messager):
    """A simple messager used within application

    Returns:
        Messager: messager instance
    """
    __slots__ = ['_queue']

    def __init__(self, *args, **kwargs):
        self._queue = asyncio.Queue()
        super(SimpleMessager, self).__init__(*args, **kwargs)

    def setup(self):
        """initial object
        """
        super().setup()

    def cleanup(self):
        return super().cleanup()

    async def send(self, msg: str):
        """Add command handler to bot

        Args:
            msg (str): Message body
        """
        await self._queue.put(msg)

    async def start(self):
        self._running = True
        while self._running:
            msg = await self._queue.get()
            await self.onMessage(msg)

    def stop(self):
        self._running = False
