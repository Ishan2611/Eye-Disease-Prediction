from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize Groq client

# UNCOMMENT THE BELOW MESSAGE 
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

class SmartGroqFundusExplainer:
    def __init__(self, client, prediction_label, confidence):
        self.client = client
        self.prediction_label = prediction_label
        self.confidence = confidence
        self.is_normal = (prediction_label.lower() == "normal")
        self.prediction_context = self._build_prediction_context()
        self.system_context = self._build_system_context()

    def _build_prediction_context(self):
        """Build specific context based on prediction"""
        if self.is_normal:
            return """✅ THIS PATIENT'S EYE IS NORMAL:
- The AI found no disease markers
- Eye structures (optic disc, blood vessels) look healthy
- Patient should feel reassured
- Regular checkups still recommended"""
        else:
            return """⚠️ THIS PATIENT'S EYE IS DISEASED:
- The AI detected abnormalities
- Requires professional medical evaluation
- Should be taken seriously
- Patient needs ophthalmologist appointment URGENTLY"""

    def _build_system_context(self):
        """Build system context for Groq"""
        return f"""You are a friendly medical AI assistant explaining THIS SPECIFIC fundus image analysis.

📊 YOUR ACTUAL ANALYSIS RESULT:
- Prediction: {self.prediction_label}
- Confidence: {self.confidence:.2f}%

{self.prediction_context}

Guidelines:
1. Answer based on THIS SPECIFIC result (not generic)
2. Use simple, patient-friendly language
3. ALWAYS recommend consulting ophthalmologist
4. Use emoji: 🔴 = important, ✅ = good, ⚠️ = warning
5. Keep answers under 150 words
6. Be empathetic"""

    def handle_prediction_question(self):
        """Direct answer for 'what is the prediction' type questions"""
        if self.is_normal:
            return f"""YOUR PREDICTION RESULT: NORMAL ({self.confidence:.2f}% confidence)

This means your eye fundus appears HEALTHY and FREE FROM DISEASE:
• Your optic disc looks clear and well-defined
• Blood vessels appear normal and healthy
• Retinal structures show no abnormalities
• No signs of hemorrhages, lesions, or disease

🎉 This is good news! Your eye is healthy.
📋 Still recommended: Annual eye checkups to maintain eye health."""
        else:
            return f"""YOUR PREDICTION RESULT: DISEASED ({self.confidence:.2f}% confidence)

This means the AI detected ABNORMALITIES in your fundus:
• The eye shows structural changes
• Possible disease markers were found
• Blood vessels or retinal areas appear abnormal
• Professional evaluation is CRITICAL

🏥 URGENT ACTION NEEDED:
1. Schedule ophthalmologist appointment IMMEDIATELY
2. Bring this report to your doctor
3. Describe any vision symptoms
4. Do NOT delay - early treatment matters"""

    def handle_eye_status_question(self):
        """Direct answer for 'what happened to my eye' type questions"""
        if self.is_normal:
            return f"""YOUR EYE STATUS: NORMAL AND HEALTHY

Good news! According to our AI analysis:
• Your eye fundus appears completely normal
• All retinal structures are healthy
• No disease or abnormalities detected
• Confidence level: {self.confidence:.2f}%

This means you can feel reassured about your eye health.
Continue with regular annual eye checkups."""
        else:
            return f"""YOUR EYE STATUS: ABNORMALITIES DETECTED

Important: Our AI detected disease markers in your eye:
• Confidence level: {self.confidence:.2f}%
• Abnormalities found in fundus structure
• May indicate disease requiring treatment
• Exact diagnosis requires professional evaluation

ACTION REQUIRED:
See an ophthalmologist URGENTLY for proper diagnosis.
This could be serious if left untreated."""

    def handle_heatmap_question(self):
        """Heatmap explanation specific to prediction"""
        if self.is_normal:
            return """🔴 RED AREAS (NORMAL RESULT):
Red highlights show WHERE the model looked for disease:
• Optic disc - checked for clarity & shape
• Blood vessels - checked for health
• Retinal areas - checked for lesions

🟢 GOOD NEWS: Model found all these areas are HEALTHY
These red areas show healthy structures, not disease."""
        else:
            return """🔴 RED AREAS (DISEASED RESULT):
Red highlights show WHERE the model found problems:
• Abnormal retinal areas
• Structural changes
• Disease markers
• Areas requiring professional evaluation

⚠️ RED AREAS = DISEASE INDICATORS
These are the regions a doctor needs to examine closely."""

    def handle_help_question(self):
        """Help menu with example questions"""
        return """📚 EXAMPLE QUESTIONS:

**About Your Diagnosis:**
• What is the prediction?
• What happened to my eye?
• Is my eye normal or diseased?

**About the Visualization:**
• What do the red areas mean?
• How to read the heatmap?

**Next Steps:**
• What should I do?
• How reliable is this?
• Do I need a doctor?

Just ask naturally - I'll understand! 😊"""

    def get_groq_answer(self, user_question):
        """Get answer from Groq API"""
        try:
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_context
                    },
                    {
                        "role": "user",
                        "content": user_question
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=250,
            )
            return message.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                return "❌ API Key Error. Check: https://console.groq.com/keys"
            elif "429" in error_msg:
                return "⏳ Rate limited. Wait a moment and try again."
            else:
                return f"❌ Error: {error_msg}"

    def answer_question(self, question):
        """Intelligent question routing"""
        question_lower = question.lower().strip()

        # Help command
        if question_lower == "help":
            return self.handle_help_question()

        # Direct prediction questions
        if any(phrase in question_lower for phrase in
               ["what is the prediction", "what's the prediction", "what is my prediction",
                "tell me the prediction", "what was predicted", "my prediction",
                "the prediction", "prediction result", "what did it predict"]):
            return self.handle_prediction_question()

        # Eye status questions
        elif any(phrase in question_lower for phrase in
                ["what happened to my eye", "what's wrong with my eye", "status of my eye",
                 "is my eye normal", "my eye", "eye condition", "eye health",
                 "am i normal", "do i have disease", "do i have something"]):
            return self.handle_eye_status_question()

        # Heatmap questions
        elif any(phrase in question_lower for phrase in
                ["red", "blue", "heatmap", "color", "area", "regions", "highlights",
                 "grad-cam", "visualization", "what does the image show"]):
            return self.handle_heatmap_question()

        # Default: Ask Groq with full context
        else:
            return self.get_groq_answer(question)


