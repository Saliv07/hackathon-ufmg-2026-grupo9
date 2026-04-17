from flask import Flask, jsonify, request
from flask_cors import CORS
from data import CASES, RAW_STATS
from services.stats_service import calculate_macro_stats

app = Flask(__name__)
CORS(app)

# Processa as estatísticas iniciais
STATS = calculate_macro_stats(RAW_STATS)

@app.route('/api/cases', methods=['GET'])
def get_cases():
    return jsonify(CASES)

@app.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    case = next((c for c in CASES if c['id'] == case_id), None)
    if case:
        return jsonify(case)
    return jsonify({"error": "Case not found"}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(STATS)

@app.route('/api/analyze', methods=['POST'])
def analyze_case():
    data = request.json
    return jsonify({
        "status": "success",
        "analysis": "Análise realizada via Python Backend.",
        "ai_recommendation": "Sugerido manter a estratégia atual baseada nos subsídios fornecidos."
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
