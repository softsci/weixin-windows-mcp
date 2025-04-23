import platform

WindowsWeixin = None
MacWeixin = None

# 根据平台条件导入
current_platform = platform.system().lower()
if current_platform == "windows":
    from weixin_windows_mcp.windows_weixin import WindowsWeixin
elif current_platform == "darwin":
    from weixin_windows_mcp.mac_weixin import MacWeixin
else:
    raise ValueError(f"不支持的平台: {current_platform}")


class WeixinFactory:
    @staticmethod
    def create_weixin():
        platform_to_class = {
            "windows": WindowsWeixin,
            "darwin": MacWeixin
        }
        weixin_class = platform_to_class.get(current_platform)
        if weixin_class:
            return weixin_class()
        else:
            raise ValueError(f"不支持的平台: {current_platform}")
