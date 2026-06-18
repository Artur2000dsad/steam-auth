(function () {
	"use strict";

	const HASH_TO_DOC = {
		agreements: "terms",
		rules: "rules",
		launcher_manual: "instruction",
	};

	const state = {
		config: null,
		apiBase: window.location.origin,
	};

	function $(id) {
		return document.getElementById(id);
	}

	async function fetchJson(url) {
		const res = await fetch(url, { headers: { Accept: "application/json" } });
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	}

	async function loadSiteConfig() {
		state.apiBase = window.location.origin;
		try {
			const cfg = await fetchJson(`${state.apiBase}/api/site-config`);
			state.config = cfg;
			applyLinks(cfg.urls || {});
			if (cfg.projectName) {
				document.title = `${cfg.projectName} — Официальный проект Rust`;
			}
		} catch (err) {
			console.warn("Site config fallback:", err);
			applyLinks({
				discord: "https://discord.gg/sabr-rust",
				telegram: "https://t.me/sabrrust",
				shop: "https://sabrrust.gamestores.app/",
			});
		}
	}

	function applyLinks(urls) {
		const map = [
			["nav-discord", "footer-discord", urls.discord],
			["nav-telegram", "footer-telegram", urls.telegram],
			["nav-shop", "footer-shop", urls.shop],
			["launcher-download", null, urls.launcher],
			["hero-launcher", null, "#launcher"],
		];

		map.forEach(([a, b, href]) => {
			if (!href) return;
			[a, b].filter(Boolean).forEach((id) => {
				const el = $(id);
				if (el) el.href = href;
			});
		});
	}

	function renderMetaTags(s) {
		const parts = [];
		if (s.versionDisplay) {
			const cls = s.versionClass ? ` ${escapeHtml(s.versionClass)}` : "";
			parts.push(`<span class="tag${cls}">${escapeHtml(s.versionDisplay)}</span>`);
		}
		if (s.tags) {
			s.tags.split(/[·,]/).forEach((t) => {
				const text = t.trim();
				if (text) parts.push(`<span class="tag">${escapeHtml(text)}</span>`);
			});
		}
		if (s.serverTypeLabel) {
			const label = String(s.serverTypeLabel);
			const inTags = (s.tags || "").includes(label);
			if (!inTags) parts.push(`<span class="tag">${escapeHtml(label)}</span>`);
		}
		return parts.join("");
	}

	function shortServerName(name) {
		const raw = String(name || "");
		const match = raw.match(/SABR RUST\s*№?\s*(\d+)/i);
		return match ? `SABR RUST №${match[1]}` : raw.split("|")[0].trim();
	}

	function heroMetaFromServer(s) {
		const bits = [];
		if (s.versionDisplay) bits.push(s.versionDisplay);
		if (s.tags) bits.push(...s.tags.split(/[·,]/).map((t) => t.trim()).filter(Boolean));
		const nameParts = String(s.name || "").split("|").slice(1).map((p) => p.trim()).filter(Boolean);
		if (!s.tags && nameParts.length) bits.push(...nameParts);
		return bits.join(" · ") || "Rust Server";
	}

	function updateHeroPreview(servers) {
		const rows = document.querySelectorAll("#hero-preview-servers .preview-server");
		if (!rows.length || !servers.length) return;

		servers.slice(0, 2).forEach((s, i) => {
			const row = rows[i];
			if (!row) return;
			const nameEl = row.querySelector(".preview-server-name");
			const metaEl = row.querySelector(".preview-server-meta");
			const statusEl = row.querySelector("[data-hero-status]");
			if (nameEl) nameEl.textContent = shortServerName(s.name);
			if (metaEl) metaEl.textContent = heroMetaFromServer(s);
			if (statusEl) {
				const online = !!s.online;
				statusEl.textContent = online ? "ONLINE" : "OFFLINE";
				statusEl.classList.toggle("offline", !online);
			}
		});
	}

	function escapeHtml(str) {
		return String(str)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function showToast(message) {
		const toast = $("toast");
		if (!toast) return;
		toast.textContent = message;
		toast.hidden = false;
		toast.classList.add("show");
		clearTimeout(showToast._timer);
		showToast._timer = setTimeout(() => {
			toast.classList.remove("show");
			setTimeout(() => {
				toast.hidden = true;
			}, 300);
		}, 4500);
	}

	async function copyConnect(connect) {
		if (!connect) return;
		try {
			await navigator.clipboard.writeText(`connect ${connect}`);
			showToast(`Вы успешно скопировали connect ${connect} сервера, вставьте его в консоль игры F1`);
		} catch (err) {
			const ta = document.createElement("textarea");
			ta.value = `connect ${connect}`;
			ta.style.position = "fixed";
			ta.style.left = "-9999px";
			document.body.appendChild(ta);
			ta.select();
			try {
				document.execCommand("copy");
				showToast(`Вы успешно скопировали connect ${connect} сервера, вставьте его в консоль игры F1`);
			} catch (e2) {
				showToast("Не удалось скопировать IP:PORT");
			}
			document.body.removeChild(ta);
		}
	}

	function renderServers(data) {
		const list = $("servers-list");
		if (!list) return;

		const servers = [...(data.servers || []), ...(data.partnerServers || [])];
		if (!servers.length) {
			list.innerHTML = '<div class="glass server-card"><div>Нет серверов в конфиге</div></div>';
			return;
		}

		list.innerHTML = servers
			.map((s, idx) => {
				const online = !!s.online;
				const players = Number(s.players || 0);
				const max = Number(s.maxPlayers || 0);
				const connect = (s.connect || "").trim();
				const logoUrl = s.logoUrl || "/assets/server_avatar.png";

				return `
					<article class="server-card glass">
						<div class="server-logo">
							<img class="no-drag" draggable="false" src="${escapeHtml(logoUrl)}" alt="">
						</div>
						<div>
							<div class="server-name">${escapeHtml(s.name || "Server")}</div>
							<div class="server-meta">${renderMetaTags(s)}</div>
						</div>
						<div class="server-online">
							<div class="online-count">${players}<span> / ${max}</span></div>
							<div class="status-pill ${online ? "online" : "offline"}">${online ? "ONLINE" : "OFFLINE"}</div>
						</div>
						<button type="button" class="btn btn-primary btn-copy" data-connect="${escapeHtml(connect)}">Скопировать IP:PORT</button>
					</article>
				`;
			})
			.join("");

		list.querySelectorAll(".btn-copy").forEach((btn) => {
			btn.addEventListener("click", () => copyConnect(btn.getAttribute("data-connect")));
		});

		const totalPlayers = servers.reduce((sum, s) => sum + Number(s.players || 0), 0);
		if ($("stat-servers")) $("stat-servers").textContent = String(servers.length);
		if ($("stat-online")) $("stat-online").textContent = String(totalPlayers);
		updateHeroPreview(servers);
	}

	async function loadServers() {
		try {
			const data = await fetchJson(`${state.apiBase}/api/servers?live=1`);
			renderServers(data);
		} catch (err) {
			console.warn("Servers fallback:", err);
			renderServers({ servers: [] });
		}
	}

	function setupReveal() {
		document.querySelectorAll(".reveal").forEach((node) => {
			const io = new IntersectionObserver(
				(entries) => {
					entries.forEach((e) => {
						if (e.isIntersecting) {
							e.target.classList.add("visible");
							io.unobserve(e.target);
						}
					});
				},
				{ threshold: 0.12 }
			);
			io.observe(node);
		});
	}

	function setupContactsDropdown() {
		const dropdown = $("contacts-dropdown");
		if (!dropdown) return;
		const btn = dropdown.querySelector(".nav-dropdown-btn");
		btn.addEventListener("click", (e) => {
			e.stopPropagation();
			const open = dropdown.classList.toggle("open");
			btn.setAttribute("aria-expanded", open ? "true" : "false");
		});
		document.addEventListener("click", (e) => {
			if (!dropdown.contains(e.target)) {
				dropdown.classList.remove("open");
				btn.setAttribute("aria-expanded", "false");
			}
		});
	}

	function setupModals() {
		const overlay = $("modal-overlay");
		const titleEl = $("modal-title");
		const bodyEl = $("modal-body");
		const closeBtn = $("modal-close");
		let closing = false;

		async function openModal(docId, opts) {
			opts = opts || {};
			try {
				const data = await fetchJson(`${state.apiBase}/api/content/${docId}`);
				titleEl.textContent = data.title || "Документ";
				bodyEl.innerHTML = data.content || "<p>В разработке</p>";
				overlay.hidden = false;
				requestAnimationFrame(() => overlay.classList.add("open"));
				document.body.classList.add("modal-open");
			} catch (err) {
				titleEl.textContent = "Ошибка";
				bodyEl.innerHTML = "<p>Не удалось загрузить документ.</p>";
				overlay.hidden = false;
				overlay.classList.add("open");
			}

			if (!opts.skipHash) {
				const hashKey = Object.keys(HASH_TO_DOC).find((k) => HASH_TO_DOC[k] === docId);
				if (hashKey && location.hash !== `#${hashKey}`) {
					history.pushState(null, "", `#${hashKey}`);
				}
			}
		}

		function closeModal(opts) {
			opts = opts || {};
			if (!overlay.classList.contains("open")) return;
			closing = true;
			overlay.classList.remove("open");
			document.body.classList.remove("modal-open");
			setTimeout(() => {
				overlay.hidden = true;
				bodyEl.innerHTML = "";
				closing = false;
			}, 280);

			if (!opts.skipHash) {
				const current = location.hash.replace("#", "");
				if (HASH_TO_DOC[current]) {
					history.replaceState(null, "", location.pathname + location.search);
				}
			}
		}

		function handleHash() {
			if (closing) return;
			const key = location.hash.replace("#", "");
			if (HASH_TO_DOC[key]) {
				openModal(HASH_TO_DOC[key], { skipHash: true });
				return;
			}
			if (overlay.classList.contains("open")) {
				closeModal({ skipHash: true });
			}
		}

		document.querySelectorAll("[data-modal]").forEach((el) => {
			el.addEventListener("click", (e) => {
				const docId = el.getAttribute("data-modal");
				const hashKey = Object.keys(HASH_TO_DOC).find((k) => HASH_TO_DOC[k] === docId);
				if (hashKey) {
					e.preventDefault();
					if (location.hash === `#${hashKey}`) {
						openModal(docId, { skipHash: true });
					} else {
						location.hash = hashKey;
					}
				} else {
					openModal(docId);
				}
			});
		});

		closeBtn.addEventListener("click", () => closeModal());
		overlay.addEventListener("click", (e) => {
			if (e.target === overlay) closeModal();
		});
		document.addEventListener("keydown", (e) => {
			if (e.key === "Escape" && overlay.classList.contains("open")) closeModal();
		});

		window.addEventListener("hashchange", handleHash);
		handleHash();
	}

	function setupLightbox() {
		const img = $("launcher-demo-img");
		const lightbox = $("lightbox");
		const lightboxImg = $("lightbox-img");
		const closeBtn = $("lightbox-close");
		if (!img || !lightbox) return;

		img.addEventListener("click", () => {
			lightboxImg.src = img.src;
			lightbox.hidden = false;
			requestAnimationFrame(() => lightbox.classList.add("open"));
		});

		function close() {
			lightbox.classList.remove("open");
			setTimeout(() => {
				lightbox.hidden = true;
			}, 280);
		}

		closeBtn.addEventListener("click", close);
		lightbox.addEventListener("click", (e) => {
			if (e.target === lightbox) close();
		});
		document.addEventListener("keydown", (e) => {
			if (e.key === "Escape" && lightbox.classList.contains("open")) close();
		});
	}

	function setupNav() {
		const burger = $("burger");
		const nav = $("main-nav");
		if (burger && nav) {
			burger.addEventListener("click", () => {
				const open = nav.classList.toggle("open");
				burger.setAttribute("aria-expanded", open ? "true" : "false");
			});
		}

		const sections = ["top", "launcher", "servers"];
		window.addEventListener("scroll", () => {
			const y = window.scrollY + 120;
			let current = "home";
			sections.forEach((id) => {
				const el = document.getElementById(id);
				if (el && el.offsetTop <= y) current = id === "top" ? "home" : id;
			});
			document.querySelectorAll(".nav-link[data-nav], .nav-btn[data-nav]").forEach((a) => {
				const navId = a.getAttribute("data-nav");
				if (navId) a.classList.toggle("active", navId === current);
			});
		});
	}

	function init() {
		if ($("year")) $("year").textContent = String(new Date().getFullYear());
		setupReveal();
		setupNav();
		setupContactsDropdown();
		setupModals();
		setupLightbox();
		loadSiteConfig().then(loadServers);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
