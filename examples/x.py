import time
from AppKit import *
from Foundation import *
from ApplicationServices import *
import objc


def print_element_hierarchy(element, level=0):
    """打印元素层级结构"""
    indent = "  " * level

    # 获取元素属性
    attrs = {}
    result, attr_names = AXUIElementCopyAttributeNames(element, None)

    if result == kAXErrorSuccess and attr_names:
        for attr in attr_names:
            result, value = AXUIElementCopyAttributeValue(element, attr, None)
            if result == kAXErrorSuccess:
                attrs[attr] = value

    # 获取基本信息
    role = attrs.get('AXRole', 'Unknown')
    title = attrs.get('AXTitle', '')
    identifier = attrs.get('AXIdentifier', '')
    description = attrs.get('AXDescription', '')
    help_text = attrs.get('AXHelp', '')
    position = attrs.get('AXPosition', '')
    size = attrs.get('AXSize', '')
    enabled = attrs.get('AXEnabled', '')
    focused = attrs.get('AXFocused', '')

    # 打印详细信息
    print(f"{indent}{'=' * 50}")
    print(f"{indent}控件类型: {role}")
    if title:
        print(f"{indent}标题: {title}")
    if identifier:
        print(f"{indent}标识符: {identifier}")
    if description:
        print(f"{indent}描述: {description}")
    if help_text:
        print(f"{indent}帮助文本: {help_text}")
    if position:
        print(f"{indent}位置: {position}")
    if size:
        print(f"{indent}大小: {size}")
    if enabled is not None:
        print(f"{indent}是否启用: {enabled}")
    if focused is not None:
        print(f"{indent}是否焦点: {focused}")

    # 打印所有可用的属性名称
    print(f"{indent}可用属性: {', '.join(attr_names)}")
    print(f"{indent}{'=' * 50}")

    # 递归打印子元素
    children = attrs.get('AXChildren', [])
    if children:
        for child in children:
            print_element_hierarchy(child, level + 1)


apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_('com.tencent.xWeChat')
if apps:
    app = apps[0]
    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    time.sleep(2)
    pid = app.processIdentifier()
    # 获取应用的 UI 元素
    app_ref = AXUIElementCreateApplication(pid)
    print("\n微信应用控件层级结构:")
    print_element_hierarchy(app_ref)
