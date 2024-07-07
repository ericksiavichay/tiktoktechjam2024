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

TARGET_WIDTH = 8 * 25
TARGET_HEIGHT = 8 * 56
MAX_DURATION = 10  # Maximum duration to process in seconds
FPS = 30  # Assuming a common FPS; can be adjusted as needed

MOVIES_DIR = "../movies"
LOCAL_BACKEND_PORT = int(os.getenv("LOCAL_BACKEND_PORT", 5001))
LOCAL_HOST = os.getenv("LOCAL_HOST", "http://localhost")
SERVER = os.getenv("SERVER", "local")

FRAMES = []
SEGMENTED_FRAMES = []

if SERVER == "remote":
    device = "cuda"

    from segmentation import (
        SegTracker,
        segtracker_args,
        SegTracker_add_first_frame,
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

    # Initialize inpainting pipeline
    from inpaint import inpaint


def resize_and_crop_frame(frame):
    h, w, _ = frame.shape

    # Calculate the aspect ratio
    aspect_ratio = w / h

    # Determine new dimensions to be multiples of 8 while maintaining aspect ratio
    if aspect_ratio > (TARGET_WIDTH / TARGET_HEIGHT):
        new_height = (TARGET_HEIGHT // 8) * 8
        new_width = int(aspect_ratio * new_height) // 8 * 8
    else:
        new_width = (TARGET_WIDTH // 8) * 8
        new_height = int(new_width / aspect_ratio) // 8 * 8

    # Resize the frame to the new dimensions
    resized_frame = cv2.resize(frame, (new_width, new_height))

    # Calculate the starting coordinates for cropping to center the crop
    start_x = (new_width - TARGET_WIDTH) // 2
    start_y = (new_height - TARGET_HEIGHT) // 2

    # Crop the resized frame to the target dimensions
    cropped_frame = resized_frame[
        start_y : start_y + TARGET_HEIGHT, start_x : start_x + TARGET_WIDTH
    ]

    # Encode the cropped frame as a base64 string
    _, buffer = cv2.imencode(".jpg", cropped_frame)
    frame_str = base64.b64encode(buffer).decode("utf-8")
    return frame_str


def blend_mask_with_image(image, mask, color=(0, 255, 0), alpha=0.5):
    mask = mask.astype(np.uint8) * 255
    color_mask = np.zeros_like(image)
    color_mask[mask == 255] = color
    blended = cv2.addWeighted(image, 1 - alpha, color_mask, alpha, 0)
    return blended


@app.route("/inpaint_frame", methods=["POST"])
def inpaint_frame():
    data = request.get_json()
    frame_base64 = data["frame"]
    mask_base64 = data["mask"]
    prompt = data["prompt"]
    negative_prompt = data["negative_prompt"]
    guidance = data["guidance"]
    strength = data["strength"]
    num_inference_steps = data["iterations"]

    nparr = np.frombuffer(base64.b64decode(frame_base64), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    nparr = np.frombuffer(base64.b64decode(mask_base64), np.uint8)
    mask = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    inpainted_frame = inpaint(
        frame,
        mask,
        prompt,
        negative_prompt,
        TARGET_HEIGHT,
        TARGET_WIDTH,
        guidance,
        strength,
        num_inference_steps,
    )
    _, buffer = cv2.imencode(".png", inpainted_frame)
    inpainted_frame_str = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"inpainted_frame": inpainted_frame_str})


@app.route("/segment_frame", methods=["POST"])
def segment_frame():
    data = request.get_json()
    frame_base64 = data["frame"]
    keypoints = np.array(data["keypoints"])
    labels = np.array(data["labels"])

    nparr = np.frombuffer(base64.b64decode(frame_base64), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get the actual dimensions of the frame
    actual_height, actual_width, _ = frame.shape

    # Scale the keypoints to match the frame dimensions
    keypoints[:, 0] = keypoints[:, 0] * (actual_width / TARGET_WIDTH)
    keypoints[:, 1] = keypoints[:, 1] * (actual_height / TARGET_HEIGHT)

    interactive_mask = segtracker.sam.segment_with_click(
        frame_rgb, keypoints, labels, "True"
    )
    refined_merged_mask = segtracker.add_mask(interactive_mask)
    blended_frame_bgr = blend_mask_with_image(frame_rgb, refined_merged_mask)

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

    _, buffer_mask = cv2.imencode(".png", refined_merged_mask * 255)
    mask_str = base64.b64encode(buffer_mask).decode("utf-8")

    return jsonify({"blended_frame": blended_frame_str, "mask": mask_str})


@app.route("/segment_video", methods=["POST"])
def segment_video():
    global FRAMES
    global SEGMENTED_FRAMES

    if not FRAMES:
        return jsonify({"error": "No frames available for segmentation"}), 400

    data = request.get_json()
    if not data or "keypoints" not in data or "labels" not in data:
        print("Invalid request payload:", data)  # Debugging line
        return jsonify({"error": "Invalid request payload"}), 400

    keypoints = np.array(data["keypoints"])
    labels = np.array(data["labels"])

    print("Received keypoints:", keypoints)  # Debugging line
    print("Received labels:", labels)  # Debugging line

    try:
        init_frame = FRAMES[0]
        init_frame_rgb = cv2.cvtColor(init_frame, cv2.COLOR_BGR2RGB)

        interactive_mask = segtracker.sam.segment_with_click(
            init_frame_rgb, keypoints, labels, "True"
        )
        refined_merged_mask = segtracker.add_mask(interactive_mask)
        segtracker = SegTracker_add_first_frame(
            segtracker, init_frame_rgb, refined_merged_mask
        )

        display_segmented_frames = []
        for i, frame in enumerate(FRAMES):
            app.logger.info(f"Segmenting frame {i+1}/{len(FRAMES)}")
            if i == 0:
                pred_mask = refined_merged_mask
            else:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pred_mask = segtracker.track(frame_rgb, update_memory=True)
            SEGMENTED_FRAMES.append(pred_mask)
            _, buffer_mask = cv2.imencode(".png", pred_mask.astype(np.uint8) * 255)
            mask_str = base64.b64encode(buffer_mask).decode("utf-8")
            display_segmented_frames.append(mask_str)

        return jsonify({"segmented_frames": display_segmented_frames})
    except Exception as e:
        print("Error during segmentation:", str(e))  # Debugging line
        return jsonify({"error": str(e)}), 500


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

        global FRAMES
        FRAMES = []
        count = 0
        total_frames = min(int(video.get(cv2.CAP_PROP_FRAME_COUNT)), MAX_DURATION * FPS)

        while video.isOpened() and count < total_frames:
            ret, frame = video.read()
            if not ret:
                break
            frame_str = resize_and_crop_frame(frame)
            FRAMES.append(frame_str)
            count += 1

            app.logger.info(f"Processed frame {count}/{total_frames}")

        video.release()
        app.logger.info("Video processing complete")
        return jsonify({"frames": FRAMES, "total_frames": total_frames})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=LOCAL_BACKEND_PORT)
