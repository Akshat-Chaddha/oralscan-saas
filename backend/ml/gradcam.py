import torch
import torchvision.transforms as T
import numpy as np
import cv2
from PIL import Image
import sys
from ml.predictor import MODEL, DEVICE
sys.path.append(r"C:\Users\23ad1\oral_cancer_detection\src")
from ml.predictor import MODEL, DEVICE

TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225])
])

def generate_gradcam(pil_image: Image.Image) -> Image.Image:
    try:
        tensor  = TRANSFORM(pil_image).unsqueeze(0).to(DEVICE)
        tensor.requires_grad_(True)

        output  = MODEL(tensor)
        # Handle tuple output
        logits  = output[0] if isinstance(output, tuple) else output

        pred    = logits.argmax(dim=1)
        logits[0, pred].backward()

        grads   = tensor.grad.data.abs().mean(dim=1, keepdim=True)
        grads   = grads.squeeze().cpu().numpy()
        grads   = (grads - grads.min()) / (grads.max() - grads.min() + 1e-8)

        img_np  = np.array(pil_image.resize((224, 224)))
        heatmap = cv2.applyColorMap(
            (grads * 255).astype(np.uint8), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        overlay = (0.6 * img_np + 0.4 * heatmap).astype(np.uint8)
        return Image.fromarray(overlay)

    except Exception as e:
        print(f"Grad-CAM failed: {e}, returning original image")
        return pil_image.resize((224, 224))