param (
    [Parameter(Mandatory=$true)]
    [string]$PathsFile
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "This script requires administrator privileges to create symbolic links."
    Write-Warning "Please run PowerShell as Administrator and try again."
    exit 1
}

# Source directory in the current project (absolute path)
$sourceDir = Join-Path -Path $PSScriptRoot -ChildPath ".cursor\rules\global_prompts"
$sourceDir = [System.IO.Path]::GetFullPath($sourceDir)

# Check if source directory exists
if (-not (Test-Path $sourceDir)) {
    Write-Error "Source directory not found: $sourceDir"
    exit 1
}

# Check if paths file exists
if (-not (Test-Path $PathsFile)) {
    Write-Error "Paths file not found: $PathsFile"
    exit 1
}

# Read target project paths from the file
$targetPaths = Get-Content -Path $PathsFile

foreach ($projectPath in $targetPaths) {
    # Skip empty lines
    if ([string]::IsNullOrWhiteSpace($projectPath)) {
        continue
    }

    # Create parent directory path (.cursor\rules)
    $parentDir = Join-Path -Path $projectPath -ChildPath ".cursor\rules"
    
    # Create the parent directory if it doesn't exist
    if (-not (Test-Path $parentDir)) {
        Write-Host "Creating directory: $parentDir"
        New-Item -Path $parentDir -ItemType Directory -Force | Out-Null
    }
    
    # Target directory path
    $targetDir = Join-Path -Path $projectPath -ChildPath ".cursor\rules\global_prompts"
    
    # Remove existing directory or symlink if it exists
    if (Test-Path $targetDir) {
        Write-Host "Removing existing directory/link: $targetDir"
        Remove-Item -Path $targetDir -Force -Recurse
    }
    
    # Create symbolic link
    Write-Host "Creating symbolic link at: $targetDir"
    try {
        New-Item -ItemType SymbolicLink -Path $targetDir -Target $sourceDir -Force | Out-Null
        Write-Host "Symbolic link created successfully."
    }
    catch {
        Write-Error "Failed to create symbolic link: $_"
    }
}

Write-Host "Symbolic links have been created for all specified projects." 