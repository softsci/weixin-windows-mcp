import time
from enum import StrEnum
from typing import Callable, Any, Self

import uiautomation as auto
from uiautomation import Control

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


class Weixin:
    IMAGE_X_OFFSET = 70
    IMAGE_Y_OFFSET = 30

    def __init__(self):
        self._handlers = {}
        self.weixin_window = auto.WindowControl(searchDepth=1, ClassName='mmui::MainWindow')
        self.weixin_window.SetActive()
        self.tab_bar_items = {TabBarItemType(tab_bar.Name): tab_bar for tab_bar in
                              self.weixin_window.ToolBarControl(searchDepth=4,
                                                                searAutomationId='main_tabbar').GetChildren()}
        self.search_bar = self.weixin_window.EditControl(searchDepth=10, ClassName='mmui::XlineEdit')
        self.chats = self.get_chat_dict()
        self.sns_window = None
        self.sns_window_tool_bar_items = {}
        self.chat_message_page = self.weixin_window.GroupControl(AutomationId='chat_message_page')
        self.chat_message_list = self.chat_message_page.ListControl(AutomationId='chat_message_list')

    def on(self, message_type: MessageType):
        """装饰器方法"""

        def decorator(handler):
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
        self.sns_window = auto.WindowControl(searchDepth=1, ClassName='mmui::SNSWindow')
        self.sns_window.SetActive()
        self.sns_window_tool_bar_items = {SNSWindowToolBarItemType(tool_bar_item.Name): tool_bar_item for tool_bar_item
                                          in self.sns_window.ToolBarControl(searchDepth=3,
                                                                            AutomationId='sns_window_tool_bar').GetChildren()}
        self.sns_window_tool_bar_items[SNSWindowToolBarItemType.POST].Click()
        sns_publish_panel = self.sns_window.GroupControl(searchDepth=4, AutomationId='SnsPublishPanel')
        if msg:
            reply_input_field = sns_publish_panel.EditControl(searchDepth=8, ClassName='mmui::ReplyInputField')
            reply_input_field.SendKeys('{Ctrl}a{Delete}')
            reply_input_field.SendKeys(msg)
        if images:
            x_drag_grid_view = sns_publish_panel.ListControl(ClassName='mmui::XDragGridView')
            for image in images:
                x_drag_grid_view.ListItemControl(ClassName='mmui::PublishImageAddGridCell').Click()
                utils.choose_file(self.sns_window.WindowControl(Name='打开'), image)
            x_drag_grid_view.ListItemControl(searchDepth=1, ClassName='mmui::PublishImageGridCell').GetChildren()
            utils.print_control_tree(self.sns_window)
        sns_publish_panel.ButtonControl(ClassName='mmui::XOutlineButton', Name='发表').Click()

    def get_chat_dict(self,max_chats: int = 100) -> dict[str, Control]:
        chat_list = self.weixin_window.ListControl(ClassName='mmui::XTableView')
        return {chat.Name: chat for chat in chat_list.GetChildren()}

    def send_msg(self, msg: str, to: str, at_users: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False) -> None:
        if to in self.chats:
            self.chats[to].Click(simulateMove=False)
            edit_box = self.chat_content.EditControl(Name=to)
            if typing:
                # 使用打字模式
                self.send_typing_text(msg)
            else:
                # 使用剪贴板模式
                auto.SetClipboardText(msg)
                edit_box.SendKeys('{Ctrl}v')
            edit_box.SendKeys('{Enter}')

    def click_moments(self):
        if not self.weixin_window:
            return False

        moments_button = self.weixin_window.ButtonControl(searchDepth=5, Name='朋友圈')
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

        moments_scroll = self.weixin_window.PaneControl(searchDepth=5, AutomationId='moments_scroll')
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

    def send_typing_text(self, text: str, min_interval: float = 0.1, max_interval: float = 0.3) -> bool:
        import random

        edit_box = self.weixin_window.EditControl(Name='输入')
        if not edit_box.Exists(3):
            return False

        edit_box.Click(simulateMove=False)

        for char in text:
            edit_box.SendKeys(char, waitTime=0)  # waitTime=0 避免内部延迟
            # 随机等待时间，模拟真实输入
            time.sleep(random.uniform(min_interval, max_interval))

        return True
