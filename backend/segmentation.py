from model_args import segtracker_args, sam_args, aot_args
from SegTracker import SegTracker
import numpy as np
import torch

# from tool.transfer_tools import draw_outline, draw_points
from seg_track_anything import aot_model2ckpt, tracking_objects_in_video, draw_mask


def get_click_prompt(click_stack, point):

    click_stack[0].append(point["coord"])
    click_stack[1].append(point["mode"])

    prompt = {
        "points_coord": click_stack[0],
        "points_mode": click_stack[1],
        "multimask": "True",
    }

    return prompt


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


# def undo_click_stack_and_refine_seg(
#     Seg_Tracker,
#     origin_frame,
#     click_stack,
#     aot_model,
#     long_term_mem,
#     max_len_long_term,
#     sam_gap,
#     max_obj_num,
#     points_per_side,
# ):

#     if Seg_Tracker is None:
#         return Seg_Tracker, origin_frame, [[], []]

#     print("Undo!")
#     if len(click_stack[0]) > 0:
#         click_stack[0] = click_stack[0][:-1]
#         click_stack[1] = click_stack[1][:-1]

#     if len(click_stack[0]) > 0:
#         prompt = {
#             "points_coord": click_stack[0],
#             "points_mode": click_stack[1],
#             "multimask": "True",
#         }

#         masked_frame = seg_acc_click(Seg_Tracker, prompt, origin_frame)
#         return Seg_Tracker, masked_frame, click_stack
#     else:
#         return Seg_Tracker, origin_frame, [[], []]


# def roll_back_undo_click_stack_and_refine_seg(
#     Seg_Tracker,
#     origin_frame,
#     click_stack,
#     aot_model,
#     long_term_mem,
#     max_len_long_term,
#     sam_gap,
#     max_obj_num,
#     points_per_side,
#     input_video,
#     input_img_seq,
#     frame_num,
#     refine_idx,
# ):

#     if Seg_Tracker is None:
#         return Seg_Tracker, origin_frame, [[], []]

#     print("Undo!")
#     if len(click_stack[0]) > 0:
#         click_stack[0] = click_stack[0][:-1]
#         click_stack[1] = click_stack[1][:-1]

#     if len(click_stack[0]) > 0:
#         prompt = {
#             "points_coord": click_stack[0],
#             "points_mode": click_stack[1],
#             "multimask": "True",
#         }

#         chosen_frame_show, curr_mask, ori_frame = res_by_num(
#             input_video, input_img_seq, frame_num
#         )
#         Seg_Tracker.curr_idx = refine_idx
#         predicted_mask, masked_frame = Seg_Tracker.seg_acc_click(
#             origin_frame=origin_frame,
#             coords=np.array(prompt["points_coord"]),
#             modes=np.array(prompt["points_mode"]),
#             multimask=prompt["multimask"],
#         )
#         curr_mask[curr_mask == refine_idx] = 0
#         curr_mask[predicted_mask != 0] = refine_idx
#         predicted_mask = curr_mask
#         Seg_Tracker = SegTracker_add_first_frame(
#             Seg_Tracker, origin_frame, predicted_mask
#         )
#         return Seg_Tracker, masked_frame, click_stack
#     else:
#         return Seg_Tracker, origin_frame, [[], []]


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


# def sam_click(
#     Seg_Tracker,
#     origin_frame,
#     point_mode,
#     click_stack,
#     aot_model,
#     long_term_mem,
#     max_len_long_term,
#     sam_gap,
#     max_obj_num,
#     points_per_side,
#     evt: gr.SelectData,
# ):
#     """
#     Args:
#         origin_frame: nd.array
#         click_stack: [[coordinate], [point_mode]]
#     """

#     print("Click")

#     if point_mode == "Positive":
#         point = {"coord": [evt.index[0], evt.index[1]], "mode": 1}
#     else:
#         # TODO：add everything positive points
#         point = {"coord": [evt.index[0], evt.index[1]], "mode": 0}

#     if Seg_Tracker is None:
#         Seg_Tracker, _, _, _ = init_SegTracker(
#             aot_model,
#             long_term_mem,
#             max_len_long_term,
#             sam_gap,
#             max_obj_num,
#             points_per_side,
#             origin_frame,
#         )

#     # get click prompts for sam to predict mask
#     click_prompt = get_click_prompt(click_stack, point)

#     # Refine acc to prompt
#     masked_frame = seg_acc_click(Seg_Tracker, click_prompt, origin_frame)

#     return Seg_Tracker, masked_frame, click_stack


# def roll_back_sam_click(
#     Seg_Tracker,
#     origin_frame,
#     point_mode,
#     click_stack,
#     aot_model,
#     long_term_mem,
#     max_len_long_term,
#     sam_gap,
#     max_obj_num,
#     points_per_side,
#     input_video,
#     input_img_seq,
#     frame_num,
#     refine_idx,
#     evt: gr.SelectData,
# ):
#     """
#     Args:
#         origin_frame: nd.array
#         click_stack: [[coordinate], [point_mode]]
#     """

#     print("Click")

#     if point_mode == "Positive":
#         point = {"coord": [evt.index[0], evt.index[1]], "mode": 1}
#     else:
#         # TODO：add everything positive points
#         point = {"coord": [evt.index[0], evt.index[1]], "mode": 0}

#     if Seg_Tracker is None:
#         Seg_Tracker, _, _, _ = init_SegTracker(
#             aot_model,
#             long_term_mem,
#             max_len_long_term,
#             sam_gap,
#             max_obj_num,
#             points_per_side,
#             origin_frame,
#         )

#     # get click prompts for sam to predict mask
#     prompt = get_click_prompt(click_stack, point)

#     chosen_frame_show, curr_mask, ori_frame = res_by_num(
#         input_video, input_img_seq, frame_num
#     )

#     Seg_Tracker.curr_idx = refine_idx

#     predicted_mask, masked_frame = Seg_Tracker.seg_acc_click(
#         origin_frame=origin_frame,
#         coords=np.array(prompt["points_coord"]),
#         modes=np.array(prompt["points_mode"]),
#         multimask=prompt["multimask"],
#     )
#     curr_mask[curr_mask == refine_idx] = 0
#     curr_mask[predicted_mask != 0] = refine_idx
#     predicted_mask = curr_mask

#     Seg_Tracker = SegTracker_add_first_frame(Seg_Tracker, origin_frame, predicted_mask)

#     return Seg_Tracker, masked_frame, click_stack
