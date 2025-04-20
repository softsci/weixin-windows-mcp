import random
import time
from typing import Callable, Any, Self
from urllib.parse import quote

import uiautomation as auto
import win32gui
from uiautomation import Control, WindowControl

from weixin_windows_mcp import utils
from weixin_windows_mcp.weixin import Weixin, TabBarItemType, SearchType, ContactsMasterSubTypeCellViewType, \
    MessageType, ChatMessageClassName, SNSWindowToolBarItemType, ChatMessagePageType, Chat

auto.uiautomation.DEBUG_SEARCH_TIME = True


class WindowsChat(Chat):

    def __init__(self, chat_name: str, chat_count: int | None = None, control: Control | None = None,
                 weixin_window: WindowControl | None = None):
        super().__init__()
        self.chat_name = chat_name
        self.chat_count = chat_count
        self.control = control
        self.weixin_window = weixin_window
        if chat_count is not None:
            self.chat_type = ChatMessagePageType.GROUP
        else:
            self.chat_type = ChatMessagePageType.PERSON
        self.type = type

    def _focus_input_field(self):
        chat_input_field = self.control.EditControl(AutomationId='chat_input_field', Depth=5)
        chat_input_field.SetFocus()

    def _at(self, at: str):
        auto.SendKeys('@' + at)
        chat_mention_list = self.weixin_window.PaneControl(AutomationId='chat_mention_list')
        if chat_mention_list.Exists(maxSearchSeconds=0.1):
            chat_mention_list.SendKeys('{ENTER}')

    def _input_text(self, text, typing=False):
        if typing:
            for char in text:
                auto.SendKeys(char, waitTime=0)
                # 随机等待时间，模拟真实输入
                time.sleep(random.uniform(0.1, 0.3))
        else:
            # 使用剪贴板模式
            auto.SetClipboardText(text)
            auto.SendKeys('{Ctrl}v')

    def _send_input(self):
        auto.SendKeys('{ENTER}')

    @classmethod
    def from_control(cls, chat_message_page_control: Control, weixin_window: WindowControl) -> Self:
        chat_info_view = chat_message_page_control.GroupControl(ClassName='mmui::ChatInfoView')
        utils.print_control_tree(chat_message_page_control)
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


