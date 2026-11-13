#!/usr/bin/env python3
"""Absolute-path launcher for MCP clients, independent of their working directory."""
from benchmark_maker.mcp import serve
if __name__ == '__main__':
    serve()
