# -*- coding: utf-8 -*-
"""CDN subdomain stub - placeholder for future API."""

from __future__ import annotations

from flask import jsonify

CDN_STUB_HTML = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>CDN</title>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#050508;color:#9898a8;font-family:Segoe UI,sans-serif}
.box{text-align:center;padding:32px;border:1px solid rgba(255,45,45,.2);border-radius:16px;background:rgba(14,14,20,.9)}
h1{color:#ff6b6b;font-size:20px;margin:0 0 8px}p{margin:0;font-size:14px}</style></head>
<body><div class="box"><h1>CDN</h1><p>Razdel v razrabotke</p></div></body></html>"""


def cdn_stub_json():
    return jsonify({"ok": False, "service": "cdn", "status": "stub", "message": "CDN API is not available yet"}), 503
