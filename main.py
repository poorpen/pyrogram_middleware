import asyncio
import functools

from typing import List, Callable

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.filters import private
from pyrogram.handlers import MessageHandler


class BaseMiddleware:

    async def __call__(self, handler, **data):
        raise NotImplementedError


class ParamsConverter:

    async def __call__(self, handler, *args, **kwargs):
        data = {'client': args[0],
                'message': args[1]}
        return await handler(**data)


class MiddlewaresManager:

    def __init__(self):
        self._middlewares: List[BaseMiddleware] = []

    def add_middlewares(self, middleware: BaseMiddleware):
        self._middlewares.append(middleware)

    def wrap_handler(self, handler: Callable, skip_middlewares):
        middleware = handler
        converter = ParamsConverter()
        for m in reversed(self._middlewares):
            if type(m) not in skip_middlewares:
                middleware = functools.partial(m.__call__, middleware)
        middleware = functools.partial(converter.__call__, middleware)
        return middleware


class PyroDispatcher:

    def __init__(self, client):
        self._mm = MiddlewaresManager()
        self.client: Client = client

    def register_middleware(self, middleware: BaseMiddleware):
        self._mm.add_middlewares(middleware)

    def register_handler(self, handler: Callable, filters=None, *skip_middlewares):
        wrapped_handler = self._mm.wrap_handler(handler, skip_middlewares)
        self.client.add_handler(MessageHandler(wrapped_handler, filters=filters))


# Middlewares

class FirstMiddlewares(BaseMiddleware):

    async def __call__(self, handler, **data):
        print(data)
        print(f"{self.__class__.__name__} - Первая тестовая мидлварь")
        return await handler(**data)


class SecondMiddlewares(BaseMiddleware):

    async def __call__(self, handler, **data):
        print(data)
        print(f"{self.__class__.__name__} - Вторая тестовая мидлварь")
        return await handler(**data)


# handler

async def test_handler(client: Client, message: Message):
    print('тестовый хендлер')
    await client.send_message(chat_id=message.from_user.id, text='Ответ')


async def main():
    client = Client("name", api_id=1, api_hash="hash")
    pyro_dispatcher = PyroDispatcher(client=client)

    # register middlewares
    pyro_dispatcher.register_middleware(FirstMiddlewares())
    pyro_dispatcher.register_middleware(SecondMiddlewares())

    # register handlers
    pyro_dispatcher.register_handler(test_handler, private)

    await client.start()


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
