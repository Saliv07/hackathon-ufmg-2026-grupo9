import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from data import CASES, RAW_STATS
from services.stats_service import calculate_macro_stats

# Carrega variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path="../.env")
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: OpenAI API Key loaded: {bool(api_key)}")

app = Flask(__name__)
CORS(app)

# Configuração do Cliente OpenAI
client = OpenAI(api_key=api_key)

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
    user_message = data.get('message', '')
    case_context = data.get('case_context', '')

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Atualizado para gpt-4o para maior estabilidade
            messages=[
                {"role": "system", "content": "Você é um Agente Jurídico especialista em política de acordos para o Banco UFMG. Analise o caso com base nos subsídios e forneça uma recomendação técnica clara."},
                {"role": "user", "content": f"Contexto do Caso: {case_context}\n\nPergunta do Advogado: {user_message}"}
            ],
            temperature=0.3
        )
        
        analysis_content = response.choices[0].message.content
        
        return jsonify({
            "status": "success",
            "analysis": analysis_content,
            "ai_recommendation": "Recomendação gerada dinamicamente pelo GPT-4o."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
