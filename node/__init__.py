from .DynamicTextInputLoader import DynamicTextInputLoader
from .MultiStringSelector import MultiStringSelector
from .SaveImageWithPrompt import SaveImageWithPrompt
from .JapaneseSoftFilter import JapaneseSoftFilter
from .ImageFolderLoaderWithMetadata import ImageFolderLoaderWithMetadata

NODE_CLASS_MAPPINGS = {
    "DynamicTextInputLoader": DynamicTextInputLoader,
    "MultiStringSelector": MultiStringSelector,
    "SaveImageWithPrompt": SaveImageWithPrompt,
    "JapaneseSoftFilter": JapaneseSoftFilter,
    "ImageFolderLoaderWithMetadata": ImageFolderLoaderWithMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicTextInputLoader": "Dynamic Text Input Loader",
    "MultiStringSelector": "Multi String Selector",
    "SaveImageWithPrompt": "Save Image With Prompt",
    "JapaneseSoftFilter": "🌸 Japanese Soft Filter (White Veil)",
    "ImageFolderLoaderWithMetadata": "Image Folder Loader (Metadata & Index Control)",
}
