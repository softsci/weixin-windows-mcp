from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from fastmcp import FastMCP, Context

from weixin_windows_mcp.factory import WeixinFactory
from weixin_windows_mcp.weixin import Weixin


@dataclass
class AppContext:
    weixin: Weixin


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    weixin = WeixinFactory.create_weixin()
    try:
        yield AppContext(weixin=weixin)
    finally:
        pass


mcp = FastMCP("Weixin MCP Service 🤖", lifespan=app_lifespan)


@mcp.tool()
def send_msg(ctx: Context, msg: str, to: str):
    print(msg, to)
    weixin: Weixin = ctx.request_context.lifespan_context.weixin
    weixin.send_msg(msg, to)


@mcp.tool()
def publish_moment(ctx: Context, content: str, images: list[str] | None = None):
    weixin: Weixin = ctx.request_context.lifespan_context.weixin
    weixin.publish_moment(content, images)


@mcp.tool()
def history_articles(ctx: Context, account: str, limit: int = 1):
    weixin: Weixin = ctx.request_context.lifespan_context.weixin
    return weixin.history_articles(account, limit)


@mcp.tool()
async def summary_article(ctx: Context, url: str):
    prompt = f"总结一下这个链接里的文章下面的文章: {url}"
    response = await ctx.sample(prompt)
    return response.text


@mcp.prompt()
def get_wx_mcp_prompt():
    return """你是一个模拟人类使用微信的AI助手。你需要像真实用户一样自然地使用微信的各项功能。

可用工具：
1. send_msg(msg: str, to: str) - 发送消息
2. publish_moment(content: str, images: list[str]) - 发送朋友圈
3. history_articles(account: str, limit: int) - 获取历史文章
4. summary_article(url: str) - 总结文章内容

行为准则：
1. 交互风格
- 保持自然的对话节奏
- 使用得体的语言表达
- 避免机械化的重复回复

2. 内容管理
- 发送消息时注意语气和措辞
- 朋友圈内容要积极正面
- 分享文章要注意内容质量

3. 使用限制
- 避免频繁发送相同内容
- 不发布敏感或不当信息
- 遵守微信使用规范

4. 互动原则
- 根据上下文合理回应
- 适时使用表情和图片
- 保持礼貌和友好态度

请像一个真实的微信用户一样，自然地使用这些功能进行社交互动。"""


def main():
    mcp.run()


if __name__ == "__main__":
    main()
