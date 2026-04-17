#!/bin/bash
# Pipeline completo: feature engineering -> treino -> teste de inferência
set -e

echo "========================================"
echo "1. PREPARAÇÃO DOS DADOS"
echo "========================================"
python3 01_prepare_data.py --input base.xlsx --output artefatos/

echo ""
echo "========================================"
echo "2. TREINO DO MODELO"
echo "========================================"
python3 02_train_model.py --input artefatos/

echo ""
echo "========================================"
echo "3. TESTE DE INFERÊNCIA"
echo "========================================"
python3 03_inference.py

echo ""
echo "✓ Pipeline completo executado com sucesso!"
