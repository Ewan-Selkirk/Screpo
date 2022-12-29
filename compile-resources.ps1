#!/usr/bin/pwsh

./venv\Scripts\Activate.ps1

if (Test-Path src\resources.qrc) {
    pyside6-rcc --no-compress .\src\resources.qrc -o .\src\resources.py
    Write-Host "Compiled qrc file to Python file"

    Write-Host "Working bullshit to make compiled file work on Windows..."

    $file = Get-Content .\src\resources.py
    $file[6] += "import PySide6.QtSvg`n"
    $file | Set-Content .\src\resources.py

    Write-Host "Finished!"
} else {
    Write-Host "Could not find file 'resources.qrc' in directory 'src'..."
    Write-Host "Aborting..."
}

timeout /t 5