
import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from PIL import Image
import numpy as np

# Lazy import to improve startup messages if dependencies are missing
YOLO = None
model = None

# Configuration
MODEL_PATH = os.environ.get("MODEL_PATH", "models/best.pt")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")
MAX_CONTENT_LENGTH_MB = float(os.environ.get("MAX_CONTENT_LENGTH_MB", "10"))  # 10 MB default
CONF_DEFAULT = float(os.environ.get("CONF_DEFAULT", "0.25"))
IOU_DEFAULT = float(os.environ.get("IOU_DEFAULT", "0.45"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = int(MAX_CONTENT_LENGTH_MB * 1024 * 1024)

def load_model():
    global YOLO, model
    if model is not None:
        return model
    try:
        from ultralytics import YOLO as _YOLO
        YOLO = _YOLO
    except Exception as e:
        raise RuntimeError(f"Failed to import ultralytics. Make sure dependencies are installed. Details: {e}")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Place your trained model there or set MODEL_PATH env var."
        )
    try:
        _model = YOLO(MODEL_PATH)
        # ensure CPU for wide compatibility
        try:
            _model.to("cpu")
        except Exception:
            pass
        return _model
    except Exception as e:
        raise RuntimeError(f"Error loading YOLO model from {MODEL_PATH}: {e}")

def allowed_file(filename):
    ALLOWED = {"png","jpg","jpeg","webp","bmp"}
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED

@app.route("/health")
def health():
    # simple health check for deployments
    ok = os.path.exists(MODEL_PATH)
    return jsonify({"ok": ok, "model_path": MODEL_PATH})

@app.route("/", methods=["GET"])
def index():
    model_exists = os.path.exists(MODEL_PATH)
    return render_template("index.html", model_exists=model_exists, model_path=MODEL_PATH, conf_default=CONF_DEFAULT, iou_default=IOU_DEFAULT)

def _predict_on_path(img_path, conf, iou):
    _model = load_model()
    # Run prediction
    results = _model.predict(source=img_path, conf=conf, iou=iou, device="cpu", imgsz=640, verbose=False)
    r0 = results[0]
    # Build detections JSON
    dets = []
    names = r0.names if hasattr(r0, "names") else {}
    if getattr(r0, "boxes", None) is not None and getattr(r0.boxes, "data", None) is not None:
        xyxy = r0.boxes.xyxy.cpu().numpy() if hasattr(r0.boxes, "xyxy") else np.zeros((0,4))
        confs = r0.boxes.conf.cpu().numpy() if hasattr(r0.boxes, "conf") else np.zeros((0,))
        clss  = r0.boxes.cls.cpu().numpy() if hasattr(r0.boxes, "cls") else np.zeros((0,))
        for i in range(len(confs)):
            label = names.get(int(clss[i]), str(int(clss[i])))
            dets.append({
                "label": label,
                "confidence": float(confs[i]),
                "box": [float(x) for x in xyxy[i].tolist()]  # [x1,y1,x2,y2]
            })

    # Render annotated image (as ndarray)
    annotated = r0.plot()
    # Save to OUTPUT_DIR with uuid
    out_id = uuid.uuid4().hex
    out_filename = f"{out_id}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    # Save using PIL to avoid OpenCV GUI deps
    Image.fromarray(annotated).save(out_path, format="JPEG", quality=92)
    return out_filename, dets

@app.route("/predict", methods=["POST"])
def predict():
    # Web form submission: returns an HTML result page
    if "image" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))
    file = request.files["image"]
    if file.filename == "":
        flash("Please choose an image to upload.")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload png/jpg/jpeg/webp/bmp.")
        return redirect(url_for("index"))

    # Save upload
    uid = uuid.uuid4().hex
    ext = file.filename.rsplit(".",1)[1].lower()
    up_name = f"{uid}.{ext}"
    up_path = os.path.join(UPLOAD_DIR, up_name)
    file.save(up_path)

    # Get params
    try:
        conf = float(request.form.get("conf", CONF_DEFAULT))
    except Exception:
        conf = CONF_DEFAULT
    try:
        iou = float(request.form.get("iou", IOU_DEFAULT))
    except Exception:
        iou = IOU_DEFAULT

    try:
        out_filename, dets = _predict_on_path(up_path, conf, iou)
    except Exception as e:
        flash(f"Prediction failed: {e}")
        return redirect(url_for("index"))

    return render_template("result.html",
                           input_image=url_for("uploaded_file", filename=up_name),
                           output_image=url_for("output_file", filename=out_filename),
                           detections=dets,
                           conf=conf, iou=iou)

@app.route("/api/predict", methods=["POST"])
def api_predict():
    # JSON API: returns only JSON payload (and a URL to the annotated image)
    if "image" not in request.files:
        return jsonify({"error": "missing file 'image'"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "unsupported file type"}), 400

    uid = uuid.uuid4().hex
    ext = file.filename.rsplit(".",1)[1].lower()
    up_name = f"{uid}.{ext}"
    up_path = os.path.join(UPLOAD_DIR, up_name)
    file.save(up_path)

    conf = float(request.form.get("conf", CONF_DEFAULT))
    iou  = float(request.form.get("iou", IOU_DEFAULT))

    try:
        out_filename, dets = _predict_on_path(up_path, conf, iou)
    except Exception as e:
        return jsonify({"error": f"prediction failed: {e}"}), 500

    out_url = url_for("output_file", filename=out_filename, _external=True)
    return jsonify({
        "detections": dets,
        "conf": conf, "iou": iou,
        "annotated_image_url": out_url
    })

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/outputs/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
