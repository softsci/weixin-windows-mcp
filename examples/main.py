from weixin_windows_mcp.weixin import Weixin, MessageType

weixin = Weixin()


@weixin.on(MessageType.TEXT)
def handle_text(message):
    print('text')
    print(message)


@weixin.on(MessageType.IMAGE)
def handle_image(message):
    if message.Name == '图片':
        weixin.click_media(message)
        # preview_window = auto.WindowControl(ClassName='mmui::PreviewWindow')
        print('image')


@weixin.on(MessageType.SYSTEM)
def handle_system(message):
    print('system')


def main():
    weixin.add_message_handler(MessageType.TEXT, lambda message: print(message))
    weixin.get_msg()
    # client.publish('朋友圈自动发布器v1.0', images=[r''] * 1)
    weixin.start()


if __name__ == "__main__":
    main()
