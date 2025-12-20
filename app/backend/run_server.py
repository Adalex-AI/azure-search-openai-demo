#!/usr/bin/env python
"""Simple script to run the backend server."""
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from main import app

if __name__ == "__main__":
    config = Config()
    config.bind = ["127.0.0.1:50505"]
    asyncio.run(serve(app, config))