class WindowsWeixin(Weixin):
    IMAGE_X_OFFSET = 70
    IMAGE_Y_OFFSET = 30

    ARTICLE_TITLE_TEXT_WIDTH = 266
    ARTICLE_TITLE_TEXT_HEIGHT = 21

    def __init__(self):
        print('init windows weixin')
        super().__init__()
        self.weixin_window = auto.WindowControl(ClassName='mmui::MainWindow', Depth=1)
        self.weixin_window.SetActive()
        self.tab_bar_items = {TabBarItemType(tab_bar.Name): tab_bar for tab_bar in
                              self.weixin_window.ToolBarControl(AutomationId='main_tabbar', Depth=4).GetChildren()}
        self.search_bar = self.weixin_window.GroupControl(ClassName='mmui::XSearchField', Depth=9).EditControl(
            ClassName='mmui::XLineEdit')
        self.chats = {}
        self.sns_window = None
        self.sns_window_tool_bar_items = {}
        self.chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page')
        self.chat_message_list = self.chat_message_page.ListControl(AutomationId='chat_message_list')
        self.current_chat = None
        self._handlers = {}

    def _open_moment(self):
        self.tab_bar_items[TabBarItemType.MOMENTS].Click(simulateMove=False)
        self.sns_window = auto.WindowControl(ClassName='mmui::SNSWindow', Depth=1)
        self.sns_window.SetActive()

    def _publish_moment(self, msg, images, test_mode=False):
        """
        mmui::PublishImageAddGridCell发布后变为mmui::PublishImageGridCell
        Args:
            msg:
            images:

        Returns:

        """
        self.sns_window_tool_bar_items = {SNSWindowToolBarItemType(tool_bar_item.Name): tool_bar_item for tool_bar_item
                                          in self.sns_window.ToolBarControl(AutomationId='sns_window_tool_bar',
                                                                            Depth=3).GetChildren()}
        self.sns_window_tool_bar_items[SNSWindowToolBarItemType.POST].Click()
        sns_publish_panel = self.sns_window.GroupControl(AutomationId='SnsPublishPanel', Depth=4)
        if msg:
            reply_input_field = sns_publish_panel.EditControl(ClassName='mmui::ReplyInputField', Depth=8)
            reply_input_field.SendKeys('{Ctrl}a{Del}')
            reply_input_field.SendKeys(msg)
        if images:
            x_drag_grid_view = sns_publish_panel.ListControl(ClassName='mmui::XDragGridView')
            for image in images:
                x_drag_grid_view.ListItemControl(ClassName='mmui::PublishImageAddGridCell').Click()
                utils.choose_file(self.sns_window.WindowControl(Name='打开'), image)
            x_drag_grid_view.ListItemControl(ClassName='mmui::PublishImageGridCell', Depth=1).GetChildren()
            utils.print_control_tree(self.sns_window)
        if not test_mode:
            sns_publish_panel.ButtonControl(ClassName='mmui::XOutlineButton', Name='发表').Click()

    def _show(self):
        win32gui.ShowWindow(self.weixin_window.NativeWindowHandle, 1)
        time.sleep(0.1)
        win32gui.SetForegroundWindow(self.weixin_window.NativeWindowHandle)
        # self.weixin_window.SwitchToThisWindow()

    def _navigate_to_chat(self, to: str, exact_match=False) -> Chat:
        chat_message_page = None
        if auto.WindowControl(ClassName='mmui::FramelessMainWindow', Depth=1).GroupControl(
                AutomationId='chat_message_page').Exists(maxSearchSeconds=1,
                                                         printIfNotExist=True):
            chat_message_page = auto.WindowControl(ClassName='mmui::FramelessMainWindow', Depth=1).GroupControl(
                AutomationId='chat_message_page')
        elif self.weixin_window.GroupControl(AutomationId='chat_message_page').Exists(maxSearchSeconds=1,
                                                                                      printIfNotExist=True):
            chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        if chat_message_page and chat_message_page.GroupControl(ClassName='mmui::ChatInfoView').TextControl(
                AutomationId='top_content_h_view.top_spacing_v_view.top_left_info_v_view.big_title_line_h_view.current_chat_name_label').Name == to:
            pass
        else:
            self.search_contact(to)
            chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        return WindowsChat.from_control(chat_message_page, self.weixin_window)

    def search_contact(self, name):
        print('search contact')
        if self.search_bar.Exists(1):
            self.search_bar.SetFocus()
            # 有时候会触发一个奇怪的弹窗，强制关闭他
            # blank_window = auto.WindowControl(Name='微信', ClassName='mmui::FramelessMainWindow', Depth=1)
            # if blank_window.Exists():
            #     utils.print_control_tree(blank_window)
            # time.sleep(2)
            self.search_bar.SendKeys(name, interval=0.5)
            is_contact = False
            for child in self.weixin_window.ListControl(AutomationId='search_list', Depth=3).GetChildren():
                if child.ClassName == 'mmui::XTableCell' and child.Name == '联系人':
                    is_contact = True
                if is_contact:
                    if child.ClassName == 'mmui::SearchContentCellView' and child.Name == name:
                        child.Click()

    def _search(self, query: str):
        self.tab_bar_items[TabBarItemType.MINI_PROGRAMS].Click()
        search_pane = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1)
        search_pane.PaneControl(Depth=6, Compare=lambda control,
                                                        _: control.BoundingRectangle.width() == 32 and control.BoundingRectangle.height() == 32).Click()
        search_pane.EditControl(Depth=7).Click()
        search_bar = search_pane.EditControl(Depth=7)
        auto.SetClipboardText(query)
        search_bar.SendKeys('{Ctrl}v')
        search_bar.SendKeys('{Enter}')
        # when search finish, document control has name
        search_pane.DocumentControl(Name='', ClassName='Chrome_RenderWidgetHostHWND', Depth=1).Disappears()

    def history_articles(self, account: str, limit: int) -> list[dict]:
        self.show()
        search_url = self.get_search_url(account, search_type=SearchType.OFFICIAL_ACCOUNTS)
        self.search(search_url)
        search_result = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1).GroupControl(
            AutomationId='search_result', Depth=6,
            Compare=lambda control, _: control.BoundingRectangle.height() > 0)
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
