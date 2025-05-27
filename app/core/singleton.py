from abc import ABC
from functools import wraps
from typing import Any, Callable, Type, TypeVar, cast
from util.util import camel_to_snake

T = TypeVar("T", bound="Singleton")


class Singleton(ABC):
    implementation: "Singleton" = None

    def __init__(self) -> None:
        cls = self.__class__
        if cls.implementation is not None:
            raise Exception(
                f"{self.__class__.__name__} is a singleton class. Use ServerObject.get_instance() instead."
            )

        cls.implementation = self

    @classmethod
    def get_instance(cls: Type[T], *args, **kwargs) -> T:
        if cls.implementation is None:
            cls(*args, **kwargs)
        return cast(T, cls.implementation)

    @classmethod
    def object(cls, func: Any, alias: str = None) -> Callable[..., Any]:
        def decorator(func: Any):
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                self = cls.get_instance()
                kwargs[alias or camel_to_snake(self.__class__.__name__)] = self
                return func(*args, **kwargs)

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)
