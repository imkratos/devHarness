"""本机任务清单演示服务。"""
import argparse
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_body(status, 'application/json; charset=utf-8', body)

    def send_body(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def payload(self):
        if self.headers.get_content_type() != 'application/json':
            self.reply(415, {'error': '需要 JSON 请求'})
            return None
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 16384:
                raise ValueError
            data = json.loads(self.rfile.read(size).decode())
            if not isinstance(data, dict):
                raise ValueError
            return data
        except ValueError:
            self.reply(400, {'error': '无效的 JSON 请求'})
            return None

    def do_GET(self):
        if self.path == '/':
            self.send_body(200, 'text/html; charset=utf-8', self.server.page)
        elif self.path == '/api/tasks':
            with closing(sqlite3.connect(self.server.db)) as db:
                rows = db.execute('SELECT id, title, done FROM tasks ORDER BY id')
                tasks = [dict(id=i, title=t, done=bool(d)) for i, t, d in rows]
            self.reply(200, {'stage': self.server.stage, 'tasks': tasks})
        else:
            self.reply(404, {'error': '路径不存在'})

    def do_POST(self):
        if self.path != '/api/tasks' or self.server.stage == 'M0':
            return self.reply(404, {'error': '路径不存在'})
        data = self.payload()
        if data is None:
            return
        title = data.get('title')
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
            return self.reply(400, {'error': '请输入 1 至 200 字的任务名称'})
        with closing(sqlite3.connect(self.server.db)) as db, db:
            cursor = db.execute('INSERT INTO tasks(title) VALUES (?)', (title.strip(),))
        self.reply(201, {'id': cursor.lastrowid})

    def do_PATCH(self):
        match = re.fullmatch(r'/api/tasks/([1-9][0-9]*)', self.path)
        if not match or self.server.stage != 'F2':
            return self.reply(404, {'error': '路径不存在'})
        data = self.payload()
        if data is None:
            return
        done = data.get('done')
        if not isinstance(done, bool):
            return self.reply(400, {'error': '完成状态应为布尔值'})
        with closing(sqlite3.connect(self.server.db)) as db, db:
            updated = db.execute('UPDATE tasks SET done = ? WHERE id = ?', (done, match[1]))
        if not updated.rowcount:
            return self.reply(404, {'error': '任务不存在'})
        self.reply(200, {'done': done})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['M0', 'F1', 'F2'], default='F2')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--db', type=Path, default=Path('data/tasks.sqlite3'))
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(args.db)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS tasks '
                   '(id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)')
    with ThreadingHTTPServer(('127.0.0.1', args.port), Handler) as server:
        server.db = args.db
        server.stage = args.stage
        server.page = Path(__file__).with_name('index.html').read_bytes()
        print(f'http://127.0.0.1:{server.server_port}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
