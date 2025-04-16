from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from fastapi import FastAPI
from fastmcp import FastMCP, Context

from weixin import Weixin


@dataclass
class AppContext:
    weixin: Weixin


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    weixin = Weixin()
    try:
        yield AppContext(weixin=weixin)
    finally:
        pass


mcp = FastMCP("Weixin MCP Service 🤖", lifespan=app_lifespan)

app = FastAPI()
app.mount("/", mcp.sse_app())


@mcp.tool()
def send_msg(ctx: Context, msg: str, to: str):
    print(msg, to)
    weixin = ctx.request_context.lifespan_context.weixin
    weixin.send_msg(msg, to)


@mcp.tool()
def history_articles(ctx: Context, account: str):
    weixin = ctx.request_context.lifespan_context.weixin
    return weixin.history_articles(account)


@mcp.tool()
def publish_moment(ctx: Context, content: str, images: list[str] | None = None):
    weixin = ctx.request_context.lifespan_context.weixin
    weixin.publish(content, images)


if __name__ == "__main__":
    mcp.run()
