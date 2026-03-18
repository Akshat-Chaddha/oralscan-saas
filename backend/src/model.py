"""
model.py
========
Novel Hybrid CNN-ViT architecture with Cross-Attention Fusion
for oral cancer severity grading.

Architecture:
  EfficientNet-B4  (local texture features)
       +
  Swin Transformer (global context features)
       ↓
  Cross-Attention Fusion Module
       ↓
  Severity Grading Head (4 classes)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
from torchvision import models
import yaml
import logging

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
#  Cross-Attention Fusion Module
# ──────────────────────────────────────────────────────────────
class CrossAttentionFusion(nn.Module):
    """
    Fuses CNN (local) and ViT (global) features using cross-attention.
    CNN features attend TO ViT features to capture which global
    contexts are relevant for each local texture region.
    """

    def __init__(self, dim: int = 512, num_heads: int = 8):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim  = dim // num_heads
        self.scale     = self.head_dim ** -0.5

        self.q_proj    = nn.Linear(dim, dim)
        self.k_proj    = nn.Linear(dim, dim)
        self.v_proj    = nn.Linear(dim, dim)
        self.out_proj  = nn.Linear(dim, dim)
        self.norm      = nn.LayerNorm(dim)
        self.dropout   = nn.Dropout(0.1)

    def forward(self,
                cnn_feat: torch.Tensor,
                vit_feat: torch.Tensor) -> torch.Tensor:
        """
        cnn_feat: (B, 1, dim)
        vit_feat: (B, 1, dim)
        returns : (B, dim)
        """
        B = cnn_feat.size(0)

        Q = self.q_proj(cnn_feat)   # (B, 1, dim)
        K = self.k_proj(vit_feat)
        V = self.v_proj(vit_feat)

        # Reshape for multi-head attention
        Q = Q.view(B, 1, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(B, 1, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(B, 1, self.num_heads, self.head_dim).transpose(1, 2)

        attn_weights = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        attn_weights = self.dropout(F.softmax(attn_weights, dim=-1))

        out  = torch.matmul(attn_weights, V)
        out  = out.transpose(1, 2).contiguous().view(B, 1, -1)
        out  = self.out_proj(out).squeeze(1)

        # Residual connection
        return self.norm(out + cnn_feat.squeeze(1))


# ──────────────────────────────────────────────────────────────
#  Feature Projection Blocks
# ──────────────────────────────────────────────────────────────
class ProjectionBlock(nn.Module):
    def __init__(self, in_features: int, out_features: int,
                 dropout: float = 0.2):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(in_features, out_features),
            nn.BatchNorm1d(out_features),
            nn.GELU(),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.block(x)


# ──────────────────────────────────────────────────────────────
#  Main Hybrid Model
# ──────────────────────────────────────────────────────────────
class OralCancerHybridModel(nn.Module):
    """
    Multi-Scale Hybrid Vision Transformer for oral cancer
    severity grading (Normal / Leukoplakia / Erythroplakia / OSCC).
    """

    def __init__(self,
                 num_classes   : int   = 4,
                 fusion_dim    : int   = 512,
                 cnn_features  : int   = 1792,
                 vit_features  : int   = 1024,
                 dropout       : float = 0.4,
                 pretrained    : bool  = True):
        super().__init__()

        # ── Branch 1: EfficientNet-B4 (local texture) ────────
        efficientnet        = models.efficientnet_b4(
            weights=models.EfficientNet_B4_Weights.IMAGENET1K_V1
            if pretrained else None
        )
        # Remove classifier, keep feature extractor
        self.cnn_branch     = nn.Sequential(
            *list(efficientnet.children())[:-2]  # keep spatial features
        )
        self.cnn_gap        = nn.AdaptiveAvgPool2d(1)
        self.cnn_proj       = ProjectionBlock(cnn_features, fusion_dim,
                                               dropout=0.2)

        # ── Branch 2: Swin Transformer (global context) ──────
        self.vit_branch     = timm.create_model(
            "swin_base_patch4_window7_224",
            pretrained  = pretrained,
            num_classes = 0,         # remove head
            global_pool = "avg"
        )
        self.vit_proj       = ProjectionBlock(vit_features, fusion_dim,
                                               dropout=0.2)

        # ── Cross-Attention Fusion ────────────────────────────
        self.fusion         = CrossAttentionFusion(dim=fusion_dim,
                                                    num_heads=8)

        # ── Classification Head ───────────────────────────────
        # num_classes=2 for binary (cancer/non_cancer)
        # num_classes=4 for 4-class grading (future extension)
        self.classifier     = nn.Sequential(
            nn.LayerNorm(fusion_dim),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim, 256),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(256, num_classes),
        )

        # ── Feature head for contrastive loss ────────────────
        self.projection_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
        )

        self._init_weights()

    def _init_weights(self):
        for module in [self.cnn_proj, self.vit_proj, self.classifier,
                        self.projection_head]:
            for m in module.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Returns fused feature vector (before classifier)."""
        # CNN branch
        cnn_out  = self.cnn_branch(x)
        cnn_out  = self.cnn_gap(cnn_out).flatten(1)
        cnn_feat = self.cnn_proj(cnn_out).unsqueeze(1)

        # ViT branch
        vit_out  = self.vit_branch(x)
        vit_feat = self.vit_proj(vit_out).unsqueeze(1)

        # Cross-attention fusion
        fused    = self.fusion(cnn_feat, vit_feat)
        return fused

    def forward(self, x: torch.Tensor) -> tuple:
        """
        Returns:
            logits    (B, num_classes)  — for classification loss
            proj_feat (B, 128)          — for contrastive loss
        """
        fused     = self.forward_features(x)
        logits    = self.classifier(fused)
        proj_feat = F.normalize(self.projection_head(fused), dim=1)
        return logits, proj_feat


