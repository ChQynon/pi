from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET-запросов"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Бот для ухода за растениями работает!".encode('utf-8'))
    
    def do_POST(self):
        """Обработка POST-запросов"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Webhook endpoint is working! Telegram updates will be processed."
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8')) 