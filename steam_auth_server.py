#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam OpenID Callback Server
Сервер для получения callback от Steam при авторизации через OpenID
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import json
import threading
import time
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

from steam_auth_success_page import render_auth_success_html

# Порт для Steam callback сервера
STEAM_AUTH_PORT = int(os.environ.get('STEAM_AUTH_PORT', '5000'))
# Хост бинда (для сервера за nginx обычно 127.0.0.1, для прямого запуска можно 0.0.0.0)
STEAM_AUTH_HOST = os.environ.get('STEAM_AUTH_HOST', '0.0.0.0')
# Публичный домен сервера Steam-авторизации
STEAM_AUTH_DOMAIN = os.environ.get('STEAM_AUTH_DOMAIN', 'launch-serversteamauth.ru').strip()
# Явный публичный base URL (если задан, приоритетнее host/proto из заголовков)
STEAM_AUTH_PUBLIC_URL = os.environ.get('STEAM_AUTH_PUBLIC_URL', 'https://launch-serversteamauth.ru').strip().rstrip('/')
# URL основного сервера для отправки информации об авторизации
MAIN_SERVER_URL = os.environ.get('MAIN_SERVER_URL', 'http://rust.blue-hosting.ru:10006')

# Steam Auth Session Storage (временное хранилище сессий)
steam_auth_sessions = {}
steam_auth_lock = threading.Lock()

