# Politica de Acordo - Enter AI 

## 1. OBJETIVO

Estabelecer critérios objetivos e auditáveis para decisão entre 
*defesa judicial* e *proposta de acordo* em ações declaratórias 
de inexistência de débito envolvendo empréstimos consignados, 
garantindo consistência entre escritórios e maximizando a 
eficiência financeira do contencioso.

## 2. ESCOPO

Aplica-se exclusivamente a ações cíveis em que a parte autora 
alega não reconhecer a contratação de empréstimo consignado 
junto ao Banco UFMG.

## 3. CRITÉRIOS DE DECISÃO

### 3.1 Classificação dos Subsídios

*Subsídios CRÍTICOS* (alto poder probatório):
•⁠  ⁠Contrato (cédula de crédito bancário)
•⁠  ⁠Extrato bancário comprovando o crédito
•⁠  ⁠Comprovante de Crédito BACEN

*Subsídios COMPLEMENTARES* (reforço probatório):
•⁠  ⁠Dossiê grafotécnico/documental
•⁠  ⁠Demonstrativo de Evolução da Dívida
•⁠  ⁠Laudo Referenciado

### 3.2 Análise do Dossiê (quando presente)

O Dossiê deve ser classificado em:
•⁠  ⁠*CONFORME*: Reforça a defesa.
•⁠  ⁠*NÃO CONFORME: Recomenda acordo imediato* independente dos demais subsídios.
•⁠  ⁠*AUSENTE ou INCOMPLETO*: tratado como neutro (não reforça defesa nem prejudica).

### 3.3 Matriz de Recomendação

| Cenário | Recomendação |
|---|---|
| Dossiê NÃO CONFORME | *ACORDO* (prioritário) |
| 0–1 subsídios críticos presentes | *ACORDO* |
| 2 subsídios críticos + Dossiê CONFORME ou ausente | *AVALIAR* (modelo ML) |
| 3 subsídios críticos presentes | *DEFESA* |
| UF de alto risco (AM, AP) com ≤ 2 subsídios críticos | *ACORDO* |

## 4. CÁLCULO DO VALOR DO ACORDO

#### 4.1 Fórmula base

*Valor alvo do acordo = Valor da Causa × Fator Base (30%)*

Esta é a prática consolidada dos acordos históricos do banco 
(R² = 0,67 contra base de 280 acordos), validada por 
correlação de 0,82 com o valor da causa.

### 4.2 Ajustes por perfil (pequenos, aditivos)

| Cenário | Ajuste no fator |
|---|:-:|
| 3 subsídios críticos presentes (banco forte) | –3 pp (27%) |
| 0–1 subsídio crítico (banco fraco) | +3 pp (33%) |
| Dossiê NÃO CONFORME | +5 pp (35%) |
| UF de alto risco (AM, AP) | +2 pp |
| UF de baixo risco (MA, PI, TO...) | –2 pp |

### 4.3 Faixa de negociação

| Valor | Referência histórica |
|---|---|
| Abertura da negociação | P25 da faixa (valor × 24–26%) |
| Alvo principal | P50 da faixa (valor × 28–30%) |
| Máximo aceitável | P75 da faixa (valor × 35%) |
| Teto absoluto | P90 da faixa (valor × 40%) |