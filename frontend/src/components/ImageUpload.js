import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./ImageUpload.css";

const API_BASE = process.env.REACT_APP_API || "http://127.0.0.1:5000";

const ImageUpload = () => {
  const [uploadedImages, setUploadedImages] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const handleFiles = (files) => {
    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageData = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: formatFileSize(file.size),
          url: e.target.result,
          file: file,
        };
        setUploadedImages((prev) => [...prev, imageData]);
      };
      reader.readAsDataURL(file);
    });
  };

  const handleFileInputChange = (e) => handleFiles(e.target.files);
  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const removeImage = (id) => setUploadedImages((prev) => prev.filter((i) => i.id !== id));
  const clearAllImages = () => {
    if (window.confirm("Clear all images?")) {
      setUploadedImages([]);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleProceed = async () => {
    if (uploadedImages.length === 0) {
      alert("Please upload at least one image.");
      return;
    }
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("image", uploadedImages[0].file);

      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Prediction request failed");
      }

      const data = await res.json();
      navigate("/output", { state: { image: uploadedImages[0].url, result: data } });
    } catch (err) {
      console.error(err);
      alert("Prediction failed: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="ai-background">
      <div className="glass-card">
        <header className="ai-header">
          <h1>Retinal Blindness Detection</h1>
          <p>AI-Powered Retinal Disease Diagnosis & Grad-CAM Visualization</p>
        </header>

        <div
          className={`drop-zone ${isDragging ? "dragging" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="eye-glow">👁️</div>
          <h3>Upload or Drag & Drop Retinal Images</h3>
          <p>Supported formats: JPG, PNG, JPEG</p>
          <button
            className="upload-button"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Select Image
          </button>
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            multiple
            onChange={handleFileInputChange}
            style={{ display: "none" }}
          />
        </div>

        {uploadedImages.length > 0 && (
          <div className="image-gallery-section">
            <div className="gallery-header">
              <h2>Uploaded Images ({uploadedImages.length})</h2>
              <button onClick={clearAllImages} className="clear-all">Clear All</button>
            </div>

            <div className="gallery-grid">
              {uploadedImages.map((img) => (
                <div key={img.id} className="gallery-item">
                  <img src={img.url} alt={img.name} />
                  <button className="remove-btn" onClick={() => removeImage(img.id)}>×</button>
                  <div className="meta-info">
                    <span>{img.name}</span>
                    <small>{img.size}</small>
                  </div>
                </div>
              ))}
            </div>

            <button className="analyze-btn" onClick={handleProceed} disabled={isUploading}>
              {isUploading ? "Analyzing..." : "Proceed to AI Analysis →"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageUpload;
