from weixin_windows_mcp.weixin import Weixin

weixin = Weixin()


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
    articles = weixin.history_articles('')
    print(articles)


if __name__ == "__main__":
    main()
