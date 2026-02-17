# GitHub Setup Helper Script for Windows PowerShell
# This script helps push the eService AI Platform to GitHub

Write-Host "================================" -ForegroundColor Cyan
Write-Host "eService AI Platform - GitHub Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
$ghInstalled = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($ghInstalled) {
    Write-Host "✓ GitHub CLI (gh) is installed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Creating repository on GitHub..." -ForegroundColor Yellow
    
    $currentLocation = Get-Location
    Set-Location "c:\Users\budis\Downloads\EBOOK\!CODE\Project"
    
    gh repo create eservice-ai-platform `
        --public `
        --description "Production-grade intelligent customer service platform with LLM/RAG integration" `
        --source=. `
        --org AI-Projects-list `
        --remote origin `
        --push
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Repository created and code pushed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "View your repository at:" -ForegroundColor Cyan
        Write-Host "https://github.com/AI-Projects-list/eservice-ai-platform" -ForegroundColor Blue
    } else {
        Write-Host "✗ Failed to create repository or push code" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "✗ GitHub CLI (gh) is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "OPTION 1: Install GitHub CLI (Recommended)" -ForegroundColor Yellow
    Write-Host "  Install from: https://cli.github.com/" -ForegroundColor Gray
    Write-Host "  Then run this script again"
    Write-Host ""
    Write-Host "OPTION 2: Manual GitHub Setup" -ForegroundColor Yellow
    Write-Host "  1. Go to https://github.com/orgs/AI-Projects-list/repositories" -ForegroundColor Gray
    Write-Host "  2. Click 'New repository'" -ForegroundColor Gray
    Write-Host "  3. Name it: eservice-ai-platform" -ForegroundColor Gray
    Write-Host "  4. Description: Production-grade intelligent customer service platform" -ForegroundColor Gray
    Write-Host "  5. Choose 'Public'" -ForegroundColor Gray
    Write-Host "  6. Click 'Create repository'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Then run these commands in PowerShell:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host 'cd "c:\Users\budis\Downloads\EBOOK\!CODE\Project"' -ForegroundColor Cyan
    Write-Host "git remote add origin https://github.com/AI-Projects-list/eservice-ai-platform.git" -ForegroundColor Cyan
    Write-Host "git branch -M main" -ForegroundColor Cyan
    Write-Host "git push -u origin main" -ForegroundColor Cyan
    Write-Host ""
}
