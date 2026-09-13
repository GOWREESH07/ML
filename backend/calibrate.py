import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from backend.architecture import BrainTumorCNN

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pth")
TEMP_PATH = os.path.join(os.path.dirname(__file__), "models", "temperature.json")
TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Epic and CSCR hospital Dataset", "Test")

class TemperatureScaler(nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # Clamp temperature to avoid numerical instability
        t = torch.clamp(self.temperature, min=0.01)
        return logits / t

def compute_ece(probs: torch.Tensor, labels: torch.Tensor, n_bins: int = 10) -> float:
    confidences, predictions = torch.max(probs, dim=1)
    accuracies = predictions.eq(labels)
    ece = torch.zeros(1)
    bin_boundaries = torch.linspace(0, 1, n_bins + 1)
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = confidences.gt(bin_lower) * confidences.le(bin_upper)
        prop_in_bin = in_bin.float().mean()
        if prop_in_bin.item() > 0:
            accuracy_in_bin = accuracies[in_bin].float().mean()
            avg_confidence_in_bin = confidences[in_bin].mean()
            ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    return float(ece.item())

def calibrate():
    print("=== NeuroScan AI Temperature Scaling Calibration ===")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    if not os.path.exists(TEST_DIR):
        raise FileNotFoundError(f"Test dataset not found at {TEST_DIR}")

    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    classes = ckpt.get("classes", ["glioma", "meningioma", "notumor", "pituitary"])
    model = BrainTumorCNN(num_classes=len(classes))
    model.load_state_dict(ckpt["model"], strict=True)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    test_ds = datasets.ImageFolder(TEST_DIR, transform=transform)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)
    print(f"Loaded held-out test set: {len(test_ds)} images across {len(test_ds.classes)} classes: {test_ds.classes}")

    # 1. Collect uncalibrated logits and labels
    print("Collecting model logits across held-out test set...")
    all_logits = []
    all_labels = []
    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(test_loader):
            logits = model(images)
            all_logits.append(logits)
            all_labels.append(labels)
            if (batch_idx + 1) % 20 == 0 or (batch_idx + 1) == len(test_loader):
                print(f"  Processed {min((batch_idx + 1) * 32, len(test_ds))}/{len(test_ds)} images")

    logits_tensor = torch.cat(all_logits, dim=0)
    labels_tensor = torch.cat(all_labels, dim=0)

    # 2. Pre-calibration metrics
    criterion = nn.CrossEntropyLoss()
    pre_nll = float(criterion(logits_tensor, labels_tensor).item())
    pre_probs = torch.softmax(logits_tensor, dim=1)
    pre_ece = compute_ece(pre_probs, labels_tensor)
    print(f"\nPre-calibration:  NLL = {pre_nll:.4f}, ECE = {pre_ece:.4f}")

    # 3. Fit Temperature T via NLL minimization
    scaler = TemperatureScaler()
    optimizer = optim.LBFGS([scaler.temperature], lr=0.01, max_iter=100)

    def eval_loss():
        optimizer.zero_grad()
        loss = criterion(scaler(logits_tensor), labels_tensor)
        loss.backward()
        return loss

    optimizer.step(eval_loss)
    fitted_t = float(torch.clamp(scaler.temperature, min=0.01).item())

    # 4. Post-calibration metrics
    post_logits = logits_tensor / fitted_t
    post_nll = float(criterion(post_logits, labels_tensor).item())
    post_probs = torch.softmax(post_logits, dim=1)
    post_ece = compute_ece(post_probs, labels_tensor)
    print(f"Post-calibration: NLL = {post_nll:.4f}, ECE = {post_ece:.4f}")
    print(f"Fitted Temperature T = {fitted_t:.4f}")

    # 5. Save to temperature.json
    result = {
        "temperature": round(fitted_t, 4),
        "pre_nll": round(pre_nll, 4),
        "post_nll": round(post_nll, 4),
        "pre_ece": round(pre_ece, 4),
        "post_ece": round(post_ece, 4),
        "sample_count": len(test_ds)
    }
    with open(TEMP_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Successfully saved temperature calibration to {TEMP_PATH}")
    return result

if __name__ == "__main__":
    calibrate()
