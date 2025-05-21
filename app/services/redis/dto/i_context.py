from abc import ABC, abstractmethod
from typing import Union


class IContext(ABC):

    @abstractmethod
    def get_dumps(self) -> dict[str, Union[str, bytes]]:
        """
        Get the dumps of the Redis context.
        Returns:
            dict[str, Union[str, bytes]]: The dumps of the Redis context.
        """
        pass

    @abstractmethod
    def get_keys(self) -> list[tuple[str, Union[type[str], type[bytes]]]]:
        """
        Get the keys of the Redis context.
        Returns:
            list[str, Union[type[str], type[bytes]]]: The keys of the Redis context.
        """
        pass

        @abstractmethod
        def append(self, key: str, value: Union[str, bytes]):
            """
            Append a value to the Redis context.
            Args:
                key (str): The key to append the value to.
                value (Union[str, bytes]): The value to append.
            """
            pass
