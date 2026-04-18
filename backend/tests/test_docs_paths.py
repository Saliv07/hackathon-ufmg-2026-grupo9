import os
import pytest
from main import app
from data import CASES, DOCS_BASE

@pytest.fixture
def client():
    # Garantir que a porta mockada de teste não importe
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_documents_exist_in_data():
    """Verifica se os arquivos estáticos referenciados nos metadados do caso realmente existem"""
    for case in CASES:
        for doc in case['documents']:
            file_path = doc.get('filePath')
            assert os.path.exists(file_path), \
                   f"Documento '{doc.get('name')}' não encontrado em {file_path}. Verifique DOCS_BASE: {DOCS_BASE}"

def test_api_serve_document_endpoint():
    """Testa se a API de fato retorna o arquivo (status 200) ou se falha ao encontrar"""
    # Vamos pegar o primeiro documento do primeiro caso, se existir
    if not CASES or not CASES[0]['documents']:
        pytest.skip("Nenhum caso ou documento disponível para testar")
        
    case_id = CASES[0]['id']
    doc_id = CASES[0]['documents'][0]['id']
    
    with app.test_client() as client:
        response = client.get(f'/api/cases/{case_id}/documents/{doc_id}/file')
        assert response.status_code == 200, "O servidor não conseguiu enviar o arquivo PDF via API."
        assert response.headers['Content-Type'] == 'application/pdf'
