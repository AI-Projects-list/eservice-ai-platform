#!/bin/bash
# GitHub Setup Helper Script
# This script helps push the eService AI Platform to GitHub

echo "================================"
echo "eService AI Platform - GitHub Setup"
echo "================================"
echo ""
echo "This script will help you push the project to GitHub."
echo ""

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI (gh) is installed"
    echo ""
    echo "Creating repository on GitHub..."
    gh repo create eservice-ai-platform \
        --public \
        --description "Production-grade intelligent customer service platform with LLM/RAG integration" \
        --source=. \
        --org AI-Projects-list \
        --remote origin \
        --push
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Repository created and code pushed successfully!"
        echo ""
        echo "View your repository at:"
        echo "https://github.com/AI-Projects-list/eservice-ai-platform"
    else
        echo "✗ Failed to create repository or push code"
        exit 1
    fi
else
    echo "✗ GitHub CLI (gh) is not installed"
    echo ""
    echo "Option 1: Install GitHub CLI and run:"
    echo "  gh repo create eservice-ai-platform --public --source=. --org AI-Projects-list --remote origin --push"
    echo ""
    echo "Option 2: Manual setup (on GitHub):"
    echo "  1. Go to https://github.com/orgs/AI-Projects-list/repositories"
    echo "  2. Click 'New repository'"
    echo "  3. Name it: eservice-ai-platform"
    echo "  4. Add description: Production-grade intelligent customer service platform"
    echo "  5. Choose 'Public'"
    echo "  6. Click 'Create repository'"
    echo ""
    echo "  Then run:"
    echo "    git remote add origin https://github.com/AI-Projects-list/eservice-ai-platform.git"
    echo "    git branch -M main"
    echo "    git push -u origin main"
    exit 1
fi
