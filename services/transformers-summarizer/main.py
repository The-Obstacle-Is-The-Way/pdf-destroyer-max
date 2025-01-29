import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from src.core.summarizer import SummarizerService
from src.utils.logging import setup_logging
from src.core.config import get_settings

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

summarizer = SummarizerService()

class SummarizerHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        if self.path == '/summarize':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode())
                text = request_data.get('text')
                params = request_data.get('params', {})
                
                if not text:
                    self._send_response(400, {'error': 'No text provided'})
                    return
                
                summary = summarizer.summarize_text(text, params)
                self._send_response(200, {'summary': summary})
                
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                self._send_response(500, {'error': str(e)})
        else:
            self._send_response(404, {'error': 'Not found'})

    def do_GET(self):
        if self.path == '/health':
            health_info = {
                'status': 'healthy',
                'model_loaded': summarizer.is_model_loaded(),
                'gpu_available': summarizer.is_gpu_available()
            }
            self._send_response(200, health_info)
        else:
            self._send_response(404, {'error': 'Not found'})

def run_server(port=8006):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SummarizerHandler)
    logger.info(f"Starting summarizer service on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8006))
    run_server(port)