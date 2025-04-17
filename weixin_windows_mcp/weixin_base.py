from abc import ABC, abstractmethod


class Weixin(ABC):

    @abstractmethod
    def send_msg(self, msg: str, to: str = None, at: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False):
        raise NotImplementedError()