class SteamAuthHandler(BaseHTTPRequestHandler):
	"""Обработчик HTTP запросов для Steam OpenID callback"""

	def _build_public_base_url(self):
		"""Строит публичный base URL для callback (домен, а не localhost)."""
		if STEAM_AUTH_PUBLIC_URL:
			return STEAM_AUTH_PUBLIC_URL
		host = (self.headers.get('X-Forwarded-Host') or self.headers.get('Host') or STEAM_AUTH_DOMAIN or '').strip()
		proto = (self.headers.get('X-Forwarded-Proto') or '').strip().lower()
		if proto not in ('http', 'https'):
			proto = 'https' if host and ':443' in host else 'http'
		if not host:
			host = f"{STEAM_AUTH_DOMAIN}:{STEAM_AUTH_PORT}" if STEAM_AUTH_DOMAIN else f"localhost:{STEAM_AUTH_PORT}"
		return f"{proto}://{host}"
	
	def get_steam_profile(self, steam_id):
		"""Получает информацию о профиле Steam"""
		try:
			xml_url = f"https://steamcommunity.com/profiles/{steam_id}/?xml=1"
			with urllib.request.urlopen(xml_url, timeout=5) as response:
				xml_data = response.read().decode('utf-8')
			
			# Парсим XML
			root = ET.fromstring(xml_data)
			steam_id_elem = root.find('steamID')
			avatar_full_elem = root.find('avatarFull')
			
			name = steam_id_elem.text if steam_id_elem is not None and steam_id_elem.text else "Unknown"
			avatar_url = avatar_full_elem.text if avatar_full_elem is not None and avatar_full_elem.text else ""
			
			return name, avatar_url
		except Exception as e:
			print(f"[Steam Auth] Ошибка получения профиля: {e}")
			return "Unknown", ""
	
	def extract_steam_id(self, callback_url):
		"""Извлекает Steam ID из callback URL"""
		try:
			parsed = urlparse(callback_url)
			params = parse_qs(parsed.query)
			claimed_id = params.get('openid.claimed_id', [None])[0]
			if claimed_id:
				# Декодируем URL, если нужно
				claimed_id = unquote(claimed_id)
				# Формат: https://steamcommunity.com/openid/id/76561198012345678
				match = re.search(r'/id/(\d+)', claimed_id)
				if match:
					return match.group(1)
		except Exception as e:
			print(f"[Steam Auth] Ошибка извлечения Steam ID: {e}")
		return None
	
	def do_GET(self):
		"""Обработка GET запросов"""
		parsed_path = urlparse(self.path)
		
		if parsed_path.path in ('/auth', '/auth/steam'):
			# Получаем параметры из URL
			query_params = parse_qs(parsed_path.query)
			session_id = query_params.get('session', [None])[0]
			
			# Сохраняем callback URL для использования лаунчером (включая все параметры)
			callback_url = f"{self._build_public_base_url()}{self.path}"
			
			print(f"[Steam Auth Server] Received callback: {callback_url}")
			print(f"[Steam Auth Server] Session ID: {session_id}")
			
			if session_id:
				# Сохраняем callback URL локально (на случай, если основной сервер недоступен)
				with steam_auth_lock:
					steam_auth_sessions[session_id] = {
						'callback_url': callback_url,
						'timestamp': time.time()
					}
				print(f"[Steam Auth Server] Session saved locally: {session_id}")
				
				# Отправляем информацию на основной сервер
				try:
					callback_data = {
						'session_id': session_id,
						'status': 'success',
						'callback_url': callback_url
					}
					callback_json = json.dumps(callback_data)
					callback_bytes = callback_json.encode('utf-8')
					
					main_server_endpoint = f"{MAIN_SERVER_URL}/api/steam-auth/callback"
					req = urllib.request.Request(
						main_server_endpoint,
						data=callback_bytes,
						headers={'Content-Type': 'application/json'},
						method='POST'
					)
					
					with urllib.request.urlopen(req, timeout=2) as response:
						result = response.read().decode('utf-8')
						print(f"[Steam Auth Server] Sent callback to main server: {result}")
				except Exception as e:
					print(f"[Steam Auth Server] WARNING: Failed to send callback to main server: {e}")
					# Продолжаем работу - локальное хранилище все равно есть
			else:
				print(f"[Steam Auth Server] WARNING: No session ID in callback!")
			
			# Пытаемся извлечь Steam ID и получить информацию о профиле
			steam_id = self.extract_steam_id(callback_url)
			steam_name = "Пользователь"
			avatar_url = ""
			
			if steam_id:
				steam_name, avatar_url = self.get_steam_profile(steam_id)
			
			# Если аватар не найден, используем дефолтный
			if not avatar_url:
				avatar_url = "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"
			
			html_response = render_auth_success_html(steam_name, steam_id, avatar_url)
			
			try:
				self.send_response(200)
				self.send_header('Content-type', 'text/html; charset=utf-8')
				self.end_headers()
				self.wfile.write(html_response.encode('utf-8'))
			except (ConnectionAbortedError, BrokenPipeError, OSError):
				# Клиент закрыл соединение до отправки ответа - это нормально
				pass
		elif parsed_path.path == '/api/steam-auth/status':
			# API endpoint для проверки статуса авторизации
			query_params = parse_qs(parsed_path.query)
			session_id = query_params.get('session', [None])[0]
			
			print(f"[Steam Auth Server] Status check request for session: {session_id}")
			
			if not session_id:
				print(f"[Steam Auth Server] ERROR: No session ID provided")
				try:
					self.send_response(400)
					self.send_header('Content-type', 'application/json')
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					response = json.dumps({"success": False, "error": "Session ID required"})
					self.wfile.write(response.encode('utf-8'))
				except (ConnectionAbortedError, BrokenPipeError, OSError):
					# Клиент закрыл соединение - это нормально
					pass
				return
			
			with steam_auth_lock:
				session_data = steam_auth_sessions.get(session_id)
				
				# Удаляем старые сессии (старше 5 минут)
				current_time = time.time()
				expired_sessions = [sid for sid, data in steam_auth_sessions.items() 
									if current_time - data.get('timestamp', 0) > 300]
				for sid in expired_sessions:
					del steam_auth_sessions[sid]
					print(f"[Steam Auth Server] Removed expired session: {sid}")
			
			if session_data:
				callback_url = session_data['callback_url']
				print(f"[Steam Auth Server] Found session, returning callback URL: {callback_url}")
				try:
					self.send_response(200)
					self.send_header('Content-type', 'application/json')
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					response = json.dumps({
						"success": True,
						"status": "success",
						"callback_url": callback_url
					})
					self.wfile.write(response.encode('utf-8'))
				except (ConnectionAbortedError, BrokenPipeError, OSError):
					# Клиент закрыл соединение до отправки ответа - это нормально
					pass
				# НЕ удаляем сессию сразу - лаунчер может запросить несколько раз
				# Сессия будет удалена автоматически через 5 минут или после обработки
			else:
				print(f"[Steam Auth Server] Session not found. Available sessions: {list(steam_auth_sessions.keys())}")
				try:
					self.send_response(200)
					self.send_header('Content-type', 'application/json')
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					response = json.dumps({"success": False})
					self.wfile.write(response.encode('utf-8'))
				except (ConnectionAbortedError, BrokenPipeError, OSError):
					# Клиент закрыл соединение - это нормально
					pass
		elif parsed_path.path == '/health':
			# Простой health-check endpoint для проверки, что сервер запущен
			try:
				self.send_response(200)
				self.send_header('Content-type', 'application/json')
				self.send_header('Access-Control-Allow-Origin', '*')
				self.end_headers()
				response = json.dumps({
					"ok": True,
					"timestamp": time.time()
				})
				self.wfile.write(response.encode('utf-8'))
			except (ConnectionAbortedError, BrokenPipeError, OSError):
				pass
		else:
			# 404 для других путей
			self.send_response(404)
			self.end_headers()

	def do_POST(self):
		"""Обработка POST запросов"""
		parsed_path = urlparse(self.path)
		if parsed_path.path == '/api/steam-auth/start':
			try:
				length = int(self.headers.get('Content-Length', '0'))
				raw = self.rfile.read(length) if length > 0 else b'{}'
				payload = json.loads(raw.decode('utf-8') or '{}')
				session_id = (payload.get('session_id') or payload.get('sessionId') or '').strip()
				if not session_id:
					self.send_response(400)
					self.send_header('Content-type', 'application/json')
					self.end_headers()
					self.wfile.write(json.dumps({"ok": False, "error": "session_id required"}).encode('utf-8'))
					return
				with steam_auth_lock:
					steam_auth_sessions[session_id] = {
						'status': 'pending',
						'timestamp': time.time()
					}
				self.send_response(200)
				self.send_header('Content-type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
				return
			except Exception as e:
				try:
					self.send_response(500)
					self.send_header('Content-type', 'application/json')
					self.end_headers()
					self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode('utf-8'))
				except Exception:
					pass
				return
		self.send_response(404)
		self.end_headers()
	
	def log_message(self, format, *args):
		"""Отключаем логирование запросов"""
		pass


