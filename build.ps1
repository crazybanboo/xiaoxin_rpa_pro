#!/usr/bin/env powershell
<#
.SYNOPSIS
    Xiaoxin RPA Pro - Nuitka Build Script
.DESCRIPTION
    Package Python project to standalone Windows executable using Nuitka
.AUTHOR
    Xiaoxin RPA Pro
#>

# Set error handling
$ErrorActionPreference = "Stop"

# Output functions
function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

# Main function
function Main {
    Write-Info "Starting Xiaoxin RPA Pro packaging process..."
    
    # Check current directory
    $currentDir = Get-Location
    Write-Info "Current working directory: $currentDir"
    
    # Check if main.py exists
    if (-not (Test-Path "main.py")) {
        Write-Error "main.py not found, please run this script from the project root directory"
        exit 1
    }
    
    # Activate virtual environment
    Write-Info "Activating virtual environment..."
    if (Test-Path ".env\Scripts\activate.ps1") {
        & ".env\Scripts\activate.ps1"
        Write-Info "Virtual environment activated"
    } else {
        Write-Warning "Virtual environment not found, using system Python"
    }
    
    # Check Nuitka installation
    Write-Info "Checking Nuitka installation..."
    try {
        $nuitkaVersion = & python -m nuitka --version 2>$null
        Write-Info "Nuitka version: $nuitkaVersion"
    } catch {
        Write-Error "Nuitka not installed, please install it first: pip install nuitka"
        exit 1
    }
    
    # Create output directory
    $outputDir = "dist"
    if (Test-Path $outputDir) {
        Write-Info "Cleaning old output directory..."
        Remove-Item $outputDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Info "Created output directory: $outputDir"
    
    # Define data files and directories to include
    $dataFiles = @(
        "config",
        "templates", 
        "workflows"
    )
    
    # Build Nuitka command arguments
    $nuitkaArgs = @(
        "--standalone",
        "--output-dir=$outputDir",
        "--output-filename=xiaoxin_rpa_pro.exe",
        "--product-name=Xiaoxin RPA Pro",
        "--file-version=1.0.2",
        "--product-version=1.0.2",
        "--file-description=Python-based RPA automation software",
        "--copyright=Copyright (c) 2024 Xiaoxin RPA Pro",
        "--enable-plugin=anti-bloat",
        "--follow-imports",
        "--assume-yes-for-downloads"
    )
    
    # Add data file include parameters
    foreach ($dataFile in $dataFiles) {
        if (Test-Path $dataFile) {
            $nuitkaArgs += "--include-data-dir=$dataFile=$dataFile"
            Write-Info "Including data directory: $dataFile"
        } else {
            Write-Warning "Data directory does not exist, skipping: $dataFile"
        }
    }
    
    # Add specific module includes
    $includeModules = @(
        "cv2",
        "numpy", 
        "PIL",
        "pyautogui",
        "win32api",
        "win32gui",
        "win32con",
        "pynput",
        "keyboard",
        "mouse",
        "yaml",
        "loguru",
        "psutil"
    )
    
    foreach ($module in $includeModules) {
        $nuitkaArgs += "--include-module=$module"
    }
    
    # Add main program file
    $nuitkaArgs += "main.py"
    
    # Execute Nuitka packaging
    Write-Info "Starting Nuitka compilation..."
    Write-Info "Executing command: python -m nuitka $($nuitkaArgs -join ' ')"
    
    try {
        & python -m nuitka @nuitkaArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Info "Nuitka compilation completed successfully"
        } else {
            Write-Error "Nuitka compilation failed with exit code: $LASTEXITCODE"
            exit $LASTEXITCODE
        }
    } catch {
        Write-Error "Exception occurred during Nuitka compilation: $($_.Exception.Message)"
        exit 1
    }
    
    # Copy additional resource files to output directory
    Write-Info "Copying additional resource files..."
    $additionalFiles = @(
        "README.md",
        "docs\README.md"
    )
    
    foreach ($file in $additionalFiles) {
        if (Test-Path $file) {
            $destPath = Join-Path $outputDir (Split-Path $file -Leaf)
            Copy-Item $file $destPath -Force
            Write-Info "Copied file: $file -> $destPath"
        }
    }
    
    # Create sample run script
    $runScript = @"
@echo off
echo Xiaoxin RPA Pro - Usage Examples
echo.
echo Usage:
echo xiaoxin_rpa_pro.exe --workflow basic_example
echo xiaoxin_rpa_pro.exe --workflow wxwork --config config/wxwork_strategy.yaml
echo.
echo For more options run: xiaoxin_rpa_pro.exe --help
echo.
pause
"@
    
    $runScriptPath = Join-Path $outputDir "Usage_Examples.bat"
    Set-Content -Path $runScriptPath -Value $runScript -Encoding UTF8
    Write-Info "Created usage examples script: $runScriptPath"
    
    # Display packaging results
    Write-Info "Packaging completed!"
    Write-Info "Output directory: $outputDir"
    
    if (Test-Path (Join-Path $outputDir "xiaoxin_rpa_pro.exe")) {
        $exeSize = (Get-Item (Join-Path $outputDir "xiaoxin_rpa_pro.exe")).Length / 1MB
        Write-Info "Executable size: $([math]::Round($exeSize, 2)) MB"
        Write-Info "Executable path: $(Join-Path $outputDir 'xiaoxin_rpa_pro.exe')"
    }
    
    # List output directory contents
    Write-Info "Output directory contents:"
    Get-ChildItem $outputDir | ForEach-Object {
        if ($_.PSIsContainer) {
            Write-Host "  Folder: $($_.Name)" -ForegroundColor Cyan
        } else {
            $sizeKB = [math]::Round($_.Length / 1KB, 2)
            Write-Host "  File: $($_.Name) ($sizeKB KB)" -ForegroundColor White
        }
    }
    
    Write-Info "Packaging process completed successfully!"
}

# Script entry point
try {
    Main
} catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}