from model_args import segtracker_args, sam_args, aot_args
from SegTracker import SegTracker
import numpy as np
import torch

# from tool.transfer_tools import draw_outline, draw_points
from seg_track_anything import aot_model2ckpt


def SegTracker_add_first_frame(Seg_Tracker, origin_frame, predicted_mask):
    with torch.cuda.amp.autocast():
        # Reset the first frame's mask
        frame_idx = 0
        Seg_Tracker.restart_tracker()
        Seg_Tracker.add_reference(origin_frame, predicted_mask, frame_idx)
        Seg_Tracker.first_frame_mask = predicted_mask

    return Seg_Tracker


def init_SegTracker(
    aot_model,
    long_term_mem,
    max_len_long_term,
    sam_gap,
    max_obj_num,
    points_per_side,
    origin_frame,
):

    if origin_frame is None:
        return None, origin_frame, [[], []], ""

    # reset aot args
    aot_args["model"] = aot_model
    aot_args["model_path"] = aot_model2ckpt[aot_model]
    aot_args["long_term_mem_gap"] = long_term_mem
    aot_args["max_len_long_term"] = max_len_long_term
    # reset sam args
    segtracker_args["sam_gap"] = sam_gap
    segtracker_args["max_obj_num"] = max_obj_num
    sam_args["generator_args"]["points_per_side"] = points_per_side

    Seg_Tracker = SegTracker(segtracker_args, sam_args, aot_args)
    Seg_Tracker.restart_tracker()

    return Seg_Tracker, origin_frame, [[], []], ""


def seg_acc_click(Seg_Tracker, prompt, origin_frame):
    # seg acc to click
    predicted_mask, masked_frame = Seg_Tracker.seg_acc_click(
        origin_frame=origin_frame,
        coords=np.array(prompt["points_coord"]),
        modes=np.array(prompt["points_mode"]),
        multimask=prompt["multimask"],
    )

    Seg_Tracker = SegTracker_add_first_frame(Seg_Tracker, origin_frame, predicted_mask)

    return masked_frame
