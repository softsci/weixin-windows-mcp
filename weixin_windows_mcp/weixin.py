import random
import time
from enum import StrEnum, IntEnum
from typing import Callable, Any, Self
from urllib.parse import quote

import uiautomation as auto
from uiautomation import Control, WindowControl, GroupControl

from weixin_windows_mcp import utils

auto.uiautomation.DEBUG_SEARCH_TIME = True


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


class ChatMessagePage:

    def __init__(self, chat_name: str, chat_count: int | None = None, control: Control | None = None,
                 weixin_window: WindowControl | None = None):
        self.chat_name = chat_name
        self.chat_count = chat_count
        self.control = control
        self.weixin_window = weixin_window
        if chat_count is not None:
            self.chat_type = ChatMessagePageType.GROUP
        else:
            self.chat_type = ChatMessagePageType.PERSON
        self.type = type

    def send_msg(self, msg: str, at: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False) -> None:
        chat_input_field = self.control.EditControl(AutomationId='chat_input_field', Depth=6)
        chat_input_field.SetFocus()
        self._at(at)
        if typing:
            # 使用打字模式
            self.send_typing_text(msg)
        else:
            # 使用剪贴板模式
            auto.SetClipboardText(msg)
            chat_input_field.SendKeys('{Ctrl}v')
        chat_input_field.SendKeys('{Enter}')

    def send_typing_text(self, text: str, min_interval: float = 0.1, max_interval: float = 0.3) -> bool:
        edit_box = self.weixin_window.EditControl(Name='输入')
        if not edit_box.Exists(3):
            return False
        edit_box.Click(simulateMove=False)
        self.type_text(edit_box, text)
        return True

    def _at(self, at: str | list[str] = None):
        if self.chat_type == ChatMessagePageType.PERSON:
            return
        if at:
            at_users = [at] if isinstance(at, str) else at
            for at_user in at_users:
                auto.SendKeys('@' + at_user)
                chat_mention_list = self.weixin_window.PaneControl(AutomationId='chat_mention_list')
                if chat_mention_list.Exists(maxSearchSeconds=0.1):
                    chat_mention_list.SendKeys('{ENTER}')

    @classmethod
    def from_control(cls, chat_message_page_control: Control, weixin_window: WindowControl) -> Self:
        chat_info_view = chat_message_page_control.GroupControl(ClassName='mmui::ChatInfoView')
        chat_name_control = chat_info_view.TextControl(
            AutomationId='top_content_h_view.top_spacing_v_view.top_left_info_v_view.big_title_line_h_view.current_chat_name_label')
        chat_name = chat_name_control.Name
        chat_count_control = chat_info_view.TextControl(
            AutomationId='top_content_h_view.top_spacing_v_view.top_left_info_v_view.big_title_line_h_view.current_chat_count_label')
        chat_count = None
        if chat_count_control.Exists(maxSearchSeconds=0.1):
            count_text = chat_count_control.Name.strip('()')
            chat_count = int(count_text)

        return cls(
            chat_name=chat_name,
            chat_count=chat_count,
            control=chat_message_page_control,
            weixin_window=weixin_window
        )


