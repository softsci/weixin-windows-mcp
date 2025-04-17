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
    weixin = ctx.request_context.lifespan_context.weixin
    weixin.send_msg(msg, to)


@mcp.tool()
def history_articles(ctx: Context, account: str, limit: int = 1):
    weixin = ctx.request_context.lifespan_context.weixin
    return weixin.history_articles(account, limit)


@mcp.tool()
async def summary_article(ctx: Context, url: str):
    prompt = f"总结一下这个链接里的文章下面的文章: {url}"
    response = await ctx.sample(prompt)
    return response.text


@mcp.tool()
def publish_moment(ctx: Context, content: str, images: list[str] | None = None):
    weixin = ctx.request_context.lifespan_context.weixin
    weixin.publish(content, images)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
