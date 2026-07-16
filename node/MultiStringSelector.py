class MultiStringSelector:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "active_input": (["Manual Pormpt", "Pormpt From File", "Random Pormpt", "Selector"], {"default": "Manual Pormpt"}),
            },
            "optional": {
                "Manual Pormpt": ("STRING", {"forceInput": True}),
                "Pormpt From File": ("STRING", {"forceInput": True}),
                "Random Pormpt": ("STRING", {"forceInput": True}),
                "Selector": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "select_string"
    # CATEGORY = "utils"
    CATEGORY = "ALTOOLS"

    def select_string(self, active_input, **kwargs):
        # 使用 **kwargs 依據連線點名稱安全取值
        return (kwargs.get(active_input, ""),)
