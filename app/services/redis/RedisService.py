from ServerObject import ServerObject
from core import RedisByteManager, RedisStrManager

from .dto import IRedisContext


class RedisService(ServerObject):

    @RedisByteManager.object
    @RedisStrManager.object
    def __init__(
        self,
        redis_byte_manager: RedisByteManager,
        redis_str_manager: RedisStrManager,
    ) -> None:
        super().__init__()

        self.redis_byte_manager = redis_byte_manager
        self.redis_str_manager = redis_str_manager

    async def __save(
        self, context: IRedisContext, b_setter: callable, s_setter: callable
    ):
        dumps = context.get_dumps()
        for key, dump in dumps.items():
            if not dump:
                continue
            if isinstance(dump, bytes):
                await b_setter(key, dump)
            elif isinstance(dump, str):
                await s_setter(key, dump)
            else:
                raise TypeError(f"Unsupported type: {type(dump)}")

    # TODO 오디오 데이터는 추후 병렬처리와 효율성을 위해 shared memory로 변경 필요
    async def __load(
        self, context: IRedisContext, b_getter: callable, s_getter: callable
    ):
        for key, typ in context.get_keys():
            if typ is bytes:
                context.append(key, await b_getter(key))
            elif typ is str:
                context.append(key, await s_getter(key))
            else:
                raise TypeError(f"Unsupported type: {typ}")

    async def save(self, context: IRedisContext):
        await self.__save(
            context, self.redis_byte_manager.set, self.redis_str_manager.set
        )

    async def load(self, context: IRedisContext):
        await self.__load(
            context, self.redis_byte_manager.pop, self.redis_str_manager.pop
        )

    async def append(self, context: IRedisContext):
        await self.__save(
            context,
            self.redis_byte_manager.append_list,
            self.redis_str_manager.append_list,
        )

    async def pop(self, context: IRedisContext):
        await self.__load(
            context, self.redis_byte_manager.pop_list, self.redis_str_manager.pop_list
        )
