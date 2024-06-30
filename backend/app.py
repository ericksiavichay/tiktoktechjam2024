from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

TARGET_WIDTH = 390
TARGET_HEIGHT = 844
MAX_DURATION = 10  # Maximum duration to process in seconds
FPS = 30  # Assuming a common FPS; can be adjusted as needed

MOVIES_DIR = "../movies"
LOCAL_BACKEND_PORT = int(os.getenv("REACT_APP_LOCAL_BACKEND_PORT", 5001))
LOCAL_HOST = os.getenv("REACT_APP_LOCAL_HOST", "http://localhost")
REMOTE_HOST = os.getenv("REACT_APP_REMOTE_HOST", "http://dummyurl.com")
SERVER = os.getenv("SERVER", "local")

if SERVER == "remote":
    from segment_anything import sam_model_registry, SamPredictor

    device = "cuda"
    sam_checkpoint = "sam_vit_h_4b8939.pth"
    model_type = "vit_h"
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    predictor = SamPredictor(sam)


def resize_and_crop_frame(frame):
    h, w, _ = frame.shape
    aspect_ratio = w / h

    if aspect_ratio > TARGET_WIDTH / TARGET_HEIGHT:
        new_height = TARGET_HEIGHT
        new_width = int(aspect_ratio * TARGET_HEIGHT)
    else:
        new_width = TARGET_WIDTH
        new_height = int(TARGET_WIDTH / aspect_ratio)

    resized_frame = cv2.resize(frame, (new_width, new_height))
    start_x = (new_width - TARGET_WIDTH) // 2
    start_y = (new_height - TARGET_HEIGHT) // 2
    cropped_frame = resized_frame[
        start_y : start_y + TARGET_HEIGHT, start_x : start_x + TARGET_WIDTH
    ]

    _, buffer = cv2.imencode(".jpg", cropped_frame)
    frame_str = base64.b64encode(buffer).decode("utf-8")
    return frame_str


@app.route("/segment_frame", methods=["POST"])
def segment_frame():
    data = request.get_json()
    frame_base64 = data["frame"]
    keypoints = np.array(data["keypoints"])
    labels = np.array(data["labels"])

    nparr = np.frombuffer(base64.b64decode(frame_base64), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    predictor.set_image(frame_rgb)

    masks, scores, logits = predictor.predict(
        point_coords=keypoints,
        point_labels=labels,
        multimask_output=False,
    )

    segmented_frame = masks[0]
    _, buffer = cv2.imencode(".jpg", segmented_frame)
    segmented_frame_str = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"segmented_frame": segmented_frame_str})


@app.route("/movies", methods=["GET"])
def list_movies():
    try:
        movies = [f for f in os.listdir(MOVIES_DIR) if f.endswith(".mp4")]
        return jsonify({"movies": movies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/movies/<filename>/thumbnail", methods=["GET"])
def get_movie_thumbnail(filename):
    try:
        video_path = os.path.join(MOVIES_DIR, filename)
        video = cv2.VideoCapture(video_path)

        if not video.isOpened():
            return jsonify({"error": "Error opening video file"}), 400

        ret, frame = video.read()
        if not ret:
            return jsonify({"error": "Error reading frame"}), 400

        resized_frame = resize_and_crop_frame(frame)
        return jsonify({"thumbnail": resized_frame})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/movies/<filename>", methods=["GET"])
def get_movie_frames(filename):
    try:
        video_path = os.path.join(MOVIES_DIR, filename)
        video = cv2.VideoCapture(video_path)

        if not video.isOpened():
            app.logger.error("Error opening video file")
            return jsonify({"error": "Error opening video file"}), 400

        frames = []
        count = 0
        total_frames = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)), MAX_DURATION * FPS)

        while video.isOpened() and count < total_frames:
            ret, frame = video.read()
            if not ret:
                break
            frame_str = resize_and_crop_frame(frame)
            frames.append(frame_str)
            count += 1

            # Log progress
            app.logger.info(f"Processed frame {count}/{total_frames}")

        video.release()
        app.logger.info("Video processing complete")
        return jsonify({"frames": frames, "total_frames": total_frames})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=LOCAL_BACKEND_PORT)
