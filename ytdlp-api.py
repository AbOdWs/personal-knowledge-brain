"""
yt-dlp Metadata API
Runs on port 8765
Extracts video metadata (title, description, tags) from TikTok, YouTube, Instagram etc.
For YouTube, also extracts auto-generated transcripts.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, urllib.parse, os, re, tempfile

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.unquote(self.path[1:])
        try:
            # Get metadata
            result = subprocess.run(
                ['yt-dlp', '--dump-json', '--no-download', url],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)

            # Build base content from metadata
            content_parts = list(filter(None, [
                data.get('title', ''),
                data.get('description', ''),
                ' '.join(data.get('tags', [])),
                data.get('uploader', '')
            ]))
            base_content = ' | '.join(content_parts)

            # Try transcript for YouTube
            transcript_text = ''
            if 'youtube.com' in url or 'youtu.be' in url:
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        transcript_file = os.path.join(tmpdir, 'transcript')
                        subprocess.run([
                            'yt-dlp',
                            '--write-auto-sub',
                            '--skip-download',
                            '--sub-format', 'ttml',
                            '--convert-subs', 'srt',
                            '-o', transcript_file,
                            url
                        ], capture_output=True, timeout=30)

                        for f in os.listdir(tmpdir):
                            if f.endswith('.srt'):
                                with open(os.path.join(tmpdir, f), 'r') as tf:
                                    srt = tf.read()
                                lines = srt.split('\n')
                                text_lines = []
                                for line in lines:
                                    line = line.strip()
                                    if not line or line.isdigit() or '-->' in line:
                                        continue
                                    line = re.sub(r'<[^>]+>', '', line)
                                    if line and line != '[Music]':
                                        text_lines.append(line)
                                transcript_text = ' '.join(text_lines)[:3000]
                                break
                except Exception:
                    pass

            # Combine
            if transcript_text:
                final_content = base_content[:1000] + '\n\nTranscript: ' + transcript_text
            else:
                final_content = base_content[:3000]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'content': final_content}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'content': '', 'error': str(e)}).encode())

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    print('yt-dlp API running on port 8765')
    HTTPServer(('0.0.0.0', 8765), Handler).serve_forever()
