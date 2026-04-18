import os
import io
import time
import base64
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
from data import CASES, RAW_STATS
from services.stats_service import calculate_macro_stats, load_historical_snapshot

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: OpenAI API Key loaded: {bool(api_key)}")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

client = OpenAI(api_key=api_key)

STATS = calculate_macro_stats(RAW_STATS)

ALLOWED_MODELS = {'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4o', 'gpt-4o-mini'}

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


# ── Historical Base ────────────────────────────────────────────────────────────

# Cache: load once at startup
_HISTORICAL_HEADERS = None
_HISTORICAL_ROWS = []

def _load_historical():
    global _HISTORICAL_HEADERS, _HISTORICAL_ROWS, STATS
    try:
        headers, rows, policy_projection = load_historical_snapshot()
        _HISTORICAL_HEADERS = headers
        _HISTORICAL_ROWS = rows
        STATS = calculate_macro_stats(RAW_STATS, policy_projection=policy_projection)

        if rows:
            print(f"DEBUG: Historical base loaded: {len(rows)} rows")
        else:
            print("WARNING: Historical base not found; dashboard projection disabled")
    except Exception as e:
        STATS = calculate_macro_stats(RAW_STATS)
        print(f"WARNING: Could not load historical base: {e}")

_load_historical()

@app.route('/api/historical', methods=['GET'])
def get_historical():
    """Serve paginated rows from cached Excel data."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '').strip().lower()
    result_filter = request.args.get('result', '').strip()
    sort_by = request.args.get('sort_by', '')
    order = request.args.get('order', 'asc') # 'asc' ou 'desc'

    filtered = _HISTORICAL_ROWS
    if search:
        filtered = [r for r in filtered
                    if search in str(r.get("Número do processo", "")).lower()
                    or search in str(r.get("Assunto", "")).lower()
                    or search in str(r.get("UF", "")).lower()]
    if result_filter:
        # Normaliza o filtro para facilitar a comparação (ex: 'Exito' ou 'Êxito' -> 'exito')
        f = result_filter.lower().replace('ê', 'e')
        filtered = [r for r in filtered 
                    if str(r.get("Resultado macro", "")).lower().replace('ê', 'e') == f]

    # Ordenação
    if _HISTORICAL_HEADERS and sort_by in _HISTORICAL_HEADERS:
        def sort_key(row):
            val = row.get(sort_by, "")
            # Tenta converter para número se a coluna for de valores financeiros
            if sort_by in ["Valor da causa", "Valor da condenação/indenização"]:
                try:
                    return float(val) if val != "" else 0.0
                except:
                    return 0.0
            return str(val).lower()

        filtered = sorted(filtered, key=sort_key, reverse=(order == 'desc'))

    total = len(filtered)
    start = (page - 1) * per_page
    page_rows = filtered[start:start + per_page]

    return jsonify({
        "headers": _HISTORICAL_HEADERS,
        "rows": page_rows,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    })


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

    # Monta contexto dos documentos abertos no viewer
    docs_context = ""
    if open_documents:
        docs_context = "\n\n## Documentos Abertos no Visualizador\n"
        for doc in open_documents:
            title = doc.get('title') or 'Documento'
            doc_type = doc.get('type', '')
            content = doc.get('content', '') or '(sem conteúdo extraído)'
            docs_context += f"\n### {title} ({doc_type})\n{content}\n"

    # Monta contexto do dashboard (base histórica)
    policy_projection = STATS.get("policy_projection")
    policy_projection_context = ""
    if policy_projection:
        projection_mode = (
            "política híbrida (regras + XGBoost)"
            if policy_projection.get("projection_type") == "hybrid_policy_engine_v2_1"
            else "política determinística"
        )
        policy_projection_context = (
            f"\n- Cenário com política v2.1 usando {projection_mode}: gasto total histórico de "
            f"R$ {policy_projection['actual_total_cost']:,.2f} cairia para "
            f"R$ {policy_projection['projected_total_cost']:,.2f}, com economia "
            f"estimada de R$ {policy_projection['estimated_savings']:,.2f}."
        )

    stats_context = (
        "\n\n## Base Histórica — Banco UFMG (60.000 processos)\n"
        f"- Taxa de Êxito do banco: **{STATS['success_rate']}%** "
        f"(Improcedência + Extinção = banco ganha)\n"
        f"- Taxa de Não Êxito: **{STATS['loss_rate']}%** "
        f"(Parcial procedência + Procedência = banco perde)\n"
        f"- Acordos realizados até hoje: **{STATS['agreement_rate']}%** "
        f"(apenas 280 de 60.000 casos)\n"
        "- Detalhamento micro: "
        + ", ".join(f"{d['label']} {d['value']}%" for d in STATS['detailed'])
        + policy_projection_context
        + "\n- **Insight**: há 18.267 casos de não êxito que poderiam ter sido acordados "
        "com valor controlado, potencialmente reduzindo o ticket médio de condenação em ~60%."
    )

    system_prompt = (
        "Você é um Agente Jurídico especialista em política de acordos para o Banco UFMG. "
        "Sua função é analisar processos de não reconhecimento de contratação de empréstimo consignado "
        "e recomendar ACORDO ou DEFESA com base nos documentos e na política do banco.\n\n"
        "Use os dados da Base Histórica para embasar probabilidades e estimativas financeiras. "
        "Use os Documentos Abertos como fonte primária para analisar o caso específico. "
        "Se o usuário citar um trecho entre aspas (precedido por '>'), analise especificamente aquele trecho. "
        "Seja objetivo, claro e fundamente suas conclusões nos fatos disponíveis."
    )

    user_content = (
        f"## Dados do Processo\n{case_context}"
        f"{docs_context}"
        f"{stats_context}"
        f"\n\n## Pergunta do Advogado\n{user_message}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
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
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        # OCR para imagens usando GPT-4o-mini
        try:
            print(f"DEBUG: Iniciando OCR para {filename}...")
            base64_image = base64.b64encode(file_bytes).decode('utf-8')
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcreva todo o texto desta imagem. Se for uma conversa de WhatsApp ou chat, identifique os interlocutores e formate como um diálogo. Se houver datas ou nomes importantes, destaque-os."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
            )
            content = f"Transcrição da Imagem ({filename}):\n\n" + response.choices[0].message.content
        except Exception as e:
            print(f"ERROR: OCR falhou: {e}")
            content = f"Erro ao processar imagem: {str(e)}"
        
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        file_url = f"/api/uploads/{unique_name}"

    elif filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg', '.webm')):
        # Transcrição de áudio usando Whisper
        try:
            print(f"DEBUG: Iniciando transcrição de áudio para {filename}...")
            audio_file = io.BytesIO(file_bytes)
            audio_file.name = filename # Necessário para o client da OpenAI detectar o formato
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            content = f"Transcrição de Áudio ({filename}):\n\n" + transcription.text
        except Exception as e:
            print(f"ERROR: Transcrição falhou: {e}")
            content = f"Erro ao transcrever áudio: {str(e)}"
            
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        file_url = f"/api/uploads/{unique_name}"

    else:
        # Outros arquivos: salva e serve
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
