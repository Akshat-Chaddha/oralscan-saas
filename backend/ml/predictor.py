import torch
import torchvision.transforms as T
from PIL import Image
import sys
import os

# Works both locally and on server
LOCAL_MODEL_PATH = r"C:\Users\23ad1\oral_cancer_detection\src"
SERVER_MODEL_PATH = "/app/src"

if os.path.exists(LOCAL_MODEL_PATH):
    sys.path.insert(0, LOCAL_MODEL_PATH)
elif os.path.exists(SERVER_MODEL_PATH):
    sys.path.insert(0, SERVER_MODEL_PATH)

from model import OralCancerHybridModel

# Model checkpoint path — works both locally and on server
LOCAL_CKPT  = r"C:\Users\23ad1\oralscan-saas\ml_model\best_model.pth"
SERVER_CKPT = "/app/ml_model/best_model.pth"

CKPT_PATH = LOCAL_CKPT if os.path.exists(LOCAL_CKPT) else SERVER_CKPT

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL = OralCancerHybridModel(num_classes=2).to(DEVICE)
ckpt  = torch.load(CKPT_PATH, map_location=DEVICE, weights_only=False)

if "model_state" in ckpt:
    state_dict = ckpt["model_state"]
elif "model_state_dict" in ckpt:
    state_dict = ckpt["model_state_dict"]
elif "state_dict" in ckpt:
    state_dict = ckpt["state_dict"]
else:
    state_dict = ckpt

MODEL.load_state_dict(state_dict)
MODEL.eval()
print(f"✅ Model loaded on {DEVICE}")

TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225])
])

CLASS_NAMES = ["non_cancer", "cancer"]

def predict_image(pil_image: Image.Image) -> dict:
    tensor = TRANSFORM(pil_image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = MODEL(tensor)
        logits = output[0] if isinstance(output, tuple) else output
        probs  = torch.softmax(logits, dim=1)[0]
    cancer_prob = probs[1].item()
    pred_idx    = probs.argmax().item()
    return {
        "label":           CLASS_NAMES[pred_idx],
        "confidence":      probs[pred_idx].item(),
        "cancer_prob":     cancer_prob,
        "non_cancer_prob": probs[0].item()
    }