# PAWNOVA

Project Flask phẳng, không dùng thư mục con. Toàn bộ giao diện HTML, CSS, JavaScript, public route, API route và admin route nằm trong `app.py`. Logic database, seed 6 game/11 bàn, parser, engine và access/device lock nằm trong `core.py`.

## File

- `app.py`: web app, UI, API, admin, activation page.
- `core.py`: SQLite WAL, seed, parser, engine, API key/device lock.
- `worker.py`: scraper upstream chạy mỗi 60 giây.
- `healthcheck.py`: cron kiểm tra dữ liệu.
- `requirements.txt`: dependencies.
- `render.yaml`: Render Free preview.
- `render.paid.yaml`: cấu hình production có worker/cron/disk.
- `.env.example`, `.gitignore`.

## Chạy local

```bash
pip install -r requirements.txt
python app.py
```

Mở `http://localhost:5000`.

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app --workers 1 --bind 0.0.0.0:$PORT
```

Không có thư mục `templates`, `static`, `routes` và không có file `.zio`.
