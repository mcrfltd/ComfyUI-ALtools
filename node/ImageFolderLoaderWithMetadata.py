import os
import torch
import numpy as np
from PIL import Image, ImageOps
import json

class ImageFolderLoaderWithMetadata:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory_path": ("STRING", {"default": ""}),
                # 將 control_after_generate 綁定到 index 欄位上
                "index": ("INT", {"default": 0, "min": 0, "max": 9999999, "step": 1, "control_after_generate": True}),
                "sort_by": (["name_ascending", "name_descending", "date_newest", "date_oldest"], {"default": "name_ascending"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("image", "mask", "pos_prompt", "neg_prompt", "current_index")
    FUNCTION = "load_image"
    # CATEGORY = "image"
    CATEGORY = "ALTOOLS"

    OUTPUT_NODE = True

    def load_image(self, directory_path, index, sort_by):
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        # 1. 篩選圖片並排序
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        files = [os.path.join(directory_path, f) for f in os.listdir(directory_path)
                 if os.path.splitext(f)[1].lower() in valid_extensions]

        if not files:
            raise FileNotFoundError(f"No valid images found in: {directory_path}")

        if sort_by == "name_ascending":
            files.sort()
        elif sort_by == "name_descending":
            files.sort(reverse=True)
        elif sort_by == "date_newest":
            files.sort(key=os.path.getmtime, reverse=True)
        elif sort_by == "date_oldest":
            files.sort(key=os.path.getmtime)

        # 防止索引溢出 (循環讀取)
        actual_index = index % len(files)
        image_path = files[actual_index]

        # 2. 讀取圖片與處理 Mask
        img = Image.open(image_path)

        # 處理圖片轉為 ComfyUI Tensor Format (B, H, W, C)
        image = ImageOps.exif_transpose(img)
        image = image.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]

        # 處理 Mask
        if 'A' in img.getbands():
            mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32)

        # 3. 解析 Metadata (自動偵測 A1111 / ComfyUI)
        pos_prompt = ""
        neg_prompt = ""

        info = img.info
        if info:
            if 'parameters' in info:
                params = info['parameters']
                pos_prompt, neg_prompt = self.parse_a1111(params)
            elif 'prompt' in info:
                pos_prompt, neg_prompt = self.parse_comfyui(info['prompt'])

        # 4. 回傳結果與預覽圖
        return {
            "ui": {
                "images": [self.get_preview_dict(image_path)]
            },
            "result": (image, mask, pos_prompt, neg_prompt, index),
        }

    def parse_a1111(self, params_text):
        pos = ""
        neg = ""
        if "Negative prompt:" in params_text:
            parts = params_text.split("Negative prompt:")
            pos = parts[0].strip()
            neg_part = parts[1]
            if "Steps:" in neg_part:
                neg = neg_part.split("Steps:")[0].strip()
            else:
                neg = neg_part.strip()
        else:
            if "Steps:" in params_text:
                pos = params_text.split("Steps:")[0].strip()
            else:
                pos = params_text.strip()
        return pos, neg

    def parse_comfyui(self, prompt_json_str):
        pos = []
        neg = []
        try:
            data = json.loads(prompt_json_str)
            for node_id, node_data in data.items():
                class_type = node_data.get("class_type", "")
                if class_type == "CLIPTextEncode":
                    text = node_data.get("inputs", {}).get("text", "")
                    if any(x in text.lower() for x in ["negative", "bad anatomy", "worst quality"]):
                        neg.append(text)
                    else:
                        pos.append(text)
        except:
            pass

        return ", ".join(pos) if pos else "ComfyUI Raw Prompt Detected", ", ".join(neg)

    def get_preview_dict(self, image_path):
        filename = os.path.basename(image_path)
        dirname = os.path.dirname(image_path)
        return {
            "filename": filename,
            "subfolder": dirname,
            "type": "absolute"
        }
