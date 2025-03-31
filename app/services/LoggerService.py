import logging
from typing import Any, Callable, cast
from rich.logging import RichHandler

from ServerObject import ServerObject
from util.util import camel_to_snake

class LoggerService(ServerObject):
  def __init__(self, level: int = logging.DEBUG):
    super().__init__()
    self.__logger = logging.getLogger("SilRok")
    self.__logger.setLevel(level)

    # console_handler = logging.StreamHandler()
    # formatter = logging.Formatter("[%(asctime)s](%(levelname)s) - %(name)s:  %(message)s")
    # console_handler.setFormatter(formatter)
    self.__logger.addHandler(RichHandler())
    self.__logger.propagate = False

  @classmethod
  def object(cls, func:Any) -> Callable[..., Any]:
    def wrapper(*args, **kwargs) -> Any:
      self = cast(LoggerService, cls.get_instance())
      kwargs[camel_to_snake(self.__class__.__name__)] = self.__logger
      return func(*args, **kwargs)
    return wrapper