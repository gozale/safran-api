import onnxruntime as ort
import numpy as np
from PIL import Image
import io
import json

session = ort.InferenceSession("models/resnet18-v2-7.onnx")
with open("models/imagenet-simple-labels.json") as f:
    labels = json.load(f)

def run_model(image_bytes):
    # Load image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Resize to model input shape (ResNet wants 224x224)
    image = image.resize((224, 224))

    # Convert to float32 and normalize
    np_image = np.array(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    np_image = (np_image - mean) / std

    # Reshape to match (1, 3, 224, 224)
    np_image = np.transpose(np_image, (2, 0, 1))  # HWC to CHW
    np_image = np.expand_dims(np_image, axis=0)

    # Ensure float32 dtype before passing to ONNX
    np_image = np_image.astype(np.float32)

    # Run inference
    inputs = {session.get_inputs()[0].name: np_image}
    outputs = session.run(None, inputs)

    pred_idx = int(np.argmax(outputs[0]))
    return labels[pred_idx]