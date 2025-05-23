import random
import time
from typing import Callable, Any, Self

import uiautomation as auto
import win32clipboard
import win32con
import win32gui
from uiautomation import Control, WindowControl

from weixin_windows_mcp import utils
from weixin_windows_mcp.weixin import Weixin, TabBarItemType, ContactsMasterSubTypeCellViewType, \
    MessageType, ChatMessageClassName, SNSWindowToolBarItemType, ChatMessagePageType, Chat, ChatToolBarButtonType, \
    ChatLogMessage


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
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
            win32clipboard.CloseClipboard()
            auto.SendKeys('{Ctrl}v')

    def _send_input(self):
        auto.SendKeys('{ENTER}')

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


class WindowsWeixin(Weixin):
    IMAGE_X_OFFSET = 70
    IMAGE_Y_OFFSET = 30

    ARTICLE_TITLE_TEXT_WIDTH = 266
    ARTICLE_TITLE_TEXT_HEIGHT = 21

    AVATAR_IMAGE_WIDTH = 40
    AVATAR_IMAGE_HEIGHT = 40

    AVATAR_X_OFFSET = 28
    AVATAR_Y_OFFSET = 15

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
        self.chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        self.chat_message_list = self.chat_message_page.ListControl(AutomationId='chat_message_list')
        self.current_chat = None
        self._handlers = {}

    def _click_chat_tool_bar(self, button_type: ChatToolBarButtonType):
        for child in self.chat_message_page.ToolBarControl(AutomationId='tool_bar_accessible').GetChildren():
            if child.Name == button_type.value:
                child.Click()

    def _search_chat_history(self, query: str = None, from_date: str = None, to_date: str = None) -> list[
        ChatLogMessage]:
        search_msg_unique_chat_window = auto.WindowControl(ClassName='mmui::SearchMsgUniqueChatWindow',
                                                           Depth=1)
        if query:
            search_msg_unique_chat_window.EditControl(ClassName='mmui::XLineEdit', Depth=5).SendKeys(query)
            auto.SendKeys('{ENTER}')
        chat_log_message_list = search_msg_unique_chat_window.ListControl(
            AutomationId='chat_log_message_list', Depth=4)
        chat_log_message_list.WheelUp(1)
        time.sleep(0.5)
        self.wait_for_content_load(chat_log_message_list)
        chat_log_message_list.WheelDown(1)
        time.sleep(0.5)
        print("聊天记录列表控件信息:")
        max_try_count = 10
        # 直接获取所有子控件
        chat_log_messages = []
        try_count = 0
        # 根据屏幕Y坐标（从上到下）排序
        msg_id_set = set()
        while try_count <= max_try_count:
            chat_log_message_list.Refind()
            children = chat_log_message_list.GetChildren()
            for child in children:
                runtime_id = child.GetRuntimeId()
                if runtime_id in msg_id_set:
                    continue
                if utils.is_visible(child):
                    nickname = None
                    msg_type = ChatMessageClassName(child.ClassName)
                    if msg_type != ChatMessageClassName.SYSTEM:
                        # 计算头像中心点击位置
                        avatar_center_x = self.AVATAR_X_OFFSET + (self.AVATAR_IMAGE_WIDTH / 2)
                        avatar_center_y = self.AVATAR_Y_OFFSET + (self.AVATAR_IMAGE_HEIGHT / 2)

                        # 点击头像获取昵称
                        child.Click(x=int(avatar_center_x), y=int(avatar_center_y), simulateMove=True)
                        nickname = self.parse_nickname()
                    msg_time, msg = self.parse_message(child.Name)
                    clm = ChatLogMessage(nickname=nickname, msg_time=msg_time, msg=msg,
                                         msg_type=ChatMessageClassName(child.ClassName))
                    print(f"获取到的消息: {clm}")

                    # 添加消息到列表
                    chat_log_messages.append(clm)

                    msg_id_set.add(runtime_id)
                else:
                    print(child.Name)

            chat_log_message_list.WheelUp(waitTime=0.1)
            self.wait_for_content_load(chat_log_message_list)
            try_count += 1

        return chat_log_messages

    @staticmethod
    def is_avatar_visible(child, container):
        """判断头像区域是否在可见范围内"""
        # 获取头像区域的矩形
        avatar_rect = child.BoundingRectangle
        avatar_rect.left += WindowsWeixin.AVATAR_X_OFFSET
        avatar_rect.top += WindowsWeixin.AVATAR_Y_OFFSET
        avatar_rect.right = avatar_rect.left + WindowsWeixin.AVATAR_IMAGE_WIDTH
        avatar_rect.bottom = avatar_rect.top + WindowsWeixin.AVATAR_IMAGE_HEIGHT

        # 获取容器的可见区域
        container_rect = container.BoundingRectangle

        # 判断头像是否完全在可见区域内
        return (avatar_rect.top >= container_rect.top and
                avatar_rect.bottom <= container_rect.bottom and
                avatar_rect.left >= container_rect.left and
                avatar_rect.right <= container_rect.right)

    @staticmethod
    def wait_for_content_load(control, timeout=2.0, check_interval=0.1):
        """等待内容加载完成"""
        start_time = time.time()
        previous_items = set()

        while time.time() - start_time < timeout:
            current_items = set(item.Name for item in control.GetChildren())

            if current_items and current_items == previous_items:
                # 如果连续两次获取的内容相同，说明加载完成
                return True

            previous_items = current_items
            time.sleep(check_interval)

        return False

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
        try:
            # 检查窗口句柄
            if not self.weixin_window.NativeWindowHandle:
                print("无法获取微信窗口句柄")
                return False

            # 如果窗口最小化，先恢复
            if win32gui.IsIconic(self.weixin_window.NativeWindowHandle):
                win32gui.ShowWindow(self.weixin_window.NativeWindowHandle, 9)  # SW_RESTORE
                time.sleep(1)  # Windows 11下需要更长的等待时间

            # 使用临时置顶的技巧来激活窗口
            win32gui.SetWindowPos(
                self.weixin_window.NativeWindowHandle,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            time.sleep(0.2)

            # 取消置顶，回到普通窗口状态
            win32gui.SetWindowPos(
                self.weixin_window.NativeWindowHandle,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )

            # 使用SetForegroundWindow确保窗口在最前面
            win32gui.SetForegroundWindow(self.weixin_window.NativeWindowHandle)

            # 最后再尝试常规激活
            self.weixin_window.SetActive()

            return True
        except Exception as e:
            print(f"激活窗口失败: {str(e)}")
            return False

    def _navigate_to_chat(self, to: str, exact_match=False) -> Chat:
        chat_message_page = None
        frameless_window = auto.WindowControl(Name=to, ClassName='mmui::FramelessMainWindow', Depth=1)
        if frameless_window.Exists(maxSearchSeconds=0.5, printIfNotExist=True):
            chat_message_page_control = frameless_window.GroupControl(AutomationId='chat_message_page', Depth=3)
            if chat_message_page_control.Exists(maxSearchSeconds=0.1, printIfNotExist=True):
                chat_message_page = chat_message_page_control
        elif self.weixin_window.Exists(maxSearchSeconds=0.5, printIfNotExist=True) and self.weixin_window.GroupControl(
                AutomationId='chat_message_page',
                Depth=7).Exists(maxSearchSeconds=0.5, printIfNotExist=True):
            chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        if chat_message_page and chat_message_page.GroupControl(ClassName='mmui::ChatInfoView', Depth=1).TextControl(
                AutomationId='top_content_h_view.top_spacing_v_view.top_left_info_v_view.big_title_line_h_view.current_chat_name_label',
                Depth=5).Name == to:
            chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        else:
            self.search_contact(to)
            chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page', Depth=7)
        return WindowsChat.from_control(chat_message_page, self.weixin_window)

    def search_contact(self, name):
        if self.search_bar.Exists(1):
            self.search_bar.SetFocus()
            self.search_bar.SendKeys(name, interval=0.5)
            is_contact = False
            for child in self.weixin_window.ListControl(AutomationId='search_list', Depth=3).GetChildren():
                if child.ClassName == 'mmui::XTableCell' and child.Name in ('联系人', '群聊'):
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

    def _history_articles(self, limit: int = 1) -> list[dict]:
        search_pane = auto.PaneControl(Name='微信', ClassName='Chrome_WidgetWin_0', Depth=1)
        search_result = search_pane.GroupControl(
            AutomationId='search_result', Depth=6,
            Compare=lambda control, _: control.BoundingRectangle.height() > 0)
        search_result.ButtonControl(Depth=5).Click()
        official_account_pane = auto.PaneControl(Name='公众号', ClassName='Chrome_WidgetWin_0', Depth=1)
        official_account_pane.HyperlinkControl(Name='消息').Exists(maxSearchSeconds=5)
        skip_group = False
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

    def parse_nickname(self) -> str:
        profile_unique_pop = auto.WindowControl(Name='Weixin', ClassName='mmui::ProfileUniquePop', Depth=1)
        right_v_view = profile_unique_pop.GroupControl(AutomationId='right_v_view', Depth=5)
        nickname = right_v_view.TextControl(AutomationId='right_v_view.nickname_button_view.display_name_text',
                                            Depth=2).Name
        auto.SendKeys('{Esc}')
        return nickname
