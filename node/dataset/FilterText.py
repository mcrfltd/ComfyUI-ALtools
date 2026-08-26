class FilterText:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "ignore_text": ("STRING", {"multiline": True, "default": ""}),
                "text_separator": ("STRING", {"default": ","}),
                "ignore_separator": ("STRING", {"default": "|"}),
                "case_sensitive": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filtered_text",)
    FUNCTION = "filter_text"
    CATEGORY = "ALTOOLS"

    def filter_text(
        self,
        text,
        ignore_text,
        text_separator=",",
        ignore_separator="|",
        case_sensitive=False,
    ):
        if not text.strip():
            return ("",)

        # 1. 拆分並清理 ignore list
        raw_ignores = [
            i.strip() for i in ignore_text.split(ignore_separator) if i.strip()
        ]

        if not raw_ignores:
            return (text,)

        # 2. 處理大小寫匹配邏輯
        if not case_sensitive:
            ignore_keywords = [k.lower() for k in raw_ignores]
        else:
            ignore_keywords = raw_ignores

        # 3. 拆分 input text 並過濾包含 ignore 關鍵字的元素
        raw_elements = text.split(text_separator)
        filtered_elements = []

        for elem in raw_elements:
            elem_clean = elem.strip()
            if not elem_clean:
                continue

            target_str = elem_clean if case_sensitive else elem_clean.lower()

            # 檢查元素是否包含任何一個 ignore 關鍵字
            if not any(keyword in target_str for keyword in ignore_keywords):
                filtered_elements.append(elem_clean)

        # 4. 用原本的 text_separator 重新組合字串
        join_delimiter = f"{text_separator} " if text_separator == "," else text_separator
        result_text = join_delimiter.join(filtered_elements)

        return (result_text,)
