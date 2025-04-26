import uiautomation as auto
from uiautomation import WindowControl, Control


def choose_file(control: WindowControl, image=None):
    control.EditControl(ClassName='Edit').SendKeys(f'"{image}"')
    control.SendKeys("{Enter}")


def print_control_tree(control: Control, level=0):
    print('  ' * level + (
        f'Type: {control.ControlTypeName}, '
        f'Name: {control.Name}, '
        f'Class: {control.ClassName}, '
        f'AutomationId: {control.AutomationId}, '
        f'Rect: {control.BoundingRectangle}'
    ))
    # 获取所有子控件，包括深层嵌套的
    for child in control.GetChildren():
        print_control_tree(child, level + 1)


def print_control_tree_deep(control: Control, level=0, max_retries=3):
    # 打印当前控件信息
    print('  ' * level + (
        f'Type: {control.ControlTypeName}, '
        f'Name: {control.Name}, '
        f'Class: {control.ClassName}, '
        f'AutomationId: {control.AutomationId}, '
        f'Rect: {control.BoundingRectangle}'
    ))

    selection_pattern = control.GetPattern(auto.PatternId.SelectionPattern)
    if selection_pattern:
        for item in selection_pattern.GetSelection():
            print_control_tree_deep(item, level + 1)


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
