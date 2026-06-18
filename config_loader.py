# -*- coding: utf-8 -*-
"""Загрузка config.json и вычисление полных хостов поддоменов."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"


@dataclass(frozen=True)
class AppConfig:
    domain: str
    project_name: str
    auth_subdomain: str
    cdn_subdomain: str
    main_port: int
    steam_auth_port: int
    dev_proxy_port: int
    use_dev_proxy: bool
    discord_url: str
    telegram_url: str
    shop_url: str
    launcher_download_url: str
    launcher_server_url: str
    steam_auth_host: str
    steam_auth_callback_path: str

    @property
    def auth_host(self) -> str:
        return f"{self.auth_subdomain}.{self.domain}"

    @property
    def cdn_host(self) -> str:
        return f"{self.cdn_subdomain}.{self.domain}"

    @property
    def main_hosts(self) -> tuple[str, ...]:
        return (self.domain, f"www.{self.domain}", "localhost", "127.0.0.1")

    @property
    def auth_public_url(self) -> str:
        return f"https://{self.auth_host}"

    @property
    def cdn_public_url(self) -> str:
        return f"https://{self.cdn_host}"

    @property
    def main_public_url(self) -> str:
        return f"https://{self.domain}"

    @property
    def launcher_callback_url(self) -> str:
        base = self.launcher_server_url.rstrip("/")
        path = self.steam_auth_callback_path
        if not path.startswith("/"):
            path = "/" + path
        return f"{base}{path}"


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or CONFIG_FILE
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    domain = (raw.get("domain") or "sabrrust.online").strip().lower()
    sub = raw.get("subdomains") or {}
    ports = raw.get("ports") or {}
    urls = raw.get("urls") or {}
    steam = raw.get("steam_auth") or {}

    launcher_url = (raw.get("launcher_server_url") or raw.get("launcher_api_base") or "").strip()
    if not launcher_url:
        launcher_url = "http://localhost:10006"

    callback_path = (steam.get("callback_path") or steam.get("main_server_callback_path") or "/api/steam-auth/callback").strip()

    return AppConfig(
        domain=domain,
        project_name=(raw.get("project_name") or "SABR RUST").strip(),
        auth_subdomain=(sub.get("auth") or "auth").strip().lower(),
        cdn_subdomain=(sub.get("cdn") or "cdn").strip().lower(),
        main_port=int(ports.get("main", 8080)),
        steam_auth_port=int(ports.get("steam_auth", 8081)),
        dev_proxy_port=int(ports.get("dev_proxy", 80)),
        use_dev_proxy=bool(raw.get("use_dev_proxy", False)),
        discord_url=(urls.get("discord") or "https://discord.gg/sabrrust").strip(),
        telegram_url=(urls.get("telegram") or "https://t.me/sabrrust").strip(),
        shop_url=(urls.get("shop") or "https://sabrrust.gamestores.app/").strip(),
        launcher_download_url=(urls.get("launcher_download") or "").strip(),
        launcher_server_url=launcher_url,
        steam_auth_host=(steam.get("host") or "0.0.0.0").strip(),
        steam_auth_callback_path=callback_path,
    )


def apply_steam_auth_env(config: AppConfig) -> None:
    """Пробрасывает доменные настройки в переменные окружения для steam_auth_server."""
    os.environ["STEAM_AUTH_PORT"] = str(config.steam_auth_port)
    os.environ["STEAM_AUTH_HOST"] = config.steam_auth_host
    os.environ["STEAM_AUTH_DOMAIN"] = config.auth_host
    os.environ["STEAM_AUTH_PUBLIC_URL"] = config.auth_public_url
    os.environ["MAIN_SERVER_URL"] = config.launcher_server_url.rstrip("/")
    os.environ["MAIN_SERVER_CALLBACK_URL"] = config.launcher_callback_url
