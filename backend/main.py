import os
import io
import time
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
from data import CASES, RAW_STATS
from services.stats_service import calculate_macro_stats

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: OpenAI API Key loaded: {bool(api_key)}")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

client = OpenAI(api_key=api_key)

STATS = calculate_macro_stats(RAW_STATS)

ALLOWED_MODELS = {'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'}

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Cases ──────────────────────────────────────────────────────────────────────

@app.route('/api/cases', methods=['GET'])
def get_cases():
    # Não expõe filePath para o frontend
    safe = []
    for c in CASES:
        case_copy = {k: v for k, v in c.items() if k != 'documents'}
        case_copy['documents'] = [
            {k: v for k, v in d.items() if k != 'filePath'}
            for d in c['documents']
        ]
        safe.append(case_copy)
    return jsonify(safe)


@app.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    case = next((c for c in CASES if c['id'] == case_id), None)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    case_copy = {k: v for k, v in case.items() if k != 'documents'}
    case_copy['documents'] = [
        {k: v for k, v in d.items() if k != 'filePath'}
        for d in case['documents']
    ]
    return jsonify(case_copy)


@app.route('/api/cases/<int:case_id>/documents/<int:doc_id>/file', methods=['GET'])
def serve_document(case_id, doc_id):
    case = next((c for c in CASES if c['id'] == case_id), None)
    if not case:
        return jsonify({"error": "Caso não encontrado"}), 404

    doc = next((d for d in case['documents'] if d['id'] == doc_id), None)
    if not doc:
        return jsonify({"error": "Documento não encontrado"}), 404

    file_path = doc.get('filePath')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo PDF não disponível no servidor"}), 404

    return send_file(file_path, mimetype='application/pdf', as_attachment=False)


# ── Stats ──────────────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(STATS)


# ── AI Analysis ────────────────────────────────────────────────────────────────

@app.route('/api/analyze', methods=['POST'])
def analyze_case():
    data = request.json
    user_message = data.get('message', '')
    case_context = data.get('case_context', '')
    open_documents = data.get('open_documents', [])
    model = data.get('model', 'gpt-4o')
    temperature = float(data.get('temperature', 0.3))
    temperature = max(0.0, min(1.0, temperature))

    if model not in ALLOWED_MODELS:
        model = 'gpt-4o'

    docs_context = ""
    if open_documents:
        docs_context = "\n\nDocumentos Abertos no Visualizador:\n"
        for doc in open_documents:
            title = doc.get('title') or 'Documento'
            doc_type = doc.get('type', '')
            content = doc.get('content', '')
            docs_context += f"--- {title} ({doc_type}) ---\n{content}\n\n"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um Agente Jurídico especialista em política de acordos para o Banco UFMG. "
                        "Analise o caso com base nos subsídios e nos documentos abertos fornecidos. "
                        "Se o usuário mencionar um documento, use as informações do contexto de 'Documentos Abertos'. "
                        "Seja objetivo, claro e fundamente suas análises nos documentos disponíveis."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Contexto do Caso: {case_context}{docs_context}\n\nPergunta do Advogado: {user_message}",
                },
            ],
            temperature=temperature,
        )

        analysis_content = response.choices[0].message.content
        return jsonify({
            "status": "success",
            "analysis": analysis_content,
            "model_used": model,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── File Upload ─────────────────────────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Nome de arquivo inválido"}), 400

    filename = secure_filename(file.filename)
    # Garante nome único para evitar colisões
    unique_name = f"{int(time.time() * 1000)}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    content = f"Documento '{filename}' enviado pelo advogado."
    file_bytes = file.read()

    # Tenta extrair texto de PDF
    if filename.lower().endswith('.pdf'):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages[:5]:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
            if pages_text:
                content = "\n\n".join(pages_text)[:5000]
        except Exception:
            pass
        # Salva o PDF para visualização
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        file_url = f"/api/uploads/{unique_name}"
    elif filename.lower().endswith('.txt'):
        try:
            content = file_bytes.decode('utf-8', errors='ignore')[:5000]
        except Exception:
            pass
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        file_url = f"/api/uploads/{unique_name}"
    else:
        # Imagens e outros: salva e serve
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        file_url = f"/api/uploads/{unique_name}"

    doc_id = int(time.time() * 1000)
    return jsonify({
        "id": doc_id,
        "name": filename,
        "type": "Anexo",
        "content": content,
        "fileUrl": file_url,
        "caseNumber": "",
    })


@app.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    safe_name = secure_filename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(file_path, as_attachment=False)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
