#!/usr/bin/env python3
import http.server
import os
import webbrowser
import asyncio
import threading
import json

PORT = 54110
PROJECT_DIR = "c:/Users/wzg823/Desktop/工作/CHATWITHME"
CONTENT_DIR = f"{PROJECT_DIR}/.superpowers/brainstorm/293-1778134611/content"
STATE_DIR = f"{PROJECT_DIR}/.superpowers/brainstorm/293-1778134611/state"

# Start a simple HTTP server in background
def serve():
    os.chdir(CONTENT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(("", PORT), handler)
    print(f"Serving at port {PORT}")
    httpd.serve_forever()

threading.Thread(target=serve, daemon=True).start()
print(f"Server ready at http://localhost:{PORT}")