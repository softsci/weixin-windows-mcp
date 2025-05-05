from uiautomation import WindowControl, Control


def choose_file(control: WindowControl, image=None):
    control.EditControl(ClassName='Edit').SendKeys(f'"{image}"')
    control.SendKeys("{Enter}")


def print_control_tree(control: Control, level=0):
    """更详细地打印控件树，包括所有属性"""
    print('  ' * level + (
        f'Type: {control.ControlTypeName}, '
        f'Name: {control.Name}, '
        f'Class: {control.ClassName}, '
        f'AutomationId: {control.AutomationId}, '
        f'Rect: {control.BoundingRectangle}, '
        f'IsOffscreen: {control.IsOffscreen}, '
        f'ControlType: {control.ControlType}'
    ))
    # 获取所有子控件，包括深层嵌套的
    for child in control.GetChildren():
        print_control_tree(child, level + 1)


def is_visible(element: Control, container=None):
    container = container or element.GetParentControl()
    if not container:
        return True
    return (element.BoundingRectangle.top >= container.BoundingRectangle.top and
            element.BoundingRectangle.bottom <= container.BoundingRectangle.bottom)


def ensure_visible(element: Control, container=None):
    """确保元素在容器的可见区域内

    Args:
        element: 需要显示的元素
        container: 容器控件，默认使用元素的父容器
    """
    container = container or element.GetParentControl()
    if not container:
        return

    while element.BoundingRectangle.top < container.BoundingRectangle.top:
        container.WheelUp(waitTime=0.1)

    while element.BoundingRectangle.bottom > container.BoundingRectangle.bottom:
        container.WheelDown(waitTime=0.1)