class SteamAuthServer:
	"""Класс для управления Steam Auth сервером"""
	
	callback_url = None
	callback_received = False
	_server = None
	_thread = None
	
	@staticmethod
	def start_server(port=8080):
		"""Запускает HTTP сервер в отдельном потоке"""
		def run_server():
			try:
				server_address = (STEAM_AUTH_HOST, port)
				SteamAuthServer._server = HTTPServer(server_address, SteamAuthHandler)
				print(f"[Steam Auth Server] Запущен на {STEAM_AUTH_HOST}:{port}")
				if STEAM_AUTH_PUBLIC_URL:
					print(f"[Steam Auth Server] Public URL: {STEAM_AUTH_PUBLIC_URL}/auth")
				elif STEAM_AUTH_DOMAIN:
					print(f"[Steam Auth Server] Public URL: https://{STEAM_AUTH_DOMAIN}/auth")
				SteamAuthServer._server.serve_forever()
			except Exception as e:
				print(f"[Steam Auth Server] Ошибка: {e}")
		
		SteamAuthServer._thread = threading.Thread(target=run_server, daemon=True)
		SteamAuthServer._thread.start()
		if STEAM_AUTH_PUBLIC_URL:
			return f"{STEAM_AUTH_PUBLIC_URL}/auth/steam"
		if STEAM_AUTH_DOMAIN:
			return f"https://{STEAM_AUTH_DOMAIN}/auth/steam"
		return f"http://localhost:{port}/auth/steam"
	
	@staticmethod
	def stop_server():
		"""Останавливает сервер"""
		if SteamAuthServer._server:
			SteamAuthServer._server.shutdown()
			SteamAuthServer._server.server_close()
	
	@staticmethod
	def wait_for_callback(timeout=300):
		"""Ожидает получения callback от Steam"""
		start_time = time.time()
		while not SteamAuthServer.callback_received:
			if time.time() - start_time > timeout:
				return None
			time.sleep(0.1)
		return SteamAuthServer.callback_url


def main():
	"""Основная функция для запуска сервера"""
	port = STEAM_AUTH_PORT
	print(f"[Steam Auth Server] Запуск сервера на порту {port}...")
	
	try:
		server_address = (STEAM_AUTH_HOST, port)
		httpd = HTTPServer(server_address, SteamAuthHandler)
		print(f"[Steam Auth Server] Сервер запущен: {STEAM_AUTH_HOST}:{port}")
		if STEAM_AUTH_PUBLIC_URL:
			print(f"[Steam Auth Server] Public URL: {STEAM_AUTH_PUBLIC_URL}/auth")
		elif STEAM_AUTH_DOMAIN:
			print(f"[Steam Auth Server] Public URL: https://{STEAM_AUTH_DOMAIN}/auth")
		print("[Steam Auth Server] Ожидание callback от Steam...")
		print("[Steam Auth Server] Нажмите Ctrl+C для остановки")
		httpd.serve_forever()
	except KeyboardInterrupt:
		print("\n[Steam Auth Server] Остановка сервера...")
		httpd.shutdown()
	except OSError as e:
		if e.errno == 10048:  # Port already in use
			print(f"[Steam Auth Server] Ошибка: Порт {port} уже занят!")
			print(f"[Steam Auth Server] Попробуйте изменить порт через переменную окружения STEAM_AUTH_PORT")
		else:
			print(f"[Steam Auth Server] Ошибка: {e}")
		sys.exit(1)
	except Exception as e:
		print(f"[Steam Auth Server] Критическая ошибка: {e}")
		sys.exit(1)


if __name__ == '__main__':
	main()
