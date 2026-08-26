import hashlib
import json
import os
from functools import lru_cache

import folder_paths
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo


@lru_cache(maxsize=128)
def calculate_model_autov2(file_path):
    """計算模型檔案的全檔 SHA256，並傳回前 10 碼（AutoV2）"""
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:10].lower()
    except Exception as e:
        print(f"[SaveImage] 計算 SHA256 失敗 ({file_path}): {e}")
        return None


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
                "wipe_workflow": ("BOOLEAN", {"default": False}),
                "wipe_checkpoint": ("BOOLEAN", {"default": False}),
                "wipe_lora": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "pos_prompt": ("STRING", {"default": ""}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "ALTOOLS"

    def resolve_lora_path(self, lora_file_name):
        """尋找 LoRA 實體檔案路徑"""
        if not lora_file_name:
            return None
        clean_name = str(lora_file_name).strip()
        full_path = folder_paths.get_full_path("loras", clean_name)
        if not full_path and not clean_name.endswith(".safetensors"):
            full_path = folder_paths.get_full_path(
                "loras", clean_name + ".safetensors"
            )
        return full_path

    def resolve_model_path(self, model_file_name):
        """尋找 Checkpoint / UNet / Diffusion 模型實體檔案路徑"""
        if not model_file_name:
            return None
        clean_name = str(model_file_name).strip()
        for folder_type in ["checkpoints", "diffusion_models", "unet"]:
            full_path = folder_paths.get_full_path(folder_type, clean_name)
            if full_path:
                return full_path
            if not clean_name.endswith(".safetensors"):
                full_path = folder_paths.get_full_path(
                    folder_type, clean_name + ".safetensors"
                )
                if full_path:
                    return full_path
        return None

    def save_images(
        self,
        images,
        filename_prefix="ComfyUI",
        wipe_workflow=False,
        wipe_checkpoint=False,
        wipe_lora=False,
        pos_prompt="",
        prompt=None,
        extra_pnginfo=None,
    ):
        (
            full_output_folder,
            filename,
            counter,
            subfolder,
            filename_prefix,
        ) = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        lora_hashes_dict = {}
        model_name = ""
        model_hash = ""
        fallback_pos_prompt = ""

        if prompt is not None:
            for node_id, node_data in prompt.items():
                class_type = str(node_data.get("class_type", ""))
                inputs = node_data.get("inputs", {})

                # 1. 抓取 Checkpoint / Diffusion / UNet 模型名稱並計算 Hash
                if not wipe_checkpoint and not model_name:
                    ckpt_keys = ["ckpt_name", "model_name", "unet_name", "diffusion_model"]
                    raw_model_path = ""
                    for key in ckpt_keys:
                        if key in inputs:
                            val = inputs.get(key, "")
                            if val:
                                raw_model_path = str(val)
                                model_name = os.path.splitext(os.path.basename(raw_model_path))[0]
                                break

                    if not model_name and any(
                        k in class_type for k in ["CheckpointLoader", "UNETLoader", "DiffusionModel"]
                    ):
                        for key, val in inputs.items():
                            if isinstance(val, str) and any(
                                val.endswith(ext) for ext in [".safetensors", ".ckpt", ".pth", ".bin"]
                            ):
                                raw_model_path = val
                                model_name = os.path.splitext(os.path.basename(val))[0]
                                break

                    if raw_model_path:
                        full_model_path = self.resolve_model_path(raw_model_path)
                        if full_model_path:
                            model_hash = calculate_model_autov2(full_model_path) or ""

                # 2. 僅在 wipe_lora 為 False 時才執行 LoRA 搜尋與 Hash 計算
                if not wipe_lora:
                    if class_type == "AnimaMultiLoraLoader":
                        lora_data = inputs.get("lora_list_json", "")
                        lora_list = []
                        if isinstance(lora_data, str) and lora_data.strip():
                            try:
                                parsed = json.loads(lora_data)
                                if isinstance(parsed, str):
                                    parsed = json.loads(parsed)
                                if isinstance(parsed, list):
                                    lora_list = parsed
                            except Exception as e:
                                print(
                                    f"[SaveImage] AnimaMultiLoraLoader JSON 解析失敗: {e}"
                                )
                        elif isinstance(lora_data, list):
                            lora_list = lora_data

                        for item in lora_list:
                            if isinstance(item, str):
                                try:
                                    item = json.loads(item)
                                except Exception:
                                    continue

                            if isinstance(item, dict) and item.get("enabled", False):
                                raw_name = item.get("name", "")
                                if raw_name:
                                    lora_path = self.resolve_lora_path(raw_name)
                                    hash_val = calculate_model_autov2(lora_path)
                                    if hash_val:
                                        clean_name = os.path.splitext(
                                            os.path.basename(raw_name)
                                        )[0]
                                        lora_hashes_dict[clean_name] = hash_val

                    if (
                        class_type == "Power Lora Loader (rgthree)"
                        or "PowerLoraLoader" in class_type
                    ):
                        for key, val in inputs.items():
                            if isinstance(val, dict) and val.get("on", False):
                                raw_name = val.get("lora", "")
                                if raw_name:
                                    lora_path = self.resolve_lora_path(raw_name)
                                    hash_val = calculate_model_autov2(lora_path)
                                    if hash_val:
                                        clean_name = os.path.splitext(
                                            os.path.basename(raw_name)
                                        )[0]
                                        lora_hashes_dict[clean_name] = hash_val

                # 3. 若 pos_prompt 為空，從 AnimaPromptPlus 擷取標籤作為備用
                if not pos_prompt.strip() and class_type == "AnimaPromptPlus":
                    tags_keys = [
                        "quality_prompt",
                        "artist_tags",
                        "character_tags",
                        "clothing_tags",
                        "pose_tags",
                        "background_tags",
                        "extra_prompt",
                    ]
                    extracted_tags = []
                    for key in tags_keys:
                        val = inputs.get(key, "")
                        if isinstance(val, str) and val.strip():
                            extracted_tags.append(val.strip().strip(","))

                    if extracted_tags:
                        sep = inputs.get("separator", ", ")
                        fallback_pos_prompt = sep.join(extracted_tags)

        final_pos_prompt = (
            pos_prompt.strip() if pos_prompt.strip() else fallback_pos_prompt
        )

        results = list()
        for image in images:
            height, width = image.shape[0], image.shape[1]
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo()

            steps = 20
            cfg = 4.0
            sampler_name = "er_sde"
            scheduler = "simple"
            seed = 0
            neg_prompt = ""

            if prompt is not None:
                for node_id, node_data in prompt.items():
                    class_type = str(node_data.get("class_type", ""))

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
                                seed_inputs = prompt[seed_node_id].get(
                                    "inputs", {}
                                )
                                seed = seed_inputs.get("seed", seed)

                    elif class_type in [
                        "CLIPTextEncode",
                        "PrimitiveStringMultiline",
                        "Text Multiline",
                    ]:
                        title = (
                            node_data.get("_meta", {})
                            .get("title", "")
                            .lower()
                        )
                        if "neg" in title:
                            inputs = node_data.get("inputs", {})
                            if "text" in inputs and isinstance(
                                inputs["text"], str
                            ):
                                neg_prompt = inputs["text"]
                            elif "value" in inputs and isinstance(
                                inputs["value"], str
                            ):
                                neg_prompt = inputs["value"]

            clean_pos = final_pos_prompt.replace("\n", ", ")
            clean_neg = (
                neg_prompt.strip().replace("\n", ", ") if neg_prompt else ""
            )

            param_parts = [
                f"Steps: {steps}",
                f"Sampler: {sampler_name}",
                f"Schedule type: {scheduler}",
                f"CFG scale: {cfg}",
                f"Seed: {seed}",
                f"Size: {width}x{height}",
            ]

            if not wipe_checkpoint and model_hash:
                param_parts.append(f"Model hash: {model_hash}")

            if not wipe_checkpoint and model_name:
                param_parts.append(f"Model: {model_name}")

            if not wipe_lora and lora_hashes_dict:
                hashes_str = ", ".join(
                    [f"{k}: {v}" for k, v in lora_hashes_dict.items()]
                )
                param_parts.append(f'Lora hashes: "{hashes_str}"')

            param_parts.append("Version: ComfyUI")

            civitai_format_prompt = (
                f"{clean_pos}\n"
                f"Negative prompt: {clean_neg}\n"
                f"{', '.join(param_parts)}"
            )

            metadata.add_text("parameters", civitai_format_prompt)
            metadata.add_text("positive_prompt", final_pos_prompt)

            if not wipe_workflow:
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            else:
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        if x != "workflow":
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            file = f"{filename}_{counter:05}_.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=4,
            )
            results.append(
                {
                    "filename": file,
                    "subfolder": subfolder,
                    "type": self.type,
                }
            )
            counter += 1

        return {"ui": {"images": results}}
