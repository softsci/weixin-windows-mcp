from weixin_windows_mcp import mac_utils
from weixin_windows_mcp.weixin_base import Weixin

class MacWeixin(Weixin):
    def __init__(self):
        self.weixin_window = mac_utils._matches_search_conditions()

    def send_msg(self, msg: str, to: str = None, at: str | list[str] = None, exact_match: bool = False,
                 typing: bool = False):

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