# API Routes
@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        diagnosis = data.get('diagnosis', 'Normal')
        confidence = data.get('confidence', 0.0)

        if not question:
            return jsonify({'error': 'Question is required'}), 400

        # Initialize explainer
        explainer = SmartGroqFundusExplainer(client, diagnosis, confidence)
        
        # Get answer
        answer = explainer.answer_question(question)

        return jsonify({
            'answer': answer,
            'diagnosis': diagnosis,
            'confidence': confidence
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/welcome', methods=['POST'])
def welcome():
    """Generate welcome message based on diagnosis"""
    try:
        data = request.json
        diagnosis = data.get('diagnosis', 'Normal')
        confidence = data.get('confidence', 0.0)

        welcome_msg = f"""👋 Hi! I'm your AI assistant. I can help explain your diagnosis of **{diagnosis}** ({confidence:.2f}% confidence).

Feel free to ask me anything about:
• What this prediction means
• Understanding the heatmap
• What you should do next
• How reliable this analysis is

Type 'help' for example questions!"""

        return jsonify({'message': welcome_msg})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'groq_configured': bool(GROQ_API_KEY),
        'model': 'llama-3.3-70b-versatile'
    })


if __name__ == '__main__':
    print("="*70)
    print("🤖 FUNDUS CHATBOT API SERVER")
    print("="*70)
    print(f"✅ Groq API configured")
    print(f"📡 Server starting on http://localhost:5000")
    print(f"📋 Endpoints:")
    print(f"   POST /api/chat - Main chat endpoint")
    print(f"   POST /api/welcome - Get welcome message")
    print(f"   GET  /api/health - Health check")
    print("="*70)
    
    app.run(debug=True, port=5000)