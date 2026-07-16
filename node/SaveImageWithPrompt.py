import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import folder_paths

class SaveImageWithPrompt:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "optional": {
                "pos_prompt": ("STRING", {"default": ""}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    # CATEGORY = "image"
    CATEGORY = "ALTOOLS"

    def save_images(self, images, filename_prefix="ComfyUI", pos_prompt="", prompt=None, extra_pnginfo=None):
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = list()
        for image in images:
            height, width = image.shape[0], image.shape[1]
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo()

            # 預設參數值（防呆）
            steps = 32
            cfg = 4.0
            sampler_name = "er_sde"
            scheduler = "simple"
            seed = 0
            neg_prompt = ""

            if prompt is not None:
                for node_id, node_data in prompt.items():
                    class_type = node_data.get("class_type")

                    # 1. 抓取 KSampler 內的真實數據
                    if class_type in ["KSampler", "KSamplerAdvanced"]:
                        inputs = node_data.get("inputs", {})
                        steps = inputs.get("steps", steps)
                        cfg = inputs.get("cfg", cfg)
                        sampler_name = inputs.get("sampler_name", sampler_name)
                        scheduler = inputs.get("scheduler", scheduler)

                        s_val = inputs.get("seed")
                        if isinstance(s_val, (int, float)):
                            seed = s_val
                        elif isinstance(s_val, list) and len(s_val) > 0:
                            seed_node_id = str(s_val[0])
                            if seed_node_id in prompt:
                                seed_inputs = prompt[seed_node_id].get("inputs", {})
                                seed = seed_inputs.get("seed", seed)

                    # 2. 抓取負向提示詞 (精準比對你的 PrimitiveStringMultiline 節點)
                    elif class_type in ["CLIPTextEncode", "PrimitiveStringMultiline", "Text Multiline"]:
                        title = node_data.get("_meta", {}).get("title", "").lower()
                        # 只要標題包含 "neg" (例如你的 "Neg Prompt") 就抓取
                        if "neg" in title:
                            inputs = node_data.get("inputs", {})
                            if "text" in inputs and isinstance(inputs["text"], str):
                                neg_prompt = inputs["text"]
                            elif "value" in inputs and isinstance(inputs["value"], str):
                                neg_prompt = inputs["value"]

            # 處理 Sampler 命名相容性
            # 如果 scheduler 是 simple，WebUI 格式通常只寫常規的 sampler 名稱
            if scheduler == "simple" or scheduler == "normal":
                sampler_display = sampler_name
            else:
                sampler_display = f"{sampler_name}_{scheduler}"

            # 清理換行符號
            clean_pos = pos_prompt.strip().replace("\n", ", ")
            clean_neg = neg_prompt.strip().replace("\n", ", ") if neg_prompt else ""

            # 完美組裝 Civitai 識別格式
            civitai_format_prompt = (
                f"{clean_pos}\n"
                f"Negative prompt: {clean_neg}\n"
                f"Steps: {steps}, Sampler: {sampler_display}, CFG scale: {cfg}, Seed: {seed}, Size: {width}x{height}"
            )

            metadata.add_text("parameters", civitai_format_prompt)
            metadata.add_text("positive_prompt", pos_prompt)

            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            file = f"{filename}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return { "ui": { "images": results } }
