import pytest
from main import app, _HISTORICAL_ROWS, _HISTORICAL_HEADERS

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Injetar dados de teste controlados para garantir que o filtro funcione independente do Excel
    global _HISTORICAL_ROWS, _HISTORICAL_HEADERS
    original_rows = list(_HISTORICAL_ROWS)
    original_headers = _HISTORICAL_HEADERS
    
    _HISTORICAL_HEADERS = ["Número do processo", "Resultado macro"]
    _HISTORICAL_ROWS[:] = [
        {"Número do processo": "123", "Resultado macro": "Êxito"},
        {"Número do processo": "456", "Resultado macro": "Não Êxito"},
        {"Número do processo": "789", "Resultado macro": "Acordo"}
    ]
    
    with app.test_client() as client:
        yield client
        
    # Restaurar dados originais
    _HISTORICAL_ROWS[:] = original_rows
    _HISTORICAL_HEADERS = original_headers

def test_filter_exito_with_accent(client):
    """Certifica que filtrar por 'Êxito' funciona."""
    response = client.get('/api/historical?result=Êxito')
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["Resultado macro"] == "Êxito"

def test_filter_exito_without_accent(client):
    """Certifica que filtrar por 'Exito' (sem acento) também funciona devido à normalização."""
    response = client.get('/api/historical?result=Exito')
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["Resultado macro"] == "Êxito"

def test_filter_case_insensitive(client):
    """Certifica que o filtro não diferencia maiúsculas/minúsculas."""
    response = client.get('/api/historical?result=exito')
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert data["rows"][0]["Resultado macro"] == "Êxito"

def test_filter_no_results(client):
    """Certifica que filtros inexistentes retornam lista vazia."""
    response = client.get('/api/historical?result=Inexistente')
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 0
