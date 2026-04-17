import pytest
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_cases(client):
    """Verifica se o endpoint de casos retorna uma lista válida."""
    response = client.get('/api/cases')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "plaintiff" in data[0]

def test_get_stats(client):
    """Verifica se o endpoint de estatísticas retorna os dados reais configurados."""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert "success_rate" in data
    assert data["success_rate"] == 69.6
    assert "total_cases" in data
    assert data["total_cases"] == 60000

def test_analyze_case(client):
    """Verifica se o endpoint de análise retorna a recomendação para um caso específico."""
    response = client.get('/api/cases/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == 1
    assert data["recommendation"] == "DEFESA"
