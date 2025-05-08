import time

from pywinauto.application import Application


def wait_for_content_load(chat_list, timeout=2.0, check_interval=0.1):
    """等待内容加载完成"""
    start_time = time.time()
    previous_items = set()

    while time.time() - start_time < timeout:
        current_items = set(item.window_text() for item in chat_list.children(control_type="ListItem"))

        if current_items and current_items == previous_items:
            # 如果连续两次获取的内容相同，说明加载完成
            return True

        previous_items = current_items
        time.sleep(check_interval)

    return False


if __name__ == '__main__':
    try:
        # 使用窗口句柄直接连接
        app = Application(backend="uia").connect(handle=5900484)
        window = app.window(handle=5900484)

        # 获取聊天记录列表控件
        chat_list = window.child_window(auto_id="chat_log_message_list", control_type="List")

        window.set_focus()
        # 初始化滚动位置，确保加载最新消息
        # 先向下滚动确保在底部
        chat_list.wheel_mouse_input(wheel_dist=3)
        chat_list.wheel_mouse_input(wheel_dist=-5)
        wait_for_content_load(chat_list)
        time.sleep(0.5)  # 额外等待以确保完全加载

        # 再向上滚动一点再向下，触发完整加载
        chat_list.wheel_mouse_input(wheel_dist=1)
        wait_for_content_load(chat_list)
        chat_list.wheel_mouse_input(wheel_dist=-1)
        wait_for_content_load(chat_list)

        print("当前可见的聊天记录：")
        messages = []

        # 获取初始消息
        list_items = chat_list.children(control_type="ListItem")
        for item in list_items:
            msg_text = item.window_text()
            if msg_text not in messages:
                messages.append(msg_text)
                print(f"消息 {len(messages)}: {msg_text}")

        # 循环滚动并获取消息
        for i in range(20):
            # 向上滚动列表
            chat_list.wheel_mouse_input(wheel_dist=1)
            wait_for_content_load(chat_list)

            # 获取当前可见的消息
            list_items = sorted(
                chat_list.children(control_type="ListItem"),
                key=lambda x: x.rectangle().top
            )
            for item in list_items:
                msg_text = item.window_text()
                if msg_text not in messages:
                    messages.append(msg_text)
                    print(f"消息 {len(messages)}: {msg_text}")

    except Exception as e:
        print(f"操作失败: {str(e)}")
