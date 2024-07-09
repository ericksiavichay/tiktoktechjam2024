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


def inpaint(
    img,
    mask,
    text_prompt: str,
    negative_prompt="",
    height=512,
    width=512,
    guidance_scale=7.5,
    strength=1.0,
    num_inference_steps=50,
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
        pipe(
            prompt=text_prompt,
            image=img,
            mask_image=mask,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
            guidance_scale=guidance_scale,
            strength=strength,
            num_inference_steps=num_inference_steps,
            output_type="pil",
        ).images[0]
        # .cpu()
        # .numpy()
    )
    return img_filled
