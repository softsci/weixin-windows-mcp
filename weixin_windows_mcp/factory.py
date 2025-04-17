import platform

from weixin_windows_mcp.weixin import WindowsWeixin


class WeixinFactory:
    @staticmethod
    def create_weixin():
        current_platform = platform.system().lower()
        platform_to_class = {
            "windows": WindowsWeixin,
            "darwin": MacWeixin
        }
        weixin_class = platform_to_class.get(current_platform)
        if weixin_class:
            return weixin_class()
        else:
            raise ValueError(f"不支持的平台: {current_platform}")
