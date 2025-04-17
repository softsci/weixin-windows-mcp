import re


def find_element(self, element, AXRole, AXClass, AXIdentifier, name, sub_name, regex_name,
                 compare) -> AXUIElement:
    if AXRole:
        result, role = AXUIElementCopyAttributeValue(element, 'AXRole', None)
        if result != kAXErrorSuccess or role != AXRole:
            return False


def _matches_search_conditions(self, element, AXRol, AXClass, AXIdentifier, name, sub_name, regex_name,
                               compare) -> Ui:
    """检查元素是否匹配搜索条件"""
    # 检查 ControlType
    if AXRole:
        result, role = AXUIElementCopyAttributeValue(element, 'AXRole', None)
        if result != kAXErrorSuccess or role != control_type:
            return False

    # 检查 ClassName
    if AXClass:
        # macOS 上没有直接的 ClassName 属性，可以使用 AXClass 或其他方式
        # 这里只是一个示例，实际实现可能需要调整
        result, value = AXUIElementCopyAttributeValue(element, 'AXClass', None)
        if result != kAXErrorSuccess or value != class_name:
            return False

    # 检查 AutomationId
    if AXIdentifier:
        result, value = AXUIElementCopyAttributeValue(element, 'AXIdentifier', None)
        if result != kAXErrorSuccess or value != automation_id:
            return False

    # 检查 Name
    if AXTitle:
        result, value = AXUIElementCopyAttributeValue(element, 'AXTitle', None)
        if result != kAXErrorSuccess or value != name:
            return False

    # 检查 SubName
    if sub_name:
        result, value = AXUIElementCopyAttributeValue(element, 'AXTitle', None)
        if result != kAXErrorSuccess or sub_name not in value:
            return False

    # 检查 RegexName
    if regex_name:
        result, value = AXUIElementCopyAttributeValue(element, 'AXTitle', None)
        if result != kAXErrorSuccess or not re.match(regex_name, value):
            return False

    # 检查自定义比较函数
    if compare:
        if not compare(element, current_depth):
            return False

    return True
