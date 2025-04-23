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
    articles = weixin.send_msg('📚你好元宝，最近过得怎么样呀？希望一切都好！', '元宝')
    print(articles)


if __name__ == "__main__":
    main()
