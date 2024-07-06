from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

TARGET_WIDTH = 390
TARGET_HEIGHT = 844
MAX_DURATION = 10  # Maximum duration to process in seconds
FPS = 30  # Assuming a common FPS; can be adjusted as needed

MOVIES_DIR = "../movies"
LOCAL_BACKEND_PORT = int(os.getenv("LOCAL_BACKEND_PORT", 5001))
LOCAL_HOST = os.getenv("LOCAL_HOST", "http://localhost")
SERVER = os.getenv("SERVER", "local")

if SERVER == "remote":
    device = "cuda"

    from segmentation import (
        SegTracker,
        seg_acc_click,
        segtracker_args,
        sam_args,
        aot_args,
    )

    from seg_track_anything import aot_model2ckpt, tracking_objects_in_video

    # Initialize SegTracker
    aot_model = "r50_deaotl"
    long_term_mem = 9999
    max_len_long_term = 9999
    sam_gap = 100
    max_obj_num = 255
    points_per_side = 16

    # Initialize SegTracker arguments
    segtracker_args["sam_gap"] = sam_gap
    segtracker_args["max_obj_num"] = max_obj_num
    sam_args["generator_args"]["points_per_side"] = points_per_side
    aot_args["model"] = aot_model
    aot_args["model_path"] = aot_model2ckpt[aot_model]
    aot_args["long_term_mem_gap"] = long_term_mem
    aot_args["max_len_long_term"] = max_len_long_term

    # Initialize segmentation tracker
    segtracker = SegTracker(segtracker_args, sam_args, aot_args)
    segtracker.restart_tracker()


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


def blend_mask_with_image(image, mask, color=(0, 255, 0), alpha=0.5):
    mask = mask.astype(np.uint8) * 255
    color_mask = np.zeros_like(image)
    color_mask[mask == 255] = color
    blended = cv2.addWeighted(image, 1 - alpha, color_mask, alpha, 0)
    return blended


@app.route("/segment_frame", methods=["POST"])
def segment_frame():
    data = request.get_json()
    frame_base64 = data["frame"]
    keypoints = np.array(data["keypoints"])
    labels = np.array(data["labels"])

    nparr = np.frombuffer(base64.b64decode(frame_base64), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    prompt = {
        "points_coord": keypoints,
        "points_mode": labels,
        "multimask": "True",
    }

    predicted_mask, masked_frame = segtracker.seg_acc_click(
        origin_frame=frame_rgb,
        coords=prompt["points_coord"],
        modes=prompt["points_mode"],
        multimask=prompt["multimask"],
    )
    mask = (masked_frame[:, :, 1] == 255).astype(np.uint8)
    blended_frame_bgr = blend_mask_with_image(frame_rgb, mask)

    keypoints = keypoints.astype(int)
    for (x, y), label in zip(keypoints, labels):
        color = (0, 255, 0) if label == 1 else (0, 0, 255)
        cv2.drawMarker(
            blended_frame_bgr,
            (x, y),
            color,
            markerType=cv2.MARKER_STAR,
            markerSize=20,
            thickness=2,
        )

    _, buffer_blended = cv2.imencode(".jpg", blended_frame_bgr)
    blended_frame_str = base64.b64encode(buffer_blended).decode("utf-8")

    _, buffer_mask = cv2.imencode(".png", mask)
    mask_str = base64.b64encode(buffer_mask).decode("utf-8")

    return jsonify({"blended_frame": blended_frame_str, "mask": mask_str})


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

            app.logger.info(f"Processed frame {count}/{total_frames}")

        video.release()
        app.logger.info("Video processing complete")
        return jsonify({"frames": frames, "total_frames": total_frames})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=LOCAL_BACKEND_PORT)
