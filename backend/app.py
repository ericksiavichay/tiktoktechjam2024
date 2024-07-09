from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import base64
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import PIL.Image as Image
import multiprocessing
from multiprocessing import set_start_method


load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

TARGET_WIDTH = 8 * 25
TARGET_HEIGHT = 8 * 56
MAX_DURATION = 10  # Maximum duration to process in seconds
FPS = 25  # Assuming a common FPS; can be adjusted as needed

MOVIES_DIR = "../movies"
LOCAL_BACKEND_PORT = int(os.getenv("LOCAL_BACKEND_PORT", 5001))
LOCAL_HOST = os.getenv("LOCAL_HOST", "http://localhost")
REMOTE_HOST = os.getenv("REMOTE_HOST", None)
SERVER = os.getenv("SERVER", "local")

if SERVER == "remote":
    device = "cuda"
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    # Initialize inpainting pipeline
    from inpaint import inpaint

else:
    device = "cpu"
    from ultralytics import FastSAM
    from ultralytics.models.fastsam import FastSAMPrompt

    app.logger.info("Loading FastSAM model")
    model = FastSAM("FastSAM-s.pt")


def format_shape(shape):
    # coverts shape to nearest multiple of 8
    return (shape[0] // 8) * 8, (shape[1] // 8) * 8


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

    return cropped_frame


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
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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


@app.route("/inpaint_video_masks", methods=["POST"])
def inpaint_video_masks():
    print("Loading payload in inpaint_video_masks")
    data = request.get_json()
    print("Finished loading payload in inpaint_video_masks")
    masks = data["masks"]
    masks = [np.array(mask).astype(np.uint8) for mask in masks]
    images = data["images"]
    images = [np.array(image).astype(np.uint8) for image in images]

    prompt = data["prompt"]
    negative_prompt = data["negative_prompt"]
    guidance = data["guidance"]
    strength = data["strength"]
    iterations = data["iterations"]

    H, W = masks[0].shape

    inpainted_frames = []
    for i, (image, mask) in enumerate(zip(images, masks)):
        print(f"Processing Inpainted Frame [{i+1}/{len(images)}]")
        inpainted_frame = inpaint(
            image, mask, prompt, negative_prompt, H, W, guidance, strength, iterations
        )
        inpainted_frames.append(inpainted_frame)

    return jsonify({"inpainted_frames": inpainted_frames}), 200


@app.route("/inpaint_video/<filename>", methods=["POST"])
def inpaint_video(filename):

    data = request.get_json()
    prompt = data["prompt"]
    negative_prompt = data["negative_prompt"]
    guidance = data["guidance"]
    strength = data["strength"]
    num_inference_steps = data["iterations"]
    mask_source = MOVIES_DIR + "/" + filename
    image_source = MOVIES_DIR + "/" + "original_" + filename.split("segmented_")[-1]

    payload = {
        "images": [],
        "masks": [],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "guidance": guidance,
        "strength": strength,
        "num_inference_steps": num_inference_steps,
        "iterations": num_inference_steps,
    }

    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out_path = MOVIES_DIR + "/" + "inpaint_" + filename
    out = None

    video = cv2.VideoCapture(mask_source)
    if not video.isOpened():
        return jsonify({"error": "Error opening video file"}), 400
    frame_count = 1
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        if not out:
            h, w, _ = frame.shape
            out = cv2.VideoWriter(out_path, fourcc, FPS, (w, h), isColor=True)
        # Get the mask as a grayscale image
        from pdb import set_trace

        set_trace()
        mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        payload["masks"].append(mask.tolist())
        frame_count += 1
        print(f"Processing Frame [{frame_count}]")
    video.release()

    video = cv2.VideoCapture(image_source)
    if not video.isOpened():
        return jsonify({"error": "Error opening video file"}), 400

    frame_count = 1
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        payload["images"].append(image.tolist())
        frame_count += 1
        print(f"Processing Frame [{frame_count}]")
    video.release()

    try:
        batch_size = 4
        for i in range(0, len(payload["images"]), batch_size):
            print(
                f"Processing batch [{i//batch_size+1}/{len(payload['images'])//batch_size}]"
            )
            batch = {
                "images": payload["images"][i : i + batch_size],
                "masks": payload["masks"][i : i + batch_size],
                "prompt": payload["prompt"],
                "negative_prompt": payload["negative_prompt"],
                "guidance": payload["guidance"],
                "strength": payload["strength"],
                "num_inference_steps": payload["num_inference_steps"],
                "iterations": payload["iterations"],
            }
            response = requests.post(
                f"{REMOTE_HOST}/inpaint_video_masks",
                json=batch,
            )
            response.raise_for_status()
            batch_inpaints = response.json()["inpainted_frames"]
            from pdb import set_trace

            set_trace()

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    out.release()
    cv2.destroyAllWindows()

    return jsonify({"out_path": out_path})


@app.route("/segment_frame", methods=["POST"])
def segment_frame():
    data = request.get_json()
    frame_base64 = data["frame"]
    segmentation_prompt = data["segmentation_prompt"]

    nparr = np.frombuffer(base64.b64decode(frame_base64), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    app.logger.info("Segmenting single frame")
    results = model(frame_rgb, device=device, imgsz=TARGET_WIDTH, stream=False)
    app.logger.info("Finished segmenting frame")
    app.logger.info("Prompting FastSAM model")
    prompt_process = FastSAMPrompt(frame_rgb, results, device=device)
    mask = (
        prompt_process.text_prompt(text=segmentation_prompt)[0]
        .masks.data[0]
        .cpu()
        .numpy()
        .astype(np.uint8)
    )

    # Resize mask to be same size as frame_rgb
    mask = cv2.resize(mask, (frame_rgb.shape[1], frame_rgb.shape[0]))

    blended_frame_bgr = blend_mask_with_image(frame_rgb, mask)

    _, buffer_blended = cv2.imencode(".jpg", blended_frame_bgr)
    blended_frame_str = base64.b64encode(buffer_blended).decode("utf-8")

    _, buffer_mask = cv2.imencode(".png", mask * 255)
    mask_str = base64.b64encode(buffer_mask).decode("utf-8")

    return jsonify({"blended_frame": blended_frame_str, "mask": mask_str})


@app.route("/segment_video/<filename>", methods=["POST"])
def segment_video(filename):
    data = request.get_json()
    segmentation_prompt = data["segmentation_prompt"]
    source = MOVIES_DIR + "/" + filename
    results = model.track(
        source, device=device, imgsz=312, conf=0.5, iou=0.9, stream=False
    )
    print("Finished segmenting video")
    prompt_process = FastSAMPrompt(source, results, device=device)
    ann = prompt_process.text_prompt(text=segmentation_prompt)

    out_path = MOVIES_DIR + "/" + "segmented_" + filename
    _, H, W = ann[0][0].masks.data.cpu().numpy().shape
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(out_path, fourcc, FPS, (W, H), isColor=False)
    for i, result in enumerate(ann):
        mask = result[0].masks.data.cpu().numpy().astype(np.uint8).squeeze(0) * 255
        print(f"Processing Mask [{i+1}/{len(ann)}], shape: {mask.shape}")
        formatted_H, formatted_W = format_shape(mask.shape)
        mask = cv2.resize(mask, (formatted_W, formatted_H))
        # ensure mask is binary of 0s and 255s
        mask[mask > 0] = 255
        out.write(mask)
    out.release()
    cv2.destroyAllWindows()

    original_out_path = MOVIES_DIR + "/" + "original_" + filename
    original_out = cv2.VideoWriter(original_out_path, fourcc, FPS, (W, H), isColor=True)
    video = cv2.VideoCapture(source)
    frame_count = 1
    while video.isOpened():
        print(f"Processing original video [{frame_count}/{len(ann)}]")
        frame_count += 1
        ret, frame = video.read()
        if not ret:
            break

        frame = cv2.resize(frame, (W, H))
        original_out.write(frame)
    original_out.release()
    video.release()

    app.logger.info("Finished segmenting video")

    return jsonify({"out_path": out_path})


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

        frame = resize_and_crop_frame(frame)
        # Encode the cropped frame as a base64 string
        _, buffer = cv2.imencode(".jpg", frame)
        frame = base64.b64encode(buffer).decode("utf-8")
        return jsonify({"thumbnail": frame})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/movies/<filename>", methods=["GET"])
def get_movie(filename):
    app.logger.info(f"Retrieving movie {filename}")
    return send_from_directory(MOVIES_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=LOCAL_BACKEND_PORT)
