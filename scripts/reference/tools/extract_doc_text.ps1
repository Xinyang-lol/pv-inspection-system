param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$word = $null
$document = $null

try {
    $resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
    $outputDirectory = Split-Path -Path $OutputPath -Parent
    if (-not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $document = $word.Documents.Open($resolvedInput, $false, $true)
    $content = $document.Content.Text

    [System.IO.File]::WriteAllText($OutputPath, $content, [System.Text.Encoding]::UTF8)
}
finally {
    if ($document -ne $null) {
        $document.Close()
    }
    if ($word -ne $null) {
        $word.Quit()
    }
}
