import pytest
from services.stats_service import calculate_macro_stats

def test_calculate_macro_stats():
    raw_data = [
        {"label": "Ganhou", "value": 60.0, "macro": "Exito"},
        {"label": "Perdeu", "value": 40.0, "macro": "Não Êxito"}
    ]
    stats = calculate_macro_stats(raw_data)
    assert stats["success_rate"] == 60.0
    assert stats["loss_rate"] == 40.0
    assert stats["total_cases"] == 60000 # Default constant
    assert len(stats["detailed"]) == 2

def test_calculate_macro_stats_complex():
    raw_data = [
        {"label": "A", "value": 10.0, "macro": "Exito"},
        {"label": "B", "value": 20.0, "macro": "Exito"},
        {"label": "C", "value": 30.0, "macro": "Não Êxito"},
        {"label": "D", "value": 40.0, "macro": "Não Êxito"}
    ]
    stats = calculate_macro_stats(raw_data)
    assert stats["success_rate"] == 30.0
    assert stats["loss_rate"] == 70.0
