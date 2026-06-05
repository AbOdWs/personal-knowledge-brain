"""
Whisper Transcription API
Runs on port 8766
Downloads audio from Telegram and transcribes using Groq Whisper.
Auto-detects language (Arabic, English, and more).
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, urllib.parse, tempfile, os


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        file_url = body.get('url')
        groq_key = body.get('key')

        try:
            # Download the audio file
            tmp = tempfile.NamedTemporaryFile(suffix='.ogg', delete=False)
            subprocess.run(['curl', '-s', '-o', tmp.name, file_url], timeout=30)

            # Send to Groq Whisper (no language specified = auto-detect)
            result = subprocess.run([
                'curl', '-s', '-X', 'POST',
                'https://api.groq.com/openai/v1/audio/transcriptions',
                '-H', f'Authorization: Bearer {groq_key}',
                '-F', f'file=@{tmp.name};type=audio/ogg;filename=voice.ogg',
                '-F', 'model=whisper-large-v3-turbo'
            ], capture_output=True, text=True, timeout=60)

            os.unlink(tmp.name)
            data = json.loads(result.stdout)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'text': data.get('text', '')}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'text': '', 'error': str(e)}).encode())

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    print('Whisper API running on port 8766')
    HTTPServer(('0.0.0.0', 8766), Handler).serve_forever()
