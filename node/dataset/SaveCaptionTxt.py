import os

class SaveCaptionTxt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "input_file_name": ("STRING", {"default": ""}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_caption"
    OUTPUT_NODE = True
    CATEGORY = "ALTOOLS"

    def _get_image_filename(self, prompt, current_node_id):
        """遞迴向前搜尋連接的 Node，尋找包含 image 檔名的欄位"""
        visited = set()

        def trace(node_id):
            if node_id in visited or node_id not in prompt:
                return None
            visited.add(node_id)

            node_inputs = prompt[node_id].get("inputs", {})

            if "image" in node_inputs and isinstance(node_inputs["image"], str):
                return node_inputs["image"]

            for val in node_inputs.values():
                if isinstance(val, list) and len(val) == 2:
                    parent_id = str(val[0])
                    res = trace(parent_id)
                    if res:
                        return res
            return None

        return trace(current_node_id)

    def save_caption(self, text, input_file_name, prompt=None, unique_id=None):
        out_path = None

        # 1. 優先採用必填的 input_file_name 絕對路徑
        if input_file_name and input_file_name.strip():
            target_file = input_file_name.strip()
            out_path = os.path.splitext(target_file)[0] + ".txt"

        # 2. 若 input_file_name 為空字串，才向上一層搜尋圖像檔名
        elif prompt and unique_id:
            image_filename = self._get_image_filename(prompt, str(unique_id))
            if image_filename:
                out_path = os.path.splitext(image_filename)[0] + ".txt"

        # 3. 救援機制 (Fallback)
        if not out_path:
            print("[SaveCaptionTxt] 錯誤：無法取得有效的 input_file_name")
            return {}

        # 自動建立目標資料夾（若不存在）
        parent_dir = os.path.dirname(out_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[SaveCaptionTxt] 已儲存標籤至: {out_path}")
        return {}
