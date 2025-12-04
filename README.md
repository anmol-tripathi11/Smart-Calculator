# Smart-Calculator
Modern web calculator with beautiful glassmorphism design. Single HTML file frontend + Flask backend API. Features: full keyboard support, dark/light themes, smart history system, copy results, responsive design. No build tools needed.

🚀 Quick Start
Backend Setup
bash
pip install flask flask-cors
python app.py
# Server runs at http://localhost:5000
Frontend Setup
Open index.html in browser or use:

bash
python -m http.server 8000
✨ Key Features
Frontend (Single HTML file)
Beautiful UI: Glassmorphism design with gradient backgrounds

Dark/Light Theme: Toggle with persistent preference

Full Keyboard Support: Type expressions directly

Smart History: Slide-down panel with timestamps & export

Copy Results: One-click copy to clipboard

Responsive: Works on mobile & desktop

Backend (Flask API)
Secure Evaluation: Safe math expression parsing

REST API: Clean endpoints for all operations

Error Handling: Comprehensive validation & user-friendly messages

📁 Project Structure
text
Smart-Calculator/
├── index.html          # Complete frontend
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
└── README.md
🔢 Calculator Functions
Basic: +, -, ×, ÷, %, ( )

Scientific: sin, cos, tan, sqrt, log, ln

Advanced: ^ (exponent), ! (factorial)

Constants: π, e

📡 API Endpoints
POST /api/evaluate - Evaluate expressions

GET /api/functions - List available functions

GET /api/health - Health check

🎮 Usage Examples
text
2 + 2 * 3 → 8
sin(pi/2) → 1
sqrt(16) → 4
2^3 → 8
50% → 0.5
🛡️ Security
Restricted evaluation environment

Input sanitization & validation

Protected against malicious inputs

📱 Responsive Design
Mobile-friendly layout

Adaptive button sizes

Touch-friendly interface

📄 License
MIT License

Smart Calculator - Modern, feature-rich calculator in a single HTML file.
