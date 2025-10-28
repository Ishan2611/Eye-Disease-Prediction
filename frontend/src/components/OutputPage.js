import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ChatbotWidget from "./ChatbotWidget";
import "./OutputPage.css";

const OutputPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state || {};
  const { image, result } = state;

  const diagnosis = result?.diagnosis || "No result";
  const confidence = result?.confidence ?? 0;
  const gradcamUrl = result?.gradcam_url || null;
  const detectedFeatures = result?.detectedFeatures || [];

  return (
    <div className="output-background">
      <div className="output-glass-card">
        <header className="output-header">
          <h1>Analysis Results</h1>
          <p>AI-Powered Retinal Analysis with Explainability</p>
        </header>

        <div className="result-content">
          {/* Left - Image Section */}
          <div className="result-left">
            <div className="image-frame">
              {image ? (
                <img src={image} alt="Uploaded" className="main-image" />
              ) : (
                <div className="placeholder">👁️ No Image</div>
              )}
            </div>

            {gradcamUrl && (
              <div className="gradcam-frame">
                <h4>Grad-CAM Visualization</h4>
                <img src={gradcamUrl} alt="Grad-CAM" className="gradcam-image" />
              </div>
            )}
          </div>

          {/* Right - Details Section */}
          <div className="result-right">
            <h2 className="diagnosis-title">Diagnosis</h2>
            <h3 className="diagnosis-result">{diagnosis}</h3>

            <div className="confidence-box">
              <div className="confidence-header">
                <span>Confidence Level</span>
                <span>{confidence.toFixed(2)}%</span>
              </div>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{ width: `${confidence}%` }}
                ></div>
              </div>
            </div>

            <div className="features-box">
              <h4>Detected Features</h4>
              <ul>
                {detectedFeatures.length ? (
                  detectedFeatures.map((f, i) => (
                    <li key={i}>
                      <span>✓</span> {f}
                    </li>
                  ))
                ) : (
                  <li>
                    <span>✓</span> No extra features available
                  </li>
                )}
              </ul>
            </div>

            <div className="recommendation-box">
              <h4>Recommendation</h4>
              <p>
                Please consult an ophthalmologist for medical confirmation. This
                analysis is intended for preliminary assistance and educational
                purposes.
              </p>
            </div>

            {/* Chat Prompt Box */}
            <div className="chat-prompt-box">
              <div className="chat-prompt-icon">💬</div>
              <div className="chat-prompt-content">
                <h4>Have questions about your diagnosis?</h4>
                <p>Click the chat button below to ask our AI assistant!</p>
              </div>
            </div>
          </div>
        </div>

        <div className="footer-center">
          <button className="analyze-again-btn" onClick={() => navigate("/")}>
            ← Analyze Another Image
          </button>
        </div>
      </div>

      {/* Chatbot Widget */}
      <ChatbotWidget diagnosis={diagnosis} confidence={confidence} />
    </div>
  );
};

export default OutputPage;