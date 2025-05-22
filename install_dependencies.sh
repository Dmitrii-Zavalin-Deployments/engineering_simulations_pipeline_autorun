#!/bin/bash
set -e

echo "🔍 Checking Python version..."
python --version

echo "🔄 Updating pip..."
python -m pip install --upgrade pip

echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt || echo "⚠️ Pip install failed, trying Conda"

if ! pip show pyopenvdb; then
  echo "⚠️ Trying Conda installation for PyOpenVDB..."
  conda install -c conda-forge pyopenvdb || echo "🚨 Conda install failed!"
fi

echo "✅ Dependency installation complete!"


