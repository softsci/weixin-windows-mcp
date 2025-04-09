from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import Context, FastMCP

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
def publish_moment(ctx: Context, content: str, images: list[str] | None = None):
    """Tool that uses initialized resources"""
    weixin = ctx.request_context.lifespan_context['weixin']
    weixin.publish(content, images)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
