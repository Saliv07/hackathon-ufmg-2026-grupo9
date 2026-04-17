def calculate_macro_stats(raw_data):
    """
    Calcula as taxas macro de sucesso e derrota baseadas nos dados detalhados.
    """
    success_rate = sum(item["value"] for item in raw_data if item["macro"] == "Exito")
    loss_rate = sum(item["value"] for item in raw_data if item["macro"] == "Não Êxito")
    
    # Arredondar para evitar problemas de precisão de float
    success_rate = round(success_rate, 1)
    loss_rate = round(loss_rate, 1)

    return {
        "total_cases": 60000,
        "success_rate": success_rate,
        "loss_rate": loss_rate,
        "agreement_rate": 0.5,
        "detailed": raw_data
    }
