from weixin_windows_mcp.weixin import WeChatClient, MessageType

client = WeChatClient()


@client.on(MessageType.TEXT)
def handle_text(message):
    print('text')
    print(message)


@client.on(MessageType.IMAGE)
def handle_image(message):
    if message.Name == '图片':
        client.click_media(message)
        # preview_window = auto.WindowControl(ClassName='mmui::PreviewWindow')
        print('image')


@client.on(MessageType.SYSTEM)
def handle_system(message):
    print('system')


def main():
    client = WeChatClient()
    client.add_message_handler(MessageType.TEXT, lambda message: print(message))
    client.get_msg()
    # client.publish('朋友圈自动发布器v1.0', images=[r'E:\xxd\workspace\databox\databox\wechat\chat\test.jpg'] * 1)
    client.start()


if __name__ == "__main__":
    main()
