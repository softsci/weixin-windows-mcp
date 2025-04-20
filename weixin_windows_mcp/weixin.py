import inspect
import threading
from abc import abstractmethod, ABC
from enum import IntEnum, StrEnum, auto
from urllib.parse import quote


class TabBarItemType(StrEnum):
    CHAT = '微信'
    CONTACTS = '通讯录'
    FAVORITES = '收藏'
    MOMENTS = '朋友圈'
    MINI_PROGRAMS = '小程序面板'
    MOBILE = '手机'
    SETTINGS = '设置'


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

    def publish_moment(self, msg: str, images=None):
        if images and len(images) > 9:
            raise ValueError('朋友圈图片数量不能超过9张')
        self._open_moment()
        self._publish_moment(msg, images)

    @abstractmethod
    def _open_moment(self):
        pass

    @abstractmethod
    def _publish_moment(self, msg, images):
        pass

    @abstractmethod
    def _show(self):
        pass

    def search(self, query):
        self._search(query)

    @abstractmethod
    def _search(self, query: str):
        pass

    @abstractmethod
    def _navigate_to_chat(self, to: str, exact_match=False) -> Chat:
        raise NotImplementedError()

    def history_articles(self, account: str, limit: int) -> list[dict]:
        self.show()
        search_url = self.get_search_url(account, search_type=SearchType.OFFICIAL_ACCOUNTS)
        search_result = self.search(search_url)
        search_result.ButtonControl(Depth=5).Click()
        official_account_pane = auto.PaneControl(Name='公众号', ClassName='Chrome_WidgetWin_0', Depth=1)
        skip_group = False
        official_account_pane.HyperlinkControl(Name='消息').Exists()
        history_articles = []
        for child in official_account_pane.GroupControl(
                Depth=5).GetLastChildControl().GetLastChildControl().GetChildren():
            if child.IsOffscreen:
                break
            match type(child):
                case auto.TextControl:
                    if child.TextControl(Depth=1).Name == '作者精选':
                        skip_group = True
                    else:
                        skip_group = False
                case auto.GroupControl:
                    if skip_group:
                        continue
                    else:
                        article_title = child.TextControl(Depth=2).Name
                        article_stats = (child.TextControl(Depth=3).Name.replace('\u2004', ' ')
                                         .replace('\u2005', ' ')
                                         .replace('\u2006', ' '))
                        child.Click()
                        search_pane = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1)
                        # 存在跟踪信息，可能被封禁，备用
                        # article_url = search_pane.DocumentControl(Name=article_title,
                        #                                           ClassName='Chrome_RenderWidgetHostHWND',
                        #                                           Depth=1).GetValuePattern().Value
                        more_button = search_pane.MenuItemControl(Name='更多', Depth=5)
                        close_button = more_button.GetParentControl().GetParentControl().ButtonControl(Name='关闭')
                        more_button.Click()
                        search_pane.MenuItemControl(Name='复制链接', Depth=6).Click()
                        close_button.Click()
                        article_url = auto.GetClipboardText()
                        history_articles.append({
                            'title': article_title,
                            'stats': article_stats,
                            'url': article_url
                        })
                        if len(history_articles) >= limit:
                            return history_articles
        return history_articles

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
    def get_search_url(query: str, lang: str = 'zh_CN', search_type: SearchType = SearchType.ALL):
        return f'weixin://resourceid/Search/app.html?isHomePage=0&lang={lang}&scene=85&query={quote(query)}&type={search_type.value}'
