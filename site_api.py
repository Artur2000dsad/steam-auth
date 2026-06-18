# -*- coding: utf-8 -*-
"""API основного сайта (не CDN)."""

from __future__ import annotations

import json
import socket
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from config_loader import AppConfig, BASE_DIR

site_bp = Blueprint("site", __name__)

SERVERS_FILE = BASE_DIR / "data" / "servers.json"
CONTENT_DIR = BASE_DIR / "data" / "content"


def _read_servers_file() -> dict:
    default = {
        "partnerServersEnabled": False,
        "servers": [
            {
                "id": 1,
                "name": "SABR RUST | Main",
                "tags": "PVP, X2, Классика",
                "connect": "127.0.0.1:28015",
                "queryPort": 28016,
                "versionDisplay": "266 Devblog",
                "serverTypeLabel": "Ванильный",
                "logoUrl": "",
                "online": False,
                "players": 0,
                "maxPlayers": 100,
            }
        ],
        "partnerServers": [],
    }
    if not SERVERS_FILE.exists():
        return default
    try:
        with open(SERVERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default
        data.setdefault("servers", default["servers"])
        data.setdefault("partnerServers", [])
        data.setdefault("partnerServersEnabled", False)
        return data
    except Exception:
        return default


def _parse_connect_host(connect: str) -> str | None:
    connect = (connect or "").strip()
    if not connect or ":" not in connect:
        return None
    return connect.rsplit(":", 1)[0].strip()


def _a2s_query_info(host: str, query_port: int, timeout: float = 3.0) -> dict:
    """A2S_INFO query for Rust/Source servers."""
    result = {"online": False, "players": 0, "maxPlayers": 0}
    if not host or not query_port:
        return result
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        addr = (host, int(query_port))
        query = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
        sock.sendto(query, addr)
        data = sock.recv(4096)

        if len(data) >= 9 and data[4] == 0x41:
            challenge = data[5:9]
            sock.sendto(query + challenge, addr)
            data = sock.recv(4096)

        if len(data) < 12 or data[4] != 0x49:
            sock.close()
            return result

        idx = 5

        def read_cstring(buf, start):
            end = buf.index(b"\x00", start)
            return buf[start:end].decode("utf-8", errors="replace"), end + 1

        idx += 1  # protocol
        _, idx = read_cstring(data, idx)  # name
        _, idx = read_cstring(data, idx)  # map
        _, idx = read_cstring(data, idx)  # folder
        _, idx = read_cstring(data, idx)  # game
        idx += 2  # app id
        players = data[idx]
        max_players = data[idx + 1]
        result = {
            "online": True,
            "players": int(players),
            "maxPlayers": int(max_players),
        }
        sock.close()
    except Exception:
        pass
    return result


def _enrich_server_status(server: dict) -> dict:
    item = dict(server)
    host = _parse_connect_host(item.get("connect", ""))
    query_port = int(item.get("queryPort") or 0)
    status = _a2s_query_info(host, query_port) if host else {"online": False, "players": 0, "maxPlayers": 0}
    item["online"] = bool(status.get("online"))
    item["players"] = int(status.get("players") or 0)
    item["maxPlayers"] = int(status.get("maxPlayers") or 0)
    return item


@site_bp.get("/api/health")
def api_health():
    return jsonify({"ok": True, "service": "website"})


@site_bp.get("/api/servers")
def api_servers():
    data = _read_servers_file()
    servers = [_enrich_server_status(s) for s in data.get("servers") or []]
    partner = [_enrich_server_status(s) for s in data.get("partnerServers") or []]
    return jsonify(
        {
            "ok": True,
            "partnerServersEnabled": bool(data.get("partnerServersEnabled")),
            "servers": servers,
            "partnerServers": partner if data.get("partnerServersEnabled") else [],
        }
    )


@site_bp.get("/api/site-config")
def api_site_config():
    cfg: AppConfig = current_app.config["APP_CONFIG"]
    return jsonify(
        {
            "projectName": cfg.project_name,
            "domain": cfg.domain,
            "authUrl": cfg.auth_public_url,
            "launcherServerUrl": cfg.launcher_server_url,
            "urls": {
                "discord": cfg.discord_url,
                "telegram": cfg.telegram_url,
                "shop": cfg.shop_url,
                "launcher": cfg.launcher_download_url or None,
            },
        }
    )


@site_bp.get("/api/content/<doc_id>")
def api_content(doc_id: str):
    safe_id = "".join(ch for ch in doc_id if ch.isalnum() or ch in ("-", "_"))
    path = CONTENT_DIR / f"{safe_id}.json"
    if not path.exists():
        return jsonify({"ok": False, "error": "not found"}), 404
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, **data})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
