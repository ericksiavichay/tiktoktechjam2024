import torch
import numpy as np
from diffusers import StableDiffusionInpaintPipeline
import PIL.Image as Image

device = "cuda"

pipe = StableDiffusionInpaintPipeline.from_single_file(
    "inpaint.safetensors",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=False,
    safety_checker=None,
    use_safetensors=True,
).to(device)


# def crop_for_filling_pre(image: np.array, mask: np.array, crop_size: int = 512):
#     # Calculate the aspect ratio of the image
#     height, width = image.shape[:2]
#     aspect_ratio = float(width) / float(height)
#     mask = masks.astype(np.uint8).squeeze(0) * 255

#     # If the shorter side is less than 512, resize the image proportionally
#     if min(height, width) < crop_size:
#         if height < width:
#             new_height = crop_size
#             new_width = int(new_height * aspect_ratio)
#         else:
#             new_width = crop_size
#             new_height = int(new_width / aspect_ratio)

#         image = cv2.resize(image, (new_width, new_height))
#         mask = cv2.resize(mask, (new_width, new_height))

#     # Find the bounding box of the mask
#     x, y, w, h = cv2.boundingRect(mask)

#     # Update the height and width of the resized image
#     height, width = image.shape[:2]

#     # # If the 512x512 square cannot cover the entire mask, resize the image accordingly
#     if w > crop_size or h > crop_size:
#         # padding to square at first
#         if height < width:
#             padding = width - height
#             image = np.pad(
#                 image,
#                 ((padding // 2, padding - padding // 2), (0, 0), (0, 0)),
#                 "constant",
#             )
#             mask = np.pad(
#                 mask, ((padding // 2, padding - padding // 2), (0, 0)), "constant"
#             )
#         else:
#             padding = height - width
#             image = np.pad(
#                 image,
#                 ((0, 0), (padding // 2, padding - padding // 2), (0, 0)),
#                 "constant",
#             )
#             mask = np.pad(
#                 mask, ((0, 0), (padding // 2, padding - padding // 2)), "constant"
#             )

#         resize_factor = crop_size / max(w, h)
#         image = cv2.resize(image, (0, 0), fx=resize_factor, fy=resize_factor)
#         mask = cv2.resize(mask, (0, 0), fx=resize_factor, fy=resize_factor)
#         x, y, w, h = cv2.boundingRect(mask)

#     # Calculate the crop coordinates
#     crop_x = min(max(x + w // 2 - crop_size // 2, 0), width - crop_size)
#     crop_y = min(max(y + h // 2 - crop_size // 2, 0), height - crop_size)

#     # Crop the image
#     cropped_image = image[crop_y : crop_y + crop_size, crop_x : crop_x + crop_size]
#     cropped_mask = mask[crop_y : crop_y + crop_size, crop_x : crop_x + crop_size]

#     return cropped_image, cropped_mask


# def crop_for_filling_post(
#     image: np.array,
#     mask: np.array,
#     filled_image: np.array,
#     crop_size: int = 512,
# ):
#     image_copy = image.copy()
#     mask_copy = mask.copy()
#     # Calculate the aspect ratio of the image
#     height, width = image.shape[:2]
#     height_ori, width_ori = height, width
#     aspect_ratio = float(width) / float(height)

#     # If the shorter side is less than 512, resize the image proportionally
#     if min(height, width) < crop_size:
#         if height < width:
#             new_height = crop_size
#             new_width = int(new_height * aspect_ratio)
#         else:
#             new_width = crop_size
#             new_height = int(new_width / aspect_ratio)

#         image = cv2.resize(image, (new_width, new_height))
#         mask = cv2.resize(mask, (new_width, new_height))

#     # Find the bounding box of the mask
#     x, y, w, h = cv2.boundingRect(mask)

#     # Update the height and width of the resized image
#     height, width = image.shape[:2]

#     # # If the 512x512 square cannot cover the entire mask, resize the image accordingly
#     if w > crop_size or h > crop_size:
#         flag_padding = True
#         # padding to square at first
#         if height < width:
#             padding = width - height
#             image = np.pad(
#                 image,
#                 ((padding // 2, padding - padding // 2), (0, 0), (0, 0)),
#                 "constant",
#             )
#             mask = np.pad(
#                 mask, ((padding // 2, padding - padding // 2), (0, 0)), "constant"
#             )
#             padding_side = "h"
#         else:
#             padding = height - width
#             image = np.pad(
#                 image,
#                 ((0, 0), (padding // 2, padding - padding // 2), (0, 0)),
#                 "constant",
#             )
#             mask = np.pad(
#                 mask, ((0, 0), (padding // 2, padding - padding // 2)), "constant"
#             )
#             padding_side = "w"

#         resize_factor = crop_size / max(w, h)
#         image = cv2.resize(image, (0, 0), fx=resize_factor, fy=resize_factor)
#         mask = cv2.resize(mask, (0, 0), fx=resize_factor, fy=resize_factor)
#         x, y, w, h = cv2.boundingRect(mask)
#     else:
#         flag_padding = False

#     # Calculate the crop coordinates
#     crop_x = min(max(x + w // 2 - crop_size // 2, 0), width - crop_size)
#     crop_y = min(max(y + h // 2 - crop_size // 2, 0), height - crop_size)

#     # Fill the image
#     image[crop_y : crop_y + crop_size, crop_x : crop_x + crop_size] = filled_image
#     if flag_padding:
#         image = cv2.resize(image, (0, 0), fx=1 / resize_factor, fy=1 / resize_factor)
#         if padding_side == "h":
#             image = image[padding // 2 : padding // 2 + height_ori, :]
#         else:
#             image = image[:, padding // 2 : padding // 2 + width_ori]

#     image = cv2.resize(image, (width_ori, height_ori))

#     image_copy[mask_copy == 255] = image[mask_copy == 255]
#     return image_copy


def inpaint(
    img: np.ndarray,
    mask: np.ndarray,
    text_prompt: str,
    negative_prompt="",
    height=512,
    width=512,
    device="cuda",
):
    # pipe = StableDiffusionInpaintPipeline.from_pretrained(
    #     # "stabilityai/stable-diffusion-2-inpainting",
    #     torch_dtype=torch.float16,
    #     low_cpu_mem_usage=False,
    #     safety_checker=None,
    # ).to(device)
    """
    img: (H, W, 3)
    mask: (H, W)
    """

    img_filled = (
        (
            pipe(
                prompt=text_prompt,
                image=Image.fromarray(img),
                mask_image=Image.fromarray(mask.astype(np.uint8)),
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                guidance_scale=12,
                strength=1.0,
                output_type="pt",
            ).images[0]
            * 255
        )
        .cpu()
        .numpy()
        .astype(np.uint8)
    ).transpose(1, 2, 0)
    return img_filled
