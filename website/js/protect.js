(function () {
	"use strict";

	var blockedKeys = { 123: true, 73: true, 74: true, 67: true, 85: true, 83: true };

	function isAllowedTarget(el) {
		if (!el || !el.closest) return false;
		return !!(
			el.closest(".modal-body") ||
			el.closest(".selectable") ||
			el.closest(".allow-drag") ||
			el.closest(".lightbox")
		);
	}

	document.addEventListener("contextmenu", function (e) {
		if (isAllowedTarget(e.target)) return;
		e.preventDefault();
	});

	document.addEventListener("dragstart", function (e) {
		if (e.target && e.target.closest && e.target.closest(".allow-drag")) return;
		e.preventDefault();
	});

	document.addEventListener("selectstart", function (e) {
		if (isAllowedTarget(e.target)) return;
		var tag = (e.target && e.target.tagName) || "";
		if (tag === "INPUT" || tag === "TEXTAREA" || tag === "BUTTON" || tag === "A") return;
		if (e.target && e.target.closest && e.target.closest("button, a, .btn")) return;
		e.preventDefault();
	});

	document.addEventListener("keydown", function (e) {
		if (e.key === "F12") {
			e.preventDefault();
			return false;
		}
		if (e.ctrlKey && e.shiftKey && blockedKeys[e.keyCode]) {
			e.preventDefault();
			return false;
		}
		if (e.ctrlKey && !e.shiftKey && (e.keyCode === 85 || e.keyCode === 83)) {
			if (isAllowedTarget(e.target)) return;
			e.preventDefault();
			return false;
		}
	});

	document.querySelectorAll("img:not(.allow-drag)").forEach(function (img) {
		img.setAttribute("draggable", "false");
	});
})();
