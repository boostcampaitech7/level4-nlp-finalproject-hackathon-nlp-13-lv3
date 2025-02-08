from http.server import BaseHTTPRequestHandler, HTTPServer


class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hello World")


if __name__ == "__main__":
    server_address = ('', 30823)  # 모든 인터페이스의 8080 포트
    httpd = HTTPServer(server_address, HelloHandler)
    print("서버 실행 중... (포트 8080)")
    httpd.serve_forever()
