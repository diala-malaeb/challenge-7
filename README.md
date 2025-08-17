
# YOLOv8 Object Detection — Flask + Docker (ZAKA Final Project)

Minimal, production-ready Flask app that serves your trained YOLOv8 model via a web UI and JSON API.
Containerized with Docker and ready for deployment on Render, Railway, Fly.io, or any container platform.

---

## 1) Project Features

- ✅ Upload an image, get an annotated image + detections.
- ✅ JSON API at `/api/predict` for programmatic usage.
- ✅ Health endpoint at `/health` for platform checks.
- ✅ CPU-friendly Docker image (no GPU required).
- ✅ Conf/IoU sliders on the UI.

---

## 2) Where to put your model

Put your trained YOLO file at:
```
models/best.pt
```

You can rename and update the path via `MODEL_PATH` env var or in `app.py`.

---

## 3) Quickstart (Local, without Docker)

```bash
# 0) Python 3.10+ recommended

# 1) Create & activate venv (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install --upgrade pip
pip install -r requirements.txt

# 3) Place your model at models/best.pt
#    (Create the models/ folder if it doesn't exist.)

# 4) Run
export PORT=8080  # Windows: set PORT=8080
python app.py

# 5) Open: http://localhost:8080
```

---

## 4) Run with Docker (Local)

```bash
# Build the image
docker build -t yolo-flask .

# Run the container, mount your local models/ so you don't rebuild when the model changes
docker run --rm -p 8080:8080 \
  -e PORT=8080 \
  -v "$(pwd)/models:/app/models" \
  --name yolo-flask yolo-flask

# Open: http://localhost:8080
```

---

## 5) Deploy Options (Pick One)

### A) Render (Docker)

1. Push this folder to a GitHub repo.
2. On Render.com → **New** → **Web Service** → **Build from a Dockerfile**.
3. Point to your repo, keep Dockerfile defaults.
4. Set **Environment**: `Docker`, and add an env var if needed:
   - `MODEL_PATH=models/best.pt`
5. Render sets a `$PORT` env variable automatically; our CMD honors it.
6. After deploy, visit the URL Render gives you.

*(Optional)* Use `render.yaml` Blueprint instead of clicking around.

### B) Railway (Docker)

1. Create a new project and select **Deploy from GitHub**.
2. It will detect your Dockerfile automatically.
3. Ensure the `$PORT` env is set by the platform; no changes needed.
4. Add your model file to the repo under `models/` (or use persistent volumes).

### C) Hugging Face Spaces (Docker)

1. Create a **Space** → **Docker** runtime.
2. Push the repo with Dockerfile and this app.
3. Make sure the app binds to `$PORT`. Done!

### D) Any VPS / Cloud VM

```bash
git clone <your-repo>
cd yolo-flask-docker
docker build -t yolo-flask .
docker run -d -p 80:8080 -e PORT=8080 --name yolo yolo-flask
```

---

## 6) API Usage

```bash
curl -X POST "https://<your-app>/api/predict" \
    -F "image=@/path/to/image.jpg" \
    -F "conf=0.25" \
    -F "iou=0.45"
```

Response:
```json
{
  "detections": [
    {"label": "person", "confidence": 0.91, "box": [x1,y1,x2,y2]},
    ...
  ],
  "conf": 0.25,
  "iou": 0.45,
  "annotated_image_url": "https://<your-app>/outputs/<file>.jpg"
}
```

---

## 7) Environment Variables (optional)

| Name                   | Default          | Description                            |
|------------------------|------------------|----------------------------------------|
| `PORT`                 | `8080`           | Server port                            |
| `MODEL_PATH`           | `models/best.pt` | Path to YOLO model file                |
| `MAX_CONTENT_LENGTH_MB`| `10`             | Max upload size in MB                  |
| `CONF_DEFAULT`         | `0.25`           | Default confidence threshold           |
| `IOU_DEFAULT`          | `0.45`           | Default IoU threshold                  |
| `SECRET_KEY`           | `replace-me`     | Flask session secret                   |

---

## 8) Deliverables Checklist (as requested)

- **Model File(s)**: Put your trained file in `models/best.pt`. Include any needed YAML/tokenizer files if applicable.
- **Flask App Files**: `app.py`, `templates/`, `static/` (provided).
- **Dockerization Files**: `Dockerfile`, `requirements.txt`, `.dockerignore` (provided).
- **Deployment Link**: After deploying (Render/Railway/Spaces), paste your public URL into `SLIDES_LINK.txt` and your submission doc.
- **Slides Link**: Put the Google Slides URL in `SLIDES_LINK.txt` as instructed.

---

## 9) Troubleshooting

- **Model not found**: Ensure `models/best.pt` exists in your repo/container. Check `/health` endpoint.
- **Torch install issues**: We pin CPU wheels with `--extra-index-url`. If build fails, try a newer Python base image or match versions.
- **Large image errors**: Increase `MAX_CONTENT_LENGTH_MB` env var.
- **Slow cold start**: First request loads the model; subsequent requests are faster.

---

© 2025, ZAKA AI Final Project Starter
