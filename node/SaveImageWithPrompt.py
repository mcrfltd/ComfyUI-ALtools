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
    CATEGORY = "ALTOOLS"

    def get_json_autov2_hash(self, lora_file_name):
        """專門解析 JSON，並確認 files 中的 name 與 lora_file_name 對應才取出 AutoV2 Hash"""
        if not lora_file_name:
            return None

        clean_name = str(lora_file_name).strip()
        # 取得純檔名 (例如 "zoda_v3_anima.safetensors")
        target_filename = os.path.basename(clean_name).lower()
        if not target_filename.endswith(".safetensors"):
            target_filename += ".safetensors"

        # 尋找 loras/ 目錄下的檔案
        full_lora_path = folder_paths.get_full_path("loras", clean_name)
        if not full_lora_path and not clean_name.endswith(".safetensors"):
            full_lora_path = folder_paths.get_full_path("loras", clean_name + ".safetensors")

        if not full_lora_path:
            return None

        # 拼接同名 .json 檔案路徑
        json_path = os.path.splitext(full_lora_path)[0] + ".json"

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    files = []
                    if isinstance(data, dict):
                        if "version" in data and isinstance(data["version"], dict):
                            files = data["version"].get("files", [])
                        elif "files" in data and isinstance(data["files"], list):
                            files = data["files"]

                    # 遍歷 files 陣列，確認 name 與 target_filename 對應
                    if isinstance(files, list):
                        for file_info in files:
                            if isinstance(file_info, dict):
                                file_name_in_json = str(file_info.get("name", "")).strip().lower()

                                # 【關鍵點】確認 JSON 內的 name 對得上要求的 lora_file_name
                                if file_name_in_json == target_filename:
                                    autov2 = file_info.get("hashes", {}).get("AutoV2", "")
                                    if autov2:
                                        return autov2[:10].lower()

                        # 若有多個檔案但沒完全匹配成功，退回取第一個有 AutoV2 的檔案
                        for file_info in files:
                            if isinstance(file_info, dict):
                                autov2 = file_info.get("hashes", {}).get("AutoV2", "")
                                if autov2:
                                    return autov2[:10].lower()

            except Exception as e:
                print(f"[SaveImage] 讀取 LoRA JSON 失敗 ({json_path}): {e}")

        return None

    def save_images(self, images, filename_prefix="ComfyUI", pos_prompt="", prompt=None, extra_pnginfo=None):
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        detected_loras = []
        lora_hashes_dict = {}
        model_name = ""

        if prompt is not None:
            for node_id, node_data in prompt.items():
                class_type = str(node_data.get("class_type", ""))
                inputs = node_data.get("inputs", {})
                # 抓取 Checkpoint 底模名稱
                if "CheckpointLoader" in class_type or "ckpt_name" in inputs:
                    ckpt_path = inputs.get("ckpt_name", "")
                    if ckpt_path:
                        model_name = os.path.splitext(os.path.basename(str(ckpt_path)))[0]

                # 專門處理 AnimaMultiLoraLoader 節點
                if class_type == "AnimaMultiLoraLoader":
                    lora_data = inputs.get("lora_list_json", "")
                    # 1. 容錯解析：將資料統一轉為 list 結構
                    lora_list = []
                    if isinstance(lora_data, str) and lora_data.strip():
                        try:
                            parsed = json.loads(lora_data)
                            # 處理雙重序列化 (String 裡面包 String) 的極端情況
                            if isinstance(parsed, str):
                                parsed = json.loads(parsed)
                            if isinstance(parsed, list):
                                lora_list = parsed
                        except Exception as e:
                            print(f"[SaveImage] JSON 解析失敗: {e}")
                    elif isinstance(lora_data, list):
                        lora_list = lora_data
                    # 2. 迭代 list 處理
                    for item in lora_list:
                        # 處理項目可能是 dict 或被二次序列化的 JSON string
                        if isinstance(item, str):
                            try:
                                item = json.loads(item)
                            except Exception:
                                continue
                        if isinstance(item, dict) and item.get("enabled", False):
                            raw_name = item.get("name", "")
                            strength = item.get("strength_model", item.get("strength", 1.0))

                            if not raw_name:
                                continue

                            # 到 loras/ 下搜尋 .json 檔中的 AutoV2 Hash
                            hash_val = self.get_json_autov2_hash(raw_name)

                            # 只有成功拿到 Hash 的 LoRA 才加入輸出結果
                            if hash_val:
                                clean_name = os.path.splitext(os.path.basename(raw_name))[0]
                                lora_tag = f"<lora:{clean_name}:{strength}>"

                                if lora_tag not in detected_loras:
                                    detected_loras.append(lora_tag)
                                lora_hashes_dict[clean_name] = hash_val

        results = list()
        for image in images:
            height, width = image.shape[0], image.shape[1]
            i = 255. * image.cpu().numpy()
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
                                seed_inputs = prompt[seed_node_id].get("inputs", {})
                                seed = seed_inputs.get("seed", seed)

                    elif class_type in ["CLIPTextEncode", "PrimitiveStringMultiline", "Text Multiline"]:
                        title = node_data.get("_meta", {}).get("title", "").lower()
                        if "neg" in title:
                            inputs = node_data.get("inputs", {})
                            if "text" in inputs and isinstance(inputs["text"], str):
                                neg_prompt = inputs["text"]
                            elif "value" in inputs and isinstance(inputs["value"], str):
                                neg_prompt = inputs["value"]

            clean_pos = pos_prompt.strip().replace("\n", ", ")
            clean_neg = neg_prompt.strip().replace("\n", ", ") if neg_prompt else ""

            if detected_loras:
                lora_str = " ".join(detected_loras)
                clean_pos = f"{clean_pos}, {lora_str}" if clean_pos else lora_str

            param_parts = [
                f"Steps: {steps}",
                f"Sampler: {sampler_name}",
                f"Schedule type: {scheduler}",
                f"CFG scale: {cfg}",
                f"Seed: {seed}",
                f"Size: {width}x{height}"
            ]

            if model_name:
                param_parts.append(f"Model: {model_name}")

            if lora_hashes_dict:
                hashes_str = ", ".join([f"{k}: {v}" for k, v in lora_hashes_dict.items()])
                param_parts.append(f'Lora hashes: "{hashes_str}"')

            param_parts.append("Version: ComfyUI")

            civitai_format_prompt = (
                f"{clean_pos}\n"
                f"Negative prompt: {clean_neg}\n"
                f"{', '.join(param_parts)}"
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
