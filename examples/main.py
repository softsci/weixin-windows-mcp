from src.wechat_pc_mcp.wx_client import WeChatClient, ChatMessageClassName, MessageType

client = WeChatClient()


@client.on(ChatMessageClassName.TEXT)
def handle_text(message):
    print('text')
    print(message)


@client.on(ChatMessageClassName.IMAGE)
def handle_image(message):
    if message.Name == '图片':
        client.click_media(message)
        # preview_window = auto.WindowControl(ClassName='mmui::PreviewWindow')
        print('image')


@client.on(ChatMessageClassName.SYSTEM)
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
