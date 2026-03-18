"""
losses.py
=========
Custom loss functions:
  1. SupervisedContrastiveLoss  — handles class imbalance
  2. FocalLoss                  — down-weights easy examples
  3. CombinedLoss               — CE + Contrastive + optional Focal
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# ──────────────────────────────────────────────────────────────
#  1. Supervised Contrastive Loss
# ──────────────────────────────────────────────────────────────
class SupervisedContrastiveLoss(nn.Module):
    """
    Supervised Contrastive Learning (Khosla et al., NeurIPS 2020).
    Pulls same-class features together, pushes different classes apart.
    Critical novelty for handling imbalanced oral cancer dataset.
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, features: torch.Tensor,
                labels: torch.Tensor) -> torch.Tensor:
        """
        features: (B, D) — L2-normalized projection features
        labels  : (B,)   — class indices
        """
        device   = features.device
        B        = features.size(0)

        # Cosine similarity matrix
        sim_mat  = torch.matmul(features, features.T) / self.temperature

        # Mask: same class pairs (exclude diagonal)
        labels   = labels.contiguous().view(-1, 1)
        pos_mask = (labels == labels.T).float().to(device)
        pos_mask.fill_diagonal_(0)   # exclude self-pairs

        neg_mask = 1 - pos_mask
        neg_mask.fill_diagonal_(0)

        # Numerical stability
        sim_mat  = sim_mat - sim_mat.max(dim=1, keepdim=True).values.detach()

        exp_sim  = torch.exp(sim_mat)

        # Log-sum over negatives
        denom    = (exp_sim * (1 - torch.eye(B, device=device))).sum(
                        dim=1, keepdim=True
                    ).clamp(min=1e-8)

        log_prob = sim_mat - torch.log(denom)

        # Mean over positive pairs
        n_pos    = pos_mask.sum(dim=1).clamp(min=1)
        loss     = -(log_prob * pos_mask).sum(dim=1) / n_pos

        return loss.mean()


# ──────────────────────────────────────────────────────────────
#  2. Focal Loss
# ──────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    """
    Focal Loss (Lin et al., 2017).
    Down-weights well-classified easy examples so the model
    focuses on hard-to-classify lesion boundaries.
    """

    def __init__(self, alpha: float = 1.0, gamma: float = 2.0,
                 reduction: str = "mean"):
        super().__init__()
        self.alpha     = alpha
        self.gamma     = gamma
        self.reduction = reduction

    def forward(self, logits: torch.Tensor,
                targets: torch.Tensor) -> torch.Tensor:
        ce_loss  = F.cross_entropy(logits, targets, reduction="none")
        pt       = torch.exp(-ce_loss)
        focal    = self.alpha * (1 - pt) ** self.gamma * ce_loss

        if self.reduction == "mean":
            return focal.mean()
        elif self.reduction == "sum":
            return focal.sum()
        return focal


# ──────────────────────────────────────────────────────────────
#  3. Label Smoothing Cross-Entropy
# ──────────────────────────────────────────────────────────────
class LabelSmoothingCE(nn.Module):
    """Prevents overconfident predictions — useful for small datasets."""

    def __init__(self, smoothing: float = 0.1, num_classes: int = 4):
        super().__init__()
        self.smoothing   = smoothing
        self.num_classes = num_classes

    def forward(self, logits: torch.Tensor,
                targets: torch.Tensor) -> torch.Tensor:
        log_prob   = F.log_softmax(logits, dim=-1)
        smooth_val = self.smoothing / (self.num_classes - 1)

        # Build smooth target distribution
        one_hot    = torch.zeros_like(log_prob).scatter_(
                         1, targets.view(-1, 1), 1)
        smooth_tgt = one_hot * (1 - self.smoothing) + \
                     (1 - one_hot) * smooth_val

        loss = -(smooth_tgt * log_prob).sum(dim=-1)
        return loss.mean()


# ──────────────────────────────────────────────────────────────
#  4. Combined Loss (used in training)
# ──────────────────────────────────────────────────────────────
class CombinedLoss(nn.Module):
    """
    Weighted combination:
      L_total = L_CE + λ_contrastive * L_con + λ_focal * L_focal

    Using all three is a novel contribution for oral cancer classification.
    """

    def __init__(self,
                 num_classes         : int   = 4,
                 contrastive_weight  : float = 0.5,
                 focal_weight        : float = 0.3,
                 label_smoothing     : float = 0.1,
                 temperature         : float = 0.07,
                 focal_gamma         : float = 2.0):
        super().__init__()
        self.contrastive_weight = contrastive_weight
        self.focal_weight       = focal_weight

        self.ce_loss            = LabelSmoothingCE(
                                    smoothing   = label_smoothing,
                                    num_classes = num_classes)
        self.contrastive_loss   = SupervisedContrastiveLoss(
                                    temperature = temperature)
        self.focal_loss         = FocalLoss(gamma=focal_gamma)

    def forward(self,
                logits   : torch.Tensor,
                features : torch.Tensor,
                targets  : torch.Tensor) -> dict:
        """
        logits  : (B, C)  raw class scores
        features: (B, 128) normalized projection features
        targets : (B,)    ground truth labels

        Returns dict with individual and total losses for logging.
        """
        l_ce    = self.ce_loss(logits, targets)
        l_con   = self.contrastive_loss(features, targets)
        l_focal = self.focal_loss(logits, targets)

        l_total = (l_ce
                   + self.contrastive_weight * l_con
                   + self.focal_weight       * l_focal)

        return {
            "total"       : l_total,
            "ce"          : l_ce.item(),
            "contrastive" : l_con.item(),
            "focal"       : l_focal.item(),
        }


# ──────────────────────────────────────────────────────────────
#  Class-Weighted CE (alternative simpler approach)
# ──────────────────────────────────────────────────────────────
def get_class_weights(label_list: list,
                      num_classes: int,
                      device: str = "cpu") -> torch.Tensor:
    """
    Compute inverse-frequency class weights for imbalanced datasets.
    """
    counts  = np.bincount(label_list, minlength=num_classes).astype(float)
    weights = 1.0 / (counts + 1e-8)
    weights = weights / weights.sum() * num_classes    # normalize
    return torch.tensor(weights, dtype=torch.float).to(device)


if __name__ == "__main__":
    B, C, D = 8, 4, 128
    logits   = torch.randn(B, C)
    features = F.normalize(torch.randn(B, D), dim=1)
    targets  = torch.randint(0, C, (B,))

    criterion = CombinedLoss(num_classes=C)
    losses    = criterion(logits, features, targets)
    print("✅ Loss components:")
    for k, v in losses.items():
        val = v.item() if hasattr(v, "item") else v
        print(f"  {k:15s}: {val:.4f}")
