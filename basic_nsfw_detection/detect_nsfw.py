from transformers import AutoModelForImageClassification, AutoProcessor
from PIL import Image
import torch

# Load Model
model_name = "Falconsai/nsfw_image_detection"
model = AutoModelForImageClassification.from_pretrained(model_name)
processor = AutoProcessor.from_pretrained(model_name)

def detect_nsfw(image_path):
    """Detects if an image is NSFW or Normal."""
    image = Image.open(image_path)
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    logits = outputs.logits
    predicted_label = torch.argmax(logits, dim=-1).item()

    return "NSFW" if predicted_label == 1 else "Normal"