# ──────────────────────────────────────────────────────────────
#  Lightweight Variant (for ablation study)
# ──────────────────────────────────────────────────────────────
class CNNOnlyBaseline(nn.Module):
    """EfficientNet-B4 only baseline for ablation comparison."""

    def __init__(self, num_classes=4, pretrained=True):
        super().__init__()
        self.backbone = models.efficientnet_b4(
            weights=models.EfficientNet_B4_Weights.IMAGENET1K_V1
            if pretrained else None
        )
        in_features   = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        logits = self.backbone(x)
        proj   = F.normalize(logits, dim=1)
        return logits, proj


class ViTOnlyBaseline(nn.Module):
    """Swin Transformer only baseline for ablation comparison."""

    def __init__(self, num_classes=4, pretrained=True):
        super().__init__()
        self.backbone = timm.create_model(
            "swin_base_patch4_window7_224",
            pretrained  = pretrained,
            num_classes = num_classes
        )

    def forward(self, x):
        logits = self.backbone(x)
        proj   = F.normalize(logits, dim=1)
        return logits, proj


# ──────────────────────────────────────────────────────────────
#  Model Factory
# ──────────────────────────────────────────────────────────────
def build_model(cfg: dict, model_type: str = "hybrid") -> nn.Module:
    """
    model_type: 'hybrid' | 'cnn_only' | 'vit_only'
    """
    m_cfg       = cfg["model"]
    num_classes = cfg["data"]["num_classes"]
    pretrained  = m_cfg.get("pretrained", True)

    if model_type == "hybrid":
        model = OralCancerHybridModel(
            num_classes  = num_classes,
            fusion_dim   = m_cfg["fusion_dim"],
            cnn_features = m_cfg["cnn_features"],
            vit_features = m_cfg["vit_features"],
            dropout      = m_cfg["dropout"],
            pretrained   = pretrained,
        )
    elif model_type == "cnn_only":
        model = CNNOnlyBaseline(num_classes, pretrained)
    elif model_type == "vit_only":
        model = ViTOnlyBaseline(num_classes, pretrained)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    total_params = sum(p.numel() for p in model.parameters())
    train_params = sum(p.numel() for p in model.parameters()
                        if p.requires_grad)
    log.info(f"Model: {model_type} | "
             f"Total params: {total_params:,} | "
             f"Trainable: {train_params:,}")
    return model


if __name__ == "__main__":
    with open("config.yaml") as f:
        import yaml
        cfg = yaml.safe_load(f)

    model = build_model(cfg, "hybrid")
    dummy = torch.randn(2, 3, 224, 224)
    logits, feats = model(dummy)
    print(f"✅ Model output — logits: {logits.shape}, features: {feats.shape}")