class Weixin:
    IMAGE_X_OFFSET = 70
    IMAGE_Y_OFFSET = 30

    ARTICLE_TITLE_TEXT_WIDTH = 266
    ARTICLE_TITLE_TEXT_HEIGHT = 21

    def __init__(self):
        self._handlers = {}
        self.weixin_window = auto.WindowControl(ClassName='mmui::MainWindow', Depth=1)
        self.weixin_window.SetActive()
        self.tab_bar_items = {TabBarItemType(tab_bar.Name): tab_bar for tab_bar in
                              self.weixin_window.ToolBarControl(AutomationId='main_tabbar', Depth=4).GetChildren()}
        self.search_bar = self.weixin_window.EditControl(ClassName='mmui::XLineEdit', Depth=10)
        self.chats = {}
        self.sns_window = None
        self.sns_window_tool_bar_items = {}
        self.chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page')
        self.chat_message_list = self.chat_message_page.ListControl(AutomationId='chat_message_list')
        self.current_chat = None

    def send_msg(self, msg: str, to: str = None, at: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False) -> None:
        if not msg and not at:
            return
        if not self.current_chat and not to:
            return
        self._chat_to(to)
        self.current_chat.send_msg(msg, at, exact_match, typing)

    def _chat_to(self, to):
        if self.current_chat and self.current_chat.chat_name == to:
            return
        if auto.WindowControl(ClassName='mmui::FramelessMainWindow', Depth=1).GroupControl(
                AutomationId='chat_message_page').Exists(maxSearchSeconds=0.1):
            self.current_chat = ChatMessagePage.from_control(
                auto.WindowControl(Depth=1, ClassName='mmui::FramelessMainWindow')
                .GroupControl(AutomationId='chat_message_page'),
                self.weixin_window)
        elif to in self.chats:
            self.current_chat = self.chats[to]
        else:
            print(to)
            self.search(to).Click()
            self.current_chat = ChatMessagePage.from_control(
                self.weixin_window.GroupControl(AutomationId='chat_message_page'), self.weixin_window)

    def search(self, query: str) -> GroupControl:
        self.tab_bar_items[TabBarItemType.MINI_PROGRAMS].Click()
        search_pane = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1)
        search_pane.PaneControl(Depth=6,
                                Compare=lambda control, _: control.BoundingRectangle.width() == 32
                                                           and control.BoundingRectangle.height() == 32).Click()
        search_pane.EditControl(Depth=7).Click()
        search_bar = search_pane.EditControl(Depth=7)
        auto.SetClipboardText(query)
        search_bar.SendKeys('{Ctrl}v')
        search_bar.SendKeys('{Enter}')
        # when search finish, document control has name
        search_pane.DocumentControl(Name='', ClassName='Chrome_RenderWidgetHostHWND', Depth=1).Disappears()
        return search_pane.GroupControl(AutomationId='search_result', Depth=6,
                                        Compare=lambda control, _: control.BoundingRectangle.height() > 0)

    @staticmethod
    def type_text(control: Control, text, min_interval: float = 0.1, max_interval: float = 0.3):
        for char in text:
            control.SendKeys(char, waitTime=0)
            # 随机等待时间，模拟真实输入
            time.sleep(random.uniform(min_interval, max_interval))

    def history_articles(self, account):
        search_url = self.get_search_url(account, search_type=SearchType.OFFICIAL_ACCOUNTS)
        search_result = self.search(search_url)
        search_result.ButtonControl(Depth=5).Click()
        official_account_pane = auto.PaneControl(Name='公众号', ClassName='Chrome_WidgetWin_0', Depth=1)
        history_articles = []
        skip_group = False
        for child in official_account_pane.GroupControl(
                Depth=5).GetLastChildControl().GetLastChildControl().GetChildren():
            utils.print_control_tree(child)
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
                        article_stats = child.TextControl(Depth=3).Name.replace('\u2004', ' ').replace('\u2005', ' ').replace('\u2006', ' ')
                        history_articles.append((article_title, article_stats))
        return history_articles

    def get_contact_dict(self) -> dict[str, list]:
        contact_list = self.weixin_window.ListControl(AutomationId='contact_list', Depth=7)
        contact_list.Click()
        contact_dict = {}
        current_type = None
        for item in contact_list.GetChildren():
            print(item)

            match item.ClassName:
                case 'mmui::ContactsMasterSubTypeCellView':
                    if current_type:
                        contact_dict[current_type] = []
                    current_type = ContactsMasterSubTypeCellViewType(item.Name)
                case 'mmui::ContactsMasterCellView':
                    contact_dict[current_type].append(item.Name)
        return contact_dict

    def on(self, message_type: MessageType):
        """装饰器方法"""

        def decorator(handler):
            if message_type not in self._handlers:
                self._handlers[message_type] = []
            self._handlers[message_type].append(handler)
            return handler

        return decorator

    def add_message_handler(self, message_type: MessageType, handler: Callable[..., Any]) -> Self:
        """直接注册方法"""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        return self

    def get_msg(self):
        for chat_message in self.chat_message_list.GetChildren():
            self.handle_chat_message(chat_message)

    def handle_chat_message(self, chat_message):
        for handler in self._handlers['message']:
            handler(chat_message)

        message_type = ChatMessageClassName(chat_message.ClassName)
        event_type = message_type.name.lower()
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(chat_message)

    def click_media(self, media: Control):
        utils.ensure_visible(media)
        media.Click(x=self.IMAGE_X_OFFSET, y=self.IMAGE_Y_OFFSET, simulateMove=False)

    def publish(self, msg: str, images=None):
        """
        mmui::PublishImageAddGridCell发布后变为mmui::PublishImageGridCell
        """
        if images and len(images) > 9:
            raise ValueError('朋友圈图片数量不能超过9张')
        self.tab_bar_items[TabBarItemType.MOMENTS].Click(simulateMove=False)
        self.sns_window = auto.WindowControl(ClassName='mmui::SNSWindow', Depth=1)
        self.sns_window.SetActive()
        self.sns_window_tool_bar_items = {SNSWindowToolBarItemType(tool_bar_item.Name): tool_bar_item for tool_bar_item
                                          in self.sns_window.ToolBarControl(AutomationId='sns_window_tool_bar',
                                                                            Depth=3).GetChildren()}
        self.sns_window_tool_bar_items[SNSWindowToolBarItemType.POST].Click()
        sns_publish_pane = self.sns_window.GroupControl(AutomationId='SnsPublishpane', Depth=4)
        if msg:
            reply_input_field = sns_publish_pane.EditControl(ClassName='mmui::ReplyInputField', Depth=8)
            reply_input_field.SendKeys('{Ctrl}a{Del}')
            reply_input_field.SendKeys(msg)
        if images:
            x_drag_grid_view = sns_publish_pane.ListControl(ClassName='mmui::XDragGridView')
            for image in images:
                x_drag_grid_view.ListItemControl(ClassName='mmui::PublishImageAddGridCell').Click()
                utils.choose_file(self.sns_window.WindowControl(Name='打开'), image)
            x_drag_grid_view.ListItemControl(ClassName='mmui::PublishImageGridCell', Depth=1).GetChildren()
            utils.print_control_tree(self.sns_window)
        sns_publish_pane.ButtonControl(ClassName='mmui::XOutlineButton', Name='发表').Click()

    def get_chat_dict(self, max_chats: int = 100) -> dict[str, Control]:
        chat_list = self.weixin_window.ListControl(AutomationId='session_list')
        chat_dict = dict()
        for chat in chat_list.GetChildren():
            utils.ensure_visible(chat)
            chat.Click(simulateMove=False)
            chat_name = self.weixin_window.GroupControl(ClassName='mmui::ChatInfoView').TextControl(
                AutomationId='top_content_h_view.top_spacing_v_view.top_left_info_v_view.big_title_line_h_view.current_chat_name_label').Name
            chat_dict[chat_name] = chat
        return chat_dict

    def click_moments(self):
        if not self.weixin_window:
            return False

        moments_button = self.weixin_window.ButtonControl(Name='朋友圈', Depth=5)
        if moments_button.Exists():
            moments_button.Click()
            print('已点击朋友圈按钮')
            time.sleep(2)
            return True
        print('朋友圈按钮未找到')
        return False

    def scroll_and_parse_moments(self, scroll_times=5):
        if not self.weixin_window:
            return []

        moments_scroll = self.weixin_window.PaneControl(AutomationId='moments_scroll', Depth=5)
        if not moments_scroll.Exists():
            print('朋友圈滚动区域未找到')
            return []

        posts_content = []
        for _ in range(scroll_times):
            posts = moments_scroll.GetChildren()
            for post in posts:
                text_controls = post.GetChildren()
                for text_control in text_controls:
                    if isinstance(text_control, auto.TextControl):
                        posts_content.append(text_control.Name)

            moments_scroll.Swipe(auto.SwipeDirection.Up, 1, 1)
            time.sleep(1)

        return posts_content

    def search_official_account(self, account_name):
        if not self.weixin_window:
            return False

        search_edit = self.weixin_window.EditControl(
            ControlType=auto.EditControl.ControlType,
            Name=''
        )

        if search_edit.Exists(3):
            search_edit.Click()
            search_edit.SendKeys(account_name)
            time.sleep(1)
            search_edit.SendKeys('{Enter}')
            return True

        print('未找到搜索框')
        return False

    def init_search(self):
        if not self.weixin_window:
            return False
        self.search_bar.Click(simulateMove=False)
        self.weixin_window.ListItemControl(Name='搜索网络结果').Click(simulateMove=False)
        self.weixin_window.DocumentControl(Name='搜一搜')
        self.weixin_window.EditControl().SendKeys('')

    @staticmethod
    def get_search_url(query: str, lang: str = 'zh_CN', search_type: SearchType = SearchType.ALL):
        return f'weixin://resourceid/Search/app.html?isHomePage=0&lang={lang}&scene=85&query={quote(query)}&type={search_type.value}'
