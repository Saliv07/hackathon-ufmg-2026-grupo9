from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend to access the backend

# Case Data from Documentation
CASES = [
    { 
        "id": 1, 
        "number": "0801234-56.2024.8.10.0001", 
        "plaintiff": "Maria das Graças Silva Pereira", 
        "type": "Empréstimo Consignado", 
        "risk": "Baixo", 
        "value": "R$ 20.000,00", 
        "askedValue": 20000,
        "recommendation": "DEFESA",
        "summary": "Caso robusto com subsídios completos. Assinatura manuscrita presente e validada. Dossiê Veritas confirma conformidade biométrica (91%). Extrato bancário prova crédito em conta própria e movimentação subsequente.",
        "suggestion": "Manter tese de defesa. As provas documentais são sólidas e contradizem a versão da autora de que nunca recebeu o dinheiro ou contratou o serviço.",
        "documents": [
            { "id": 101, "name": "Petição Inicial - Maria.pdf", "type": "Autos", "content": "Alegação de desconhecimento de empréstimo. Pedido de R$ 15k danos morais + repetição de indébito.", "caseNumber": "0801234-56.2024.8.10.0001" },
            { "id": 102, "name": "Contrato Assinado - Maria.pdf", "type": "Subsídio", "content": "Contrato nº 502348719 assinado em 10/05/2022. Valor: R$ 5.000.", "caseNumber": "0801234-56.2024.8.10.0001" },
            { "id": 103, "name": "Extrato Bancário - Maria.pdf", "type": "Subsídio", "content": "Crédito de R$ 5.000 em conta UFMG. Movimentações: TED R$ 3k, PIX R$ 1.5k.", "caseNumber": "0801234-56.2024.8.10.0001" },
            { "id": 104, "name": "Dossiê Veritas - Maria.pdf", "type": "Subsídio", "content": "Conformidade: Assinatura 91%, Liveness 97.3%.", "caseNumber": "0801234-56.2024.8.10.0001" }
        ]
    },
    { 
        "id": 2, 
        "number": "0654321-09.2024.8.04.0001", 
        "plaintiff": "José Raimundo Oliveira Costa", 
        "type": "Empréstimo Consignado", 
        "risk": "Alto", 
        "value": "R$ 25.000,00", 
        "askedValue": 25000,
        "recommendation": "ACORDO",
        "summary": "Subsídios incompletos e fortes indícios de fraude. Crédito realizado em conta de terceiro. Ausência de contrato assinado e vídeo de liveness não localizado.",
        "suggestion": "Propor acordo imediato. O risco de condenação é alto devido ao \"Fortuito Interno\" (Súmula 479 STJ). Valor sugerido entre R$ 5.000 e R$ 7.000.",
        "documents": [
            { "id": 201, "name": "Petição Inicial - José.pdf", "type": "Autos", "content": "Autor afirma não possuir smartphone nem conta na CEF onde o crédito caiu. BO registrado.", "caseNumber": "0654321-09.2024.8.04.0001" },
            { "id": 202, "name": "Comprovante BACEN - José.pdf", "type": "Subsídio", "content": "Crédito em conta de TERCEIRO (CEF Ag 3245).", "caseNumber": "0654321-09.2024.8.04.0001" },
            { "id": 203, "name": "Boletim de Ocorrência - José.pdf", "type": "Autos", "content": "BO nº 2024.005432 - Fraude em empréstimo consignado.", "caseNumber": "0654321-09.2024.8.04.0001" }
        ]
    },
]

# Historical Stats from Documentation
STATS = {
    "total_cases": 60000,
    "success_rate": 70,  # 46.6% Improcedencia + 23.0% Extincao
    "loss_rate": 30,     # 20.4% Parcial + 9.6% Procedencia
    "agreement_rate": 0.5,
    "detailed": [
        {"label": "Improcedência", "value": 46.6, "macro": "Exito"},
        {"label": "Extinção", "value": 23.0, "macro": "Exito"},
        {"label": "Parcial Procedência", "value": 20.4, "macro": "Não Êxito"},
        {"label": "Procedência", "value": 9.6, "macro": "Não Êxito"},
        {"label": "Acordo", "value": 0.5, "macro": "Não Êxito"},
    ]
}

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
    # Here we would normally call an LLM
    # For now, we simulate AI processing
    return jsonify({
        "status": "success",
        "analysis": "Análise realizada via Python Backend.",
        "ai_recommendation": "Sugerido manter a estratégia atual baseada nos subsídios fornecidos."
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
