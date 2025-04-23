from weixin_windows_mcp import utils, x
from weixin_windows_mcp.weixin import Weixin, Chat, TabBarItemType, SearchType, MessageType

from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
from ApplicationServices import AXUIElementCreateApplication, kAXErrorSuccess, AXUIElementCopyAttributeNames, \
    AXUIElementCopyAttributeValue


class MacChat(Chat):
    def __init__(self, chat_name: str, chat_count: int | None = None, element=None):
        super().__init__()
        self.chat_name = chat_name
        self.chat_count = chat_count
        self.element = element

    def _focus_input_field(self):
        # 查找并聚焦到输入框
        result, attrs = AXUIElementCopyAttributeNames(self.element, None)
        if result == kAXErrorSuccess:
            for attr in attrs:
                if 'Input' in attr or 'Edit' in attr:
                    result, input_element = AXUIElementCopyAttributeValue(self.element, attr, None)
                    if result == kAXErrorSuccess:
                        input_element.SetFocus()
                        return

    def _at(self, at: str):
        # 实现@功能
        pass

    def _input_text(self, text, typing=False):
        # 实现文本输入
        pass

    def _send_input(self):
        # 实现发送消息
        pass


class MacWeixin(Weixin):
    def __init__(self):
        print('init mac weixin')
        super().__init__()
        # 获取微信应用实例
        apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_('com.tencent.xWeChat')
        if not apps:
            raise RuntimeError('微信未运行')
        self.app = apps[0]
        self.pid = self.app.processIdentifier()
        self.app_ref = AXUIElementCreateApplication(self.pid)
        self.current_chat = None
        self.chats = {}
        self._handlers = {}

    def _open_moment(self):
        # 实现打开朋友圈功能
        result, attrs = AXUIElementCopyAttributeNames(self.app_ref, None)
        if result == kAXErrorSuccess:
            for attr in attrs:
                if 'Moments' in attr or '朋友圈' in attr:
                    result, moments_element = AXUIElementCopyAttributeValue(self.app_ref, attr, None)
                    if result == kAXErrorSuccess:
                        moments_element.Click()
                        return

    def _publish_moment(self, msg, images):
        # 实现发布朋友圈功能
        if images and len(images) > 9:
            raise ValueError('朋友圈图片数量不能超过9张')
        # TODO: 实现发布朋友圈的具体逻辑
        pass

    def _show(self):
        # 显示并激活微信窗口
        self.app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    def _search(self, query: str):
        x.print_element_hierarchy(self.app_ref)
        # 实现搜索功能
        result, attrs = AXUIElementCopyAttributeNames(self.app_ref, None)
        if result == kAXErrorSuccess:
            for attr in attrs:
                if 'Search' in attr or '搜索' in attr:
                    result, search_element = AXUIElementCopyAttributeValue(self.app_ref, attr, None)
                    if result == kAXErrorSuccess:
                        search_element.SetValue(query)
                        return

    def _navigate_to_chat(self, to: str, exact_match=False) -> Chat:
        # 实现导航到聊天功能
        if to in self.chats:
            return self.chats[to]

        # 搜索并打开聊天
        self._search(to)
        # TODO: 实现获取聊天窗口元素的逻辑
        chat_element = None  # 需要实现获取聊天窗口元素的逻辑

        chat = MacChat(chat_name=to, element=chat_element)
        self.chats[to] = chat
        return chat

    def _history_articles(self, limit: int = 1) -> list[dict]:
        # 实现获取历史文章功能
        articles = []
        # TODO: 实现获取历史文章的具体逻辑
        return articles
