# -*- coding: utf-8 -*-
"""
SABR RUST - main project server.

Runs:
  1) Website on main domain (sabrrust.online)
  2) CDN stub on cdn.sabrrust.online (placeholder)
  3) Steam Auth subprocess on auth.sabrrust.online
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
import threading

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.serving import run_simple

from cdn_api import CDN_STUB_HTML, cdn_stub_json
from config_loader import BASE_DIR, AppConfig, apply_steam_auth_env, load_config
from site_api import site_bp

WEBSITE_DIR = BASE_DIR / "website"
_steam_auth_proc: subprocess.Popen | None = None


def _host_without_port() -> str:
    return (request.host or "").split(":")[0].lower()


def create_app(config: AppConfig) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["APP_CONFIG"] = config
    app.register_blueprint(site_bp)

    @app.before_request
    def guard_subdomain():
        host = _host_without_port()

        if host == config.auth_host:
            abort(404)

        if host == config.cdn_host:
            if request.path.startswith("/api"):
                return cdn_stub_json()
            return CDN_STUB_HTML, 503, {"Content-Type": "text/html; charset=utf-8"}

        return None

    @app.get("/")
    def index_page():
        return send_from_directory(WEBSITE_DIR, "index.html")

    @app.get("/css/<path:filename>")
    def css_files(filename: str):
        return send_from_directory(WEBSITE_DIR / "css", filename)

    @app.get("/js/<path:filename>")
    def js_files(filename: str):
        return send_from_directory(WEBSITE_DIR / "js", filename)

    @app.get("/assets/<path:filename>")
    def asset_files(filename: str):
        return send_from_directory(WEBSITE_DIR / "assets", filename)

    @app.get("/health")
    def health():
        if _host_without_port() == config.cdn_host:
            return jsonify({"ok": False, "service": "cdn", "status": "stub"}), 503
        return jsonify({"ok": True, "service": "website"})

    return app


def start_steam_auth_subprocess(config: AppConfig) -> subprocess.Popen:
    apply_steam_auth_env(config)
    env = os.environ.copy()
    script = BASE_DIR / "steam_auth_server.py"
    python = sys.executable
    proc = subprocess.Popen([python, str(script)], cwd=str(BASE_DIR), env=env)
    print(f"[Main] Steam Auth PID {proc.pid} -> {config.auth_public_url}")
    print(f"[Main] Callbacks -> {config.launcher_callback_url}")
    return proc


def stop_steam_auth_subprocess() -> None:
    global _steam_auth_proc
    if _steam_auth_proc and _steam_auth_proc.poll() is None:
        _steam_auth_proc.terminate()
        try:
            _steam_auth_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _steam_auth_proc.kill()
        print("[Main] Steam Auth stopped")


def _run_dev_proxy(config: AppConfig, target_port: int) -> None:
    import socket
    from http.client import HTTPConnection

    listen_port = config.dev_proxy_port

    def handle_client(client_sock: socket.socket) -> None:
        try:
            client_sock.settimeout(10)
            raw = client_sock.recv(65535)
            if not raw:
                client_sock.close()
                return
            header_end = raw.find(b"\r\n\r\n")
            if header_end < 0:
                client_sock.close()
                return
            header_text = raw[:header_end].decode("iso-8859-1", errors="replace")
            lines = header_text.split("\r\n")
            if not lines:
                client_sock.close()
                return
            req_line = lines[0].split()
            if len(req_line) < 2:
                client_sock.close()
                return
            method, path = req_line[0], req_line[1]

            host_header = config.domain
            for line in lines[1:]:
                if line.lower().startswith("host:"):
                    host_header = line.split(":", 1)[1].strip().lower()
                    break

            upstream_port = config.steam_auth_port if host_header == config.auth_host else target_port

            conn = HTTPConnection("127.0.0.1", upstream_port, timeout=15)
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    if k.lower() not in ("connection", "proxy-connection"):
                        headers[k.strip()] = v.strip()
            body = raw[header_end + 4 :]
            conn.request(method, path, body=body or None, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()
            out = f"HTTP/1.1 {resp.status} {resp.reason}\r\n".encode()
            for k, v in resp.getheaders():
                if k.lower() != "transfer-encoding":
                    out += f"{k}: {v}\r\n".encode()
            out += b"\r\n" + resp_body
            client_sock.sendall(out)
            conn.close()
        except Exception as exc:
            print(f"[DevProxy] {exc}")
        finally:
            client_sock.close()

    def serve() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", listen_port))
        srv.listen(128)
        print(f"[DevProxy] :{listen_port} -> auth:{config.steam_auth_port}, other:{target_port}")
        while True:
            client, _ = srv.accept()
            threading.Thread(target=handle_client, args=(client,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()


def main() -> None:
    global _steam_auth_proc
    config = load_config()
    print("=" * 54)
    print(f"  {config.project_name} - Main Server")
    print("=" * 54)
    print(f"  Website : http://localhost:{config.main_port}  ({config.domain})")
    print(f"  CDN stub: Host {config.cdn_host} (placeholder)")
    print(f"  Auth    : http://localhost:{config.steam_auth_port} ({config.auth_host})")
    print(f"  Launcher: {config.launcher_server_url}")
    print("=" * 54)

    _steam_auth_proc = start_steam_auth_subprocess(config)
    atexit.register(stop_steam_auth_subprocess)

    app = create_app(config)

    if config.use_dev_proxy:
        _run_dev_proxy(config, config.main_port)

    try:
        run_simple("0.0.0.0", config.main_port, app, use_reloader=False, use_debugger=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[Main] Stopping...")
    finally:
        stop_steam_auth_subprocess()


if __name__ == "__main__":
    main()
