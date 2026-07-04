from .DynamicTextInputLoader import DynamicTextInputLoader
from .MultiStringSelector import MultiStringSelector
from .SaveImageWithPrompt import SaveImageWithPrompt

NODE_CLASS_MAPPINGS = {
    "DynamicTextInputLoader": DynamicTextInputLoader,
    "MultiStringSelector": MultiStringSelector,
    "SaveImageWithPrompt": SaveImageWithPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicTextInputLoader": "Dynamic Text Input Loader",
    "MultiStringSelector": "Multi String Selector",
    "SaveImageWithPrompt": "Save Image With Prompt"
}
