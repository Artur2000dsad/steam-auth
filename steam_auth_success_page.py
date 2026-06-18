# -*- coding: utf-8 -*-
"""HTML-страница успешной Steam-авторизации в стиле SABR RUST Launcher."""

from __future__ import annotations

import html as html_module


def render_auth_success_html(steam_name: str, steam_id: str | None, avatar_url: str) -> str:
    safe_name = html_module.escape(steam_name or "Пользователь")
    safe_id = html_module.escape(steam_id or "N/A")
    safe_avatar = html_module.escape(
        avatar_url
        or "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"
    )
    fallback_avatar = "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>SABR RUST — вход выполнен</title>
	<meta http-equiv="refresh" content="8;url=steam://">
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap" rel="stylesheet">
	<style>
		* {{ box-sizing: border-box; margin: 0; padding: 0; }}
		body {{
			font-family: 'Segoe UI', system-ui, sans-serif;
			min-height: 100vh;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 24px;
			color: #E8E8EC;
			background: #050508;
			overflow: hidden;
		}}
		.bg {{
			position: fixed;
			inset: 0;
			background:
				radial-gradient(ellipse 80% 60% at 20% 10%, rgba(255, 45, 45, 0.14), transparent 55%),
				radial-gradient(ellipse 70% 50% at 85% 90%, rgba(185, 28, 28, 0.12), transparent 50%),
				linear-gradient(145deg, #050508 0%, #0a0608 40%, #120808 70%, #08080c 100%);
			z-index: 0;
		}}
		.bg-grid {{
			position: fixed;
			inset: 0;
			z-index: 0;
			pointer-events: none;
			background-image:
				linear-gradient(rgba(255, 45, 45, 0.04) 1px, transparent 1px),
				linear-gradient(90deg, rgba(255, 45, 45, 0.04) 1px, transparent 1px);
			background-size: 48px 48px;
			mask-image: radial-gradient(ellipse 80% 70% at 50% 30%, black 20%, transparent 75%);
		}}
		.orb {{
			position: fixed;
			border-radius: 50%;
			filter: blur(60px);
			opacity: 0.35;
			animation: drift 14s ease-in-out infinite;
			z-index: 0;
			pointer-events: none;
		}}
		.orb-1 {{ width: 280px; height: 280px; background: #FF2D2D; top: -80px; left: -60px; }}
		.orb-2 {{ width: 220px; height: 220px; background: #B91C1C; bottom: -60px; right: -40px; animation-delay: -5s; }}
		@keyframes drift {{
			0%, 100% {{ transform: translate(0, 0) scale(1); }}
			50% {{ transform: translate(24px, 18px) scale(1.06); }}
		}}
		.card {{
			position: relative;
			z-index: 1;
			width: 100%;
			max-width: 460px;
			padding: 34px 30px 30px;
			background: rgba(14, 14, 20, 0.88);
			border: 1px solid rgba(255, 255, 255, 0.1);
			border-radius: 18px;
			box-shadow: 0 28px 70px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.05);
			backdrop-filter: blur(18px);
			-webkit-backdrop-filter: blur(18px);
			animation: cardIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
		}}
		@keyframes cardIn {{
			from {{ opacity: 0; transform: translateY(16px) scale(0.98); }}
			to {{ opacity: 1; transform: translateY(0) scale(1); }}
		}}
		.brand {{
			display: flex;
			align-items: center;
			justify-content: center;
			gap: 10px;
			margin-bottom: 22px;
		}}
		.brand-mark {{
			width: 36px;
			height: 36px;
			border-radius: 8px;
			background: #050508;
			border: 1px solid #281818;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 14px;
			font-weight: 700;
			color: #FF2D2D;
		}}
		.brand-title {{
			font-size: 13px;
			font-weight: 700;
			letter-spacing: 0.12em;
			color: #FF6B6B;
		}}
		.brand-sub {{
			font-size: 11px;
			color: #5A5A6A;
			margin-top: 2px;
		}}
		.check-wrap {{
			display: flex;
			justify-content: center;
			margin-bottom: 20px;
		}}
		.check-ring {{
			width: 64px;
			height: 64px;
			border-radius: 50%;
			background: rgba(76, 175, 80, 0.12);
			border: 2px solid rgba(76, 175, 80, 0.4);
			display: flex;
			align-items: center;
			justify-content: center;
			animation: pulse 2s ease-in-out infinite;
		}}
		@keyframes pulse {{
			0%, 100% {{ box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.25); }}
			50% {{ box-shadow: 0 0 0 14px rgba(76, 175, 80, 0); }}
		}}
		.check-icon {{
			width: 32px;
			height: 32px;
			color: #6fcf97;
		}}
		.headline {{
			text-align: center;
			font-size: 22px;
			font-weight: 700;
			margin-bottom: 6px;
			color: #E8E8EC;
		}}
		.subline {{
			text-align: center;
			font-size: 13px;
			color: #9898A8;
			margin-bottom: 22px;
			line-height: 1.45;
		}}
		.user {{
			display: flex;
			align-items: center;
			gap: 16px;
			padding: 16px;
			background: #08080c;
			border: 1px solid #281818;
			border-radius: 12px;
			margin-bottom: 20px;
		}}
		.avatar-wrap {{
			position: relative;
			flex-shrink: 0;
		}}
		.avatar {{
			width: 72px;
			height: 72px;
			border-radius: 50%;
			object-fit: cover;
			border: 2px solid #FF2D2D;
			box-shadow: 0 0 20px rgba(255, 45, 45, 0.25);
		}}
		.avatar-wrap::after {{
			content: '';
			position: absolute;
			inset: -4px;
			border-radius: 50%;
			border: 1px solid rgba(255, 107, 107, 0.35);
			pointer-events: none;
		}}
		.user-meta {{ min-width: 0; }}
		.user-name {{
			font-size: 18px;
			font-weight: 700;
			color: #E8E8EC;
			margin-bottom: 4px;
			word-break: break-word;
		}}
		.user-id {{
			font-size: 12px;
			color: #5A5A6A;
			font-variant-numeric: tabular-nums;
		}}
		.badge {{
			display: inline-flex;
			align-items: center;
			gap: 6px;
			padding: 6px 12px;
			border-radius: 999px;
			background: rgba(255, 45, 45, 0.15);
			border: 1px solid rgba(255, 45, 45, 0.35);
			color: #FF6B6B;
			font-size: 12px;
			font-weight: 600;
			margin: 0 auto 18px;
		}}
		.badge-dot {{
			width: 6px;
			height: 6px;
			border-radius: 50%;
			background: #FF2D2D;
			animation: blink 1.2s ease-in-out infinite;
		}}
		@keyframes blink {{
			0%, 100% {{ opacity: 1; }}
			50% {{ opacity: 0.35; }}
		}}
		.countdown {{
			text-align: center;
			font-size: 12px;
			color: #5A5A6A;
			margin-bottom: 18px;
		}}
		.countdown strong {{ color: #9898A8; }}
		.actions {{
			display: flex;
			gap: 10px;
			flex-wrap: wrap;
			justify-content: center;
		}}
		.btn {{
			display: inline-flex;
			align-items: center;
			justify-content: center;
			padding: 11px 18px;
			border-radius: 8px;
			font-size: 13px;
			font-weight: 600;
			text-decoration: none;
			cursor: pointer;
			border: 1px solid #281818;
			background: #14141c;
			color: #E8E8EC;
			transition: opacity 0.15s, transform 0.15s;
		}}
		.btn:hover {{ opacity: 0.92; transform: translateY(-1px); }}
		.btn-primary {{
			background: #FF2D2D;
			border-color: #FF2D2D;
			color: #fff;
			box-shadow: 0 4px 16px rgba(255, 45, 45, 0.35);
		}}
		.footer {{
			margin-top: 18px;
			text-align: center;
			font-size: 11px;
			color: #5A5A6A;
		}}
	</style>
</head>
<body>
	<div class="bg" aria-hidden="true"></div>
	<div class="bg-grid" aria-hidden="true"></div>
	<div class="orb orb-1" aria-hidden="true"></div>
	<div class="orb orb-2" aria-hidden="true"></div>

	<main class="card">
		<div class="brand">
			<div class="brand-mark">SR</div>
			<div>
				<div class="brand-title">SABR RUST</div>
				<div class="brand-sub">Launcher</div>
			</div>
		</div>

		<div class="check-wrap">
			<div class="check-ring">
				<svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M20 6L9 17l-5-5"/>
				</svg>
			</div>
		</div>

		<h1 class="headline">Вход выполнен</h1>
		<p class="subline">Steam-аккаунт привязан. Вернитесь в лаунчер — авторизация продолжится автоматически.</p>

		<div class="user">
			<div class="avatar-wrap">
				<img class="avatar" src="{safe_avatar}" alt="" onerror="this.src='{fallback_avatar}'">
			</div>
			<div class="user-meta">
				<div class="user-name">{safe_name}</div>
				<div class="user-id">Steam ID: {safe_id}</div>
			</div>
		</div>

		<div style="text-align:center">
			<span class="badge"><span class="badge-dot"></span> Сессия сохранена</span>
		</div>

		<p class="countdown">Вкладку можно закрыть. Переход в Steam через <strong><span id="t">8</span> сек.</strong></p>

		<div class="actions">
			<a class="btn btn-primary" href="steam://">Вернуться в лаунчер</a>
			<button type="button" class="btn" onclick="window.close()">Закрыть вкладку</button>
		</div>

		<p class="footer">SABR RUST Launcher · Steam OpenID</p>
	</main>

	<script>
		let left = 8;
		const node = document.getElementById('t');
		const timer = setInterval(() => {{
			left -= 1;
			if (node) node.textContent = String(Math.max(left, 0));
			if (left <= 0) clearInterval(timer);
		}}, 1000);
	</script>
</body>
</html>"""
