# ------------------------------------------------------------------
# Camera Framing & Angle 選擇器節點類別
# ------------------------------------------------------------------
class AngleSelector:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "angle": ([
                    "view from front",
                    "view from behind",
                    "view from side",
                    "from above",
                    "from below",
                    "dutch angle",
                    "none",
                ], {"default": "view from front"}),

                "shot_type": ([
                    "face focus",
                    "close up",
                    "portrait",
                    "medium shot",
                    "cowboy shot",
                    "full body shot",
                    "none",
                ], {"default": "close up"}),

                "delimiter": ("STRING", {"default": ", "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "build_prompt"
    CATEGORY = "ALTOOLS"

    def build_prompt(self, angle, shot_type, delimiter):
        parts = []
        if angle != "none":
            parts.append(angle)
        if shot_type != "none":
            parts.append(shot_type)

        output_text = delimiter.join(parts)
        return (output_text,)
