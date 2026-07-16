import torch
import numpy as np
import cv2

# ------------------------------------------------------------------
# 新增的日系白紗感調色節點類別
# ------------------------------------------------------------------
class JapaneseSoftFilter:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "blend_percentage": ("FLOAT", {
                    "default": 0.25,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_filter"
    # CATEGORY = "ImageProcessing/Effects"
    CATEGORY = "ALTOOLS"

    def apply_filter(self, image, blend_percentage):
        output_images = []

        for img_tensor in image:
            # 1. Tensor [H, W, C] (0-1) 轉 NumPy BGR (0-255)
            img_np = (img_tensor.cpu().numpy() * 255.0).astype(np.float32)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            original_bgr = img_bgr.copy()

            # 2. 核心日系 NumPy 運算 (你微調過後的最佳 Setting)
            # 大幅提亮
            img_processed = img_bgr + 55.0

            # 提高暗部
            dark_mask = (img_processed[:, :, 0] + img_processed[:, :, 1] + img_processed[:, :, 2]) / 3.0 < 90.0
            img_processed[dark_mask] += 20.0

            # 加大版清晰度降低 (Kernel 121x121, Sigma 30)
            blur_layer = cv2.GaussianBlur(img_processed, (121, 121), 30)
            img_processed = cv2.addWeighted(img_processed, 0.6, blur_layer, 0.4, 0)

            # 降低飽和度
            gray = img_processed[:, :, 0] * 0.114 + img_processed[:, :, 1] * 0.587 + img_processed[:, :, 2] * 0.299
            gray_3ch = np.stack([gray] * 3, axis=-1)
            img_processed = cv2.addWeighted(img_processed, 0.6, gray_3ch, 0.4, 0)

            # 注入日系青藍色調
            img_processed[:, :, 0] += 8.0  # Blue
            img_processed[:, :, 1] += 5.0  # Green

            effected_bgr = np.clip(img_processed, 0, 255)

            # 3. 按百分比進行線性混合
            final_bgr = (original_bgr * (1.0 - blend_percentage)) + (effected_bgr * blend_percentage)
            final_bgr = np.clip(final_bgr, 0, 255).astype(np.uint8)

            # 4. BGR 轉回 RGB 並換回 ComfyUI Tensor 格式 [H, W, C]
            final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
            final_tensor = torch.from_numpy(final_rgb.astype(np.float32) / 255.0)
            output_images.append(final_tensor)

        # 打包回 Batch Tensor [B, H, W, C] 輸出
        return (torch.stack(output_images, dim=0),)


# import cv2
# import numpy as np


# def apply_blendable_soft_filter(image_path, save_path, blend_percentage=0.5):
#     """
#     應用日系白紗感濾鏡，並可控制效果強弱。

#     blend_percentage: 控制白紗感的百分比 (0.0 到 1.0)
#                        例如 0.3 代表 30% 效果 + 70% 原圖
#     """
#     # 1. 讀取影像
#     img = cv2.imread(image_path)
#     if img is None:
#         print("無法讀取影像，請檢查路徑。")
#         return

#     # 保存一份原圖作為混合基底
#     original_img = img.astype(np.float32)

#     # 轉為 float32 進行運算
#     img_processed = original_img.copy()

#     # ----------------------------------------------------
#     # (這部分是之前的核心白紗感 NumPy 處理鏈，全部用在 img_processed 上)
#     # ----------------------------------------------------
#     # 大幅提亮 (增加到 55.0，讓效果更明顯以便混合)
#     img_processed = img_processed + 55.0

#     # 提高暗部 (模擬去純黑曲線)
#     dark_mask = (
#         img_processed[:, :, 0] + img_processed[:, :, 1] + img_processed[:, :, 2]
#     ) / 3.0 < 90.0
#     img_processed[dark_mask] += 20.0

#     # 模擬清晰度降低 (創造朦朧感)
#     blur_layer = cv2.GaussianBlur(img_processed, (61, 61), 0)
#     img_processed = cv2.addWeighted(img_processed, 0.6, blur_layer, 0.4, 0)

#     # 降低飽和度
#     gray = (
#         img_processed[:, :, 0] * 0.114
#         + img_processed[:, :, 1] * 0.587
#         + img_processed[:, :, 2] * 0.299
#     )
#     gray_3ch = np.stack([gray] * 3, axis=-1)
#     img_processed = cv2.addWeighted(img_processed, 0.6, gray_3ch, 0.4, 0)

#     # 注入日系青藍色調
#     img_processed[:, :, 0] += 8.0  # Blue
#     img_processed[:, :, 1] += 5.0  # Green

#     # 限制範圍，這是我們「100% 強度」的效果圖
#     effected_img_uint8 = np.clip(img_processed, 0, 255).astype(np.uint8)

#     # ----------------------------------------------------
#     # 關鍵步驟：NumPy 按百分比進行混合
#     # ----------------------------------------------------
#     # 確保百分比在 0-1 之間
#     percent = np.clip(blend_percentage, 0.0, 1.0)

#     # 雖然用 cv2.addWeighted 也可以，但這裡用純 NumPy 公式展示
#     final_img_float = (original_img * (1.0 - percent)) + (
#         effected_img_uint8.astype(np.float32) * percent
#     )

#     # 轉回 uint8
#     final_blended = np.clip(final_img_float, 0, 255).astype(np.uint8)

#     # ----------------------------------------------------
#     # 保存結果 (原圖 vs 混合後的圖)
#     # ----------------------------------------------------
#     result_comparison = np.hstack((img, final_blended))

#     cv2.imwrite(save_path, result_comparison)
#     print(f"白紗感調色（強度 {int(percent * 100)}%）完成！已儲存至: {save_path}")


# if __name__ == "__main__":
#     image_path = "Ramune_Heisei3.png"
#     apply_blendable_soft_filter(image_path, "output.png", blend_percentage=0.25)

# # docker run --rm -it -v $PWD:/w -w /w python:3.11-slim bash
# # pip install uv && uv pip install opencv-python-headless numpy --system
