import os
import json

class DynamicTextInputLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_list_json": ("STRING", {"default": "[]"}),
                "delimiter": ("STRING", {"default": ", ", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_texts"
    # CATEGORY = "utils"
    CATEGORY = "ALTOOLS"

    def process_texts(self, text_list_json, delimiter):
        try:
            texts = json.loads(text_list_json)
        except Exception:
            texts = []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        delim_char = delimiter.replace("\\n", "\n")
        output_string = delim_char.join(valid_texts)

        return (output_string,)
