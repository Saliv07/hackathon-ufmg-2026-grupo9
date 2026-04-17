import os

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_backend_dir)
_hackaton_dir = os.path.dirname(_project_dir)
DOCS_BASE = os.path.join(_hackaton_dir, "Docs Hackkaton", "drive-dowload")

_caso1 = os.path.join(DOCS_BASE, "Caso_01_0801234-56-2024-8-10-0001")
_caso2 = os.path.join(DOCS_BASE, "Caso_02_0654321-09-2024-8-04-0001")

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
            {
                "id": 101, "name": "01_Autos_Processo_0801234.pdf", "type": "Autos",
                "content": "Petição inicial: alegação de desconhecimento de empréstimo consignado. Pedido de R$ 15k danos morais + repetição de indébito de R$ 5.000. Autora nega ter contratado ou recebido qualquer valor.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "01_Autos_Processo_0801234-56-2024-8-10-0001.pdf"),
            },
            {
                "id": 102, "name": "02_Contrato_502348719.pdf", "type": "Subsídio",
                "content": "Contrato nº 502348719 assinado em 10/05/2022. Valor: R$ 5.000. Assinatura manuscrita presente e conforme. Parcelas de R$ 138,89/mês por 48 meses descontadas em folha.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "02_Contrato_502348719.pdf"),
            },
            {
                "id": 103, "name": "03_Extrato_Bancario.pdf", "type": "Subsídio",
                "content": "Crédito de R$ 5.000 em conta corrente UFMG da própria autora em 11/05/2022. Movimentações subsequentes: TED R$ 3.000 e PIX R$ 1.500 nos dias seguintes, indicando uso do recurso.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "03_Extrato_Bancario.pdf"),
            },
            {
                "id": 104, "name": "04_Comprovante_BACEN.pdf", "type": "Subsídio",
                "content": "Comprovante regulatório BACEN atestando operação de crédito consignado nº 502348719. Data: 10/05/2022. Valor: R$ 5.000. Operação registrada e válida junto ao Banco Central.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "04_Comprovante_de_Credito_BACEN.pdf"),
            },
            {
                "id": 105, "name": "05_Dossie_Veritas.pdf", "type": "Subsídio",
                "content": "Dossiê Veritas: Conformidade de assinatura 91%, Liveness 97.3%. Documento de identidade autêntico. Biometria facial aprovada. Nenhum indício de adulteração ou fraude detectado.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "05_Dossie_Veritas.pdf"),
            },
            {
                "id": 106, "name": "06_Demonstrativo_Evolucao_Divida.pdf", "type": "Subsídio",
                "content": "Histórico mensal de saldo devedor e pagamentos desde mai/2022. 24 parcelas pagas regularmente via desconto em folha. Saldo devedor atual: R$ 3.333,36. Nenhum atraso registrado.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "06_Demonstrativo_Evolucao_Divida.pdf"),
            },
            {
                "id": 107, "name": "07_Laudo_Referenciado.pdf", "type": "Subsídio",
                "content": "Laudo interno: canal de contratação — agência física. Agente responsável: Ag. 0234 - Belo Horizonte. Data da proposta: 09/05/2022. Taxa: 1,8% a.m. Finalidade declarada: reformas.",
                "caseNumber": "0801234-56.2024.8.10.0001",
                "filePath": os.path.join(_caso1, "07_Laudo_Referenciado.pdf"),
            },
        ],
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
        "summary": "Subsídios incompletos e fortes indícios de fraude. Crédito realizado em conta de terceiro (CEF). Ausência de contrato assinado e vídeo de liveness não localizado. Autor registrou BO.",
        "suggestion": "Propor acordo imediato. O risco de condenação é alto devido ao 'Fortuito Interno' (Súmula 479 STJ). Valor sugerido entre R$ 5.000 e R$ 7.000.",
        "documents": [
            {
                "id": 201, "name": "01_Autos_Processo_0654321.pdf", "type": "Autos",
                "content": "Petição inicial: autor afirma não possuir smartphone nem conta na CEF onde o crédito foi creditado. Alega nunca ter contratado empréstimo. Boletim de Ocorrência registrado (BO nº 2024.005432). Pede indenização por danos morais e materiais.",
                "caseNumber": "0654321-09.2024.8.04.0001",
                "filePath": os.path.join(_caso2, "01_Autos_Processo_0654321-09-2024-8-04-0001.pdf"),
            },
            {
                "id": 202, "name": "02_Comprovante_BACEN.pdf", "type": "Subsídio",
                "content": "ATENÇÃO: Crédito de R$ 25.000 realizado em conta de TERCEIRO (CEF Ag. 3245, conta 00987-6). Conta não pertence ao autor. Operação suspeita — possível fraude de identidade ou erro operacional grave.",
                "caseNumber": "0654321-09.2024.8.04.0001",
                "filePath": os.path.join(_caso2, "02_Comprovante_de_Credito_BACEN.pdf"),
            },
            {
                "id": 203, "name": "03_Demonstrativo_Evolucao_Divida.pdf", "type": "Subsídio",
                "content": "Demonstrativo de evolução da dívida: parcelas descontadas em folha do autor desde jan/2024. Autor questiona os descontos alegando não ter contratado. Saldo devedor atual: R$ 22.400.",
                "caseNumber": "0654321-09.2024.8.04.0001",
                "filePath": os.path.join(_caso2, "03_Demonstrativo_Evolucao_Divida.pdf"),
            },
            {
                "id": 204, "name": "04_Laudo_Referenciado.pdf", "type": "Subsídio",
                "content": "Laudo referenciado: canal de contratação — digital (app). Sem registro de vídeo liveness. Sem contrato físico assinado. Dados de acesso ao app provenientes de IP não habitual. Alta probabilidade de fraude.",
                "caseNumber": "0654321-09.2024.8.04.0001",
                "filePath": os.path.join(_caso2, "04_Laudo_Referenciado.pdf"),
            },
        ],
    },
]

RAW_STATS = [
    {"label": "Improcedência", "value": 46.6, "macro": "Exito"},
    {"label": "Extinção", "value": 23.0, "macro": "Exito"},
    {"label": "Parcial Procedência", "value": 20.4, "macro": "Não Êxito"},
    {"label": "Procedência", "value": 9.6, "macro": "Não Êxito"},
    {"label": "Acordo", "value": 0.5, "macro": "Não Êxito"},
]
