from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import io
import os
import cv2
import uuid
from PIL import Image
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
import traceback

app = Flask(__name__)
CORS(app)

# ========== CONFIG ==========
MODEL_PATH = os.path.join(os.path.dirname(__file__), "my_best_cnn_model.keras")
CLASS_NAMES = ['Normal', 'Diseased']
IMG_SIZE = (224, 224)
GRADCAM_DIR = os.path.join(os.path.dirname(__file__), "gradcam")
os.makedirs(GRADCAM_DIR, exist_ok=True)
# ============================

# Load model once
model = keras.models.load_model(MODEL_PATH, compile=False)
model.trainable = False


# ========= GradCAM Functions =========
def make_gradcam_heatmap_final(img_array, model, last_conv_layer_name, pred_index=None):
    img_array = tf.cast(img_array, tf.float32)
    last_conv_layer = model.get_layer(last_conv_layer_name)
    intermediate_layer_model = keras.Model(
        inputs=model.inputs[0],
        outputs=[last_conv_layer.output, model.outputs[0]]
    )
    with tf.GradientTape() as tape:
        tape.watch(img_array)
        conv_outputs, predictions = intermediate_layer_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_index]
    grads = tape.gradient(class_channel, conv_outputs)
    if grads is None:
        pooled_grads = tf.reduce_mean(tf.abs(conv_outputs), axis=(0, 1, 2))
    else:
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs_np = conv_outputs[0].numpy()
    pooled_grads_np = pooled_grads.numpy()
    heatmap = np.zeros(shape=conv_outputs_np.shape[:-1], dtype=np.float32)
    for i in range(pooled_grads_np.shape[-1]):
        heatmap += pooled_grads_np[i] * conv_outputs_np[:, :, i]
    heatmap = np.maximum(heatmap, 0)
    if np.max(heatmap) > 0:
        heatmap = heatmap / np.max(heatmap)
    return heatmap


def create_visualization(heatmap, img, pred_label, confidence, alpha=0.4):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    heatmap_resized = cv2.resize(heatmap, (224, 224))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_colored_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(img_rgb, 1 - alpha, heatmap_colored_rgb, alpha, 0)
    gradcam_filename = f"gradcam_{uuid.uuid4().hex[:8]}.jpg"
    gradcam_path = os.path.join(GRADCAM_DIR, gradcam_filename)
    cv2.imwrite(gradcam_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    return gradcam_filename


def find_last_conv_layer_name(model):
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    raise ValueError("No Conv2D layer found in model!")
# =====================================


# ========= Flask Routes =========
@app.route("/gradcam/<filename>")
def serve_gradcam(filename):
    return send_from_directory(GRADCAM_DIR, filename)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files["image"]
        img_bytes = file.read()
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = np.array(pil_img)
        img_resized = cv2.resize(img, IMG_SIZE)
        img_array = np.expand_dims(img_resized / 255.0, axis=0).astype(np.float32)

        preds = model.predict(img_array)
        pred_class = int(np.argmax(preds[0]))
        confidence = float(preds[0][pred_class])
        pred_label = CLASS_NAMES[pred_class]

        # 🔥 Grad-CAM
        last_conv_layer_name = find_last_conv_layer_name(model)
        heatmap = make_gradcam_heatmap_final(img_array, model, last_conv_layer_name, pred_index=pred_class)
        gradcam_filename = create_visualization(heatmap, img_resized, pred_label, confidence)
        gradcam_url = f"http://127.0.0.1:5000/gradcam/{gradcam_filename}"

        return jsonify({
            "diagnosis": pred_label,
            "confidence": round(confidence * 100, 2),
            "gradcam_url": gradcam_url,
            "raw_prediction": preds.tolist()
        })

    except Exception as e:
        print("❌ GradCAM generation failed:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return jsonify({"message": "Backend Running - Eye Disease Detection API"})


if __name__ == "__main__":
    print("✅ Flask backend started at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
