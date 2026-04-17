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
RAW_STATS = [
    {"label": "Improcedência", "value": 46.6, "macro": "Exito"},
    {"label": "Extinção", "value": 23.0, "macro": "Exito"},
    {"label": "Parcial Procedência", "value": 20.4, "macro": "Não Êxito"},
    {"label": "Procedência", "value": 9.6, "macro": "Não Êxito"},
    {"label": "Acordo", "value": 0.5, "macro": "Não Êxito"},
]
