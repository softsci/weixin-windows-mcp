from weixin_windows_mcp.factory import WeixinFactory

weixin = WeixinFactory.create_weixin()


#
# @weixin.on(MessageType.TEXT)
# def handle_text(message):
#     print('text')
#     print(message)
#
#
# @weixin.on(MessageType.IMAGE)
# def handle_image(message):
#     if message.Name == '图片':
#         weixin.click_media(message)
#         # preview_window = auto.WindowControl(ClassName='mmui::PreviewWindow')
#         print('image')
#
#
# @weixin.on(MessageType.SYSTEM)
# def handle_system(message):
#     print('system')


def main():
    articles = weixin.search_chat_history('MCP交流共创', 'idoubi')
    print(articles)


if __name__ == "__main__":
    main()
