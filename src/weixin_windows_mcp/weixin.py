import inspect
import threading
from abc import abstractmethod, ABC
from enum import IntEnum, StrEnum
from urllib.parse import quote

import arrow
from pydantic import BaseModel


class ChatLogMessage(BaseModel):
    message: str


class TabBarItemType(StrEnum):
    CHAT = '微信'
    CONTACTS = '通讯录'
    FAVORITES = '收藏'
    MOMENTS = '朋友圈'
    MINI_PROGRAMS = '小程序面板'
    MOBILE = '手机'
    SETTINGS = '设置'


class ChatToolBarButtonType(StrEnum):
    EMOJI = '表情'
    SEND_FILE = '发送文件'
    HIDE_SCREENSHOT = '聊天时隐藏当前截图'
    CHAT_HISTORY = '聊天记录'


class SNSWindowToolBarItemType(StrEnum):
    MESSAGE = '消息'
    POST = '发表'
    REFRESH = '刷新'
    MINIMIZE = '最小化'
    CLOSE = '关闭'


class ChatMessageClassName(StrEnum):
    TEXT = 'mmui::ChatTextItemView'
    IMAGE = 'mmui::ChatBubbleItemView'
    VOICE = 'mmui::ChatVoiceItemView'
    SYSTEM = 'mmui::ChatItemView'


class MessageType(StrEnum):
    TEXT = 'text'
    IMAGE = 'image'
    VOICE = 'voice'
    VIDEO = 'video'
    SYSTEM = 'system'


class ChatMessagePageType(IntEnum):
    PERSON = 1
    GROUP = 2


class SearchType(IntEnum):
    ALL = 0
    ACCOUNT = 33554499
    VIDEO = 7
    ARTICLES = 2
    STICKERS = 384
    ENCYCLOPEDIA = 16777728
    LIVE_STREAM = 9
    IMAGE = 17825792
    BOOKS = 1024
    LISTEN = 512
    NEWS = 16384
    INQUIRIES = 16777728
    WEIXIN_INDEX = 8192
    MOMENTS = 8
    OFFICIAL_ACCOUNTS = 1
    MINI_PROGRAMS = 262208


class ContactsMasterSubTypeCellViewType(StrEnum):
    GROUP = '群聊'
    OFFICIAL_ACCOUNT = '公众号'
    SERVICE_ACCOUNT = '服务号'
    ENTERPRISE_CONTACT = '企业微信联系人'
    CONTACT = '联系人'


class Chat(ABC):

    def __init__(self):
        self.chat_type = None

    def send_msg(self, msg: str, at: str | list[str] = None, typing: bool = False):
        self._focus_input_field()
        if self.chat_type == ChatMessagePageType.GROUP and at:
            at_users = [at] if isinstance(at, str) else at
            for at_user in at_users:
                self._at(at_user)
        self._input_text(msg, typing)
        self._send_input()

    @abstractmethod
    def _focus_input_field(self):
        raise NotImplementedError()

    @abstractmethod
    def _at(self, at: str):
        raise NotImplementedError()

    @abstractmethod
    def _input_text(self, text, typing=False):
        pass

    @abstractmethod
    def _send_input(self):
        pass


class Weixin(ABC):

    def __init__(self):
        # 添加一个线程锁，用于确保同一时间只有一个自动化任务在执行
        self._automation_lock = threading.RLock()
        self._current_task = None
        self.current_chat = None
        self.chats = None

    def send_msg(self, msg: str, to: str = None, at: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False):
        if not msg and not at:
            return
        if not self.current_chat and not to:
            return
        self._show()
        if self.current_chat and self.current_chat.chat_name == to:
            current_chat = self.current_chat
        elif to in self.chats:
            current_chat = self.chats[to]
        else:
            current_chat = self._navigate_to_chat(to, exact_match)
        if not current_chat:
            return
        current_chat.send_msg(msg, at, typing)

    def send_file(self):
        # AutomationId	tool_bar_accessible
        pass

    def search_chat_history(self, to: str, query=None, from_date: str = None, to_date: str = None):
        self._show()
        self._navigate_to_chat(to)
        self._click_chat_tool_bar(ChatToolBarButtonType.CHAT_HISTORY)
        self._search_chat_history(query, from_date, to_date)

    def publish_moment(self, msg: str, images=None):
        if images and len(images) > 9:
            raise ValueError('朋友圈图片数量不能超过9张')
        self._open_moment()
        self._publish_moment(msg, images)

    @abstractmethod
    def _show(self):
        pass

    @abstractmethod
    def _click_chat_tool_bar(self, button_type: ChatToolBarButtonType):
        pass

    @abstractmethod
    def _search_chat_history(self, query: str = None, from_date: str = None, to_date: str = None) -> list[
        ChatLogMessage]:
        pass

    @abstractmethod
    def _open_moment(self):
        pass

    @abstractmethod
    def _publish_moment(self, msg, images):
        pass

    def search(self, query):
        self._search(query)

    @abstractmethod
    def _search(self, query: str):
        pass

    @abstractmethod
    def _navigate_to_chat(self, to: str, exact_match=False) -> Chat:
        raise NotImplementedError()

    def history_articles(self, account: str, limit: int = 1) -> list[dict]:
        self._show()
        search_url = self.get_search_url(account, search_type=SearchType.OFFICIAL_ACCOUNTS)
        self.search(search_url)
        return self._history_articles(limit)
        # search_pane = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1)
        # search_pane.GroupControl(AutomationId='search_result', Depth=6,
        #                          Compare=lambda control, _: control.BoundingRectangle.height() > 0)
        # search_result = self.search(search_url)
        # search_result.ButtonControl(Depth=5).Click()

    @abstractmethod
    def _history_articles(self, limit: int = 1) -> list[dict]:
        raise NotImplementedError()

    def call_with_lock(self, callback, task_name=None):
        if task_name is None:
            frame = inspect.currentframe().f_back
            task_name = inspect.getframeinfo(frame).function
        if not self._automation_lock.acquire(blocking=False):
            print(f"自动化任务 '{self._current_task}' 正在执行，无法执行 '{task_name}'")
            return None
        try:
            self._current_task = task_name
            print(f"开始执行自动化任务: {task_name}")
            result = callback()
            return result
        finally:
            self._current_task = None
            self._automation_lock.release()
            print(f"自动化任务完成: {task_name}")

    @property
    def is_busy(self):
        """检查是否有自动化任务正在执行"""
        return self._current_task is not None

    @property
    def current_task(self):
        """获取当前正在执行的任务名称"""
        return self._current_task

    @staticmethod
    def parse_chat_time(time_str):
        patterns = [
            "HH:mm"  # 没有前缀
            "星期一 HH:mm",  # 星期几
            "昨天 HH:mm",  # 昨天
            "M月D日 HH:mm",  # 具体月日
            "YYYY年M月D日 HH:mm",  # 具体年月日
        ]
        for pattern in patterns:
            try:
                return arrow.get(time_str, pattern)
            except arrow.parser.ParserError:
                continue
        return None

    # 示例使用
    @staticmethod
    def get_search_url(query: str, lang: str = 'zh_CN', search_type: SearchType = SearchType.ALL):
        return f'weixin://resourceid/Search/app.html?isHomePage=0&lang={lang}&scene=85&query={quote(query)}&type={search_type.value}'
