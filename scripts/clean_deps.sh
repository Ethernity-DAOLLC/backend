#!/bin/bash

# Script para limpiar environment y reinstalar solo producción
# Uso: bash scripts/clean_deps.sh

set -e

echo "🧹 Cleaning development environment..."
echo ""

# OPCIÓN 1: Recrear venv desde cero
# =====================
echo "Option 1: Recreate virtual environment (RECOMENDED)"
echo "This will delete venv/ and create a fresh one"
read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting venv/..."
    rm -rf venv/
    
    echo "Creating new venv..."
    python3 -m venv venv
    
    echo "Activating venv..."
    source venv/bin/activate
    
    echo "Installing production dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✅ Done! Clean production environment ready"
    exit 0
fi

# OPCIÓN 2: Desinstalar solo dev dependencies
# =====================
echo ""
echo "Option 2: Uninstall only dev dependencies"
read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    source venv/bin/activate
    
    echo "Uninstalling dev dependencies..."
    pip uninstall -y pytest pytest-asyncio pytest-cov httpx faker
    pip uninstall -y black flake8 isort mypy
    pip uninstall -y ipython ipdb
    
    echo "✅ Done! Dev dependencies removed"
    exit 0
fi

echo "No changes made."