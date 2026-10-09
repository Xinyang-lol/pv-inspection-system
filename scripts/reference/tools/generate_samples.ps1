Add-Type -AssemblyName System.Drawing

$outputDir = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\samples"
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

function New-Canvas {
    param(
        [int]$Width = 1280,
        [int]$Height = 720
    )

    $bitmap = New-Object System.Drawing.Bitmap($Width, $Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(16, 28, 46))

    $skyBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Rectangle(0, 0, $Width, $Height)),
        [System.Drawing.Color]::FromArgb(28, 61, 96),
        [System.Drawing.Color]::FromArgb(8, 18, 30),
        90
    )
    $graphics.FillRectangle($skyBrush, 0, 0, $Width, $Height)
    $skyBrush.Dispose()

    return @{ Bitmap = $bitmap; Graphics = $graphics }
}

function Draw-PanelField {
    param(
        [System.Drawing.Graphics]$Graphics,
        [int]$Width,
        [int]$Height
    )

    $fieldBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(34, 53, 77))
    $panelBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(24, 53, 94))
    $panelPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(106, 179, 255), 3)
    $gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(48, 122, 187), 1)

    $fieldRect = New-Object System.Drawing.Rectangle -ArgumentList 80, 120, ($Width - 160), ($Height - 180)
    $Graphics.FillRectangle($fieldBrush, 80, 120, ($Width - 160), ($Height - 180))

    $panelWidth = 230
    $panelHeight = 115
    $gapX = 24
    $gapY = 22
    $startX = 120
    $startY = 160
    $index = 0

    for ($row = 0; $row -lt 3; $row++) {
        for ($col = 0; $col -lt 4; $col++) {
            $x = $startX + $col * ($panelWidth + $gapX)
            $y = $startY + $row * ($panelHeight + $gapY)
            $rect = New-Object System.Drawing.Rectangle -ArgumentList $x, $y, $panelWidth, $panelHeight
            $Graphics.FillRectangle($panelBrush, $rect)
            $Graphics.DrawRectangle($panelPen, $rect)

            for ($grid = 1; $grid -lt 6; $grid++) {
                $lineX = $x + [int]($grid * $panelWidth / 6)
                $Graphics.DrawLine($gridPen, $lineX, $y, $lineX, $y + $panelHeight)
            }
            for ($grid = 1; $grid -lt 4; $grid++) {
                $lineY = $y + [int]($grid * $panelHeight / 4)
                $Graphics.DrawLine($gridPen, $x, $lineY, $x + $panelWidth, $lineY)
            }

            $index++
        }
    }

    $fieldBrush.Dispose()
    $panelBrush.Dispose()
    $panelPen.Dispose()
    $gridPen.Dispose()
}

function Draw-DustSample {
    param([string]$Path)
    $canvas = New-Canvas
    $bitmap = $canvas.Bitmap
    $graphics = $canvas.Graphics
    Draw-PanelField -Graphics $graphics -Width $bitmap.Width -Height $bitmap.Height

    $dustBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(145, 214, 181, 61))
    $dustBrushLight = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(110, 246, 214, 90))
    $font = New-Object System.Drawing.Font("Microsoft YaHei", 28, [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)

    $graphics.DrawString("Sample 1 - Heavy Dust Coverage", $font, $textBrush, 90, 42)
    $graphics.FillEllipse($dustBrush, 150, 190, 260, 110)
    $graphics.FillEllipse($dustBrush, 420, 185, 320, 135)
    $graphics.FillEllipse($dustBrushLight, 710, 188, 320, 120)
    $graphics.FillEllipse($dustBrush, 285, 338, 360, 132)
    $graphics.FillEllipse($dustBrushLight, 824, 350, 220, 95)
    $graphics.FillEllipse($dustBrush, 510, 486, 390, 118)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $textBrush.Dispose(); $font.Dispose(); $dustBrush.Dispose(); $dustBrushLight.Dispose()
    $graphics.Dispose(); $bitmap.Dispose()
}

function Draw-CrackSample {
    param([string]$Path)
    $canvas = New-Canvas
    $bitmap = $canvas.Bitmap
    $graphics = $canvas.Graphics
    Draw-PanelField -Graphics $graphics -Width $bitmap.Width -Height $bitmap.Height

    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(240, 242, 83, 83), 5)
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $font = New-Object System.Drawing.Font("Microsoft YaHei", 28, [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)

    $graphics.DrawString("Sample 2 - Critical Crack Risk", $font, $textBrush, 90, 42)
    $graphics.DrawLine($pen, 250, 210, 310, 280)
    $graphics.DrawLine($pen, 310, 280, 385, 345)
    $graphics.DrawLine($pen, 385, 345, 420, 412)
    $graphics.DrawLine($pen, 700, 202, 760, 250)
    $graphics.DrawLine($pen, 760, 250, 845, 315)
    $graphics.DrawLine($pen, 845, 315, 912, 382)
    $graphics.DrawLine($pen, 530, 485, 620, 545)
    $graphics.DrawLine($pen, 620, 545, 700, 582)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $textBrush.Dispose(); $font.Dispose(); $pen.Dispose()
    $graphics.Dispose(); $bitmap.Dispose()
}

function Draw-StainSample {
    param([string]$Path)
    $canvas = New-Canvas
    $bitmap = $canvas.Bitmap
    $graphics = $canvas.Graphics
    Draw-PanelField -Graphics $graphics -Width $bitmap.Width -Height $bitmap.Height

    $stainBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(155, 64, 205, 117))
    $stainBrushDark = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(165, 40, 165, 86))
    $font = New-Object System.Drawing.Font("Microsoft YaHei", 28, [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)

    $graphics.DrawString("Sample 3 - Bio Stain Accumulation", $font, $textBrush, 90, 42)
    $graphics.FillPie($stainBrush, 215, 210, 95, 85, 0, 360)
    $graphics.FillPie($stainBrushDark, 248, 226, 70, 60, 0, 360)
    $graphics.FillPie($stainBrush, 610, 348, 128, 118, 0, 360)
    $graphics.FillPie($stainBrushDark, 654, 373, 66, 65, 0, 360)
    $graphics.FillPie($stainBrush, 934, 480, 112, 108, 0, 360)
    $graphics.FillPie($stainBrushDark, 974, 506, 60, 56, 0, 360)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $textBrush.Dispose(); $font.Dispose(); $stainBrush.Dispose(); $stainBrushDark.Dispose()
    $graphics.Dispose(); $bitmap.Dispose()
}

Draw-DustSample (Join-Path $outputDir "dust-heavy.png")
Draw-CrackSample (Join-Path $outputDir "crack-critical.png")
Draw-StainSample (Join-Path $outputDir "bio-stain.png")
