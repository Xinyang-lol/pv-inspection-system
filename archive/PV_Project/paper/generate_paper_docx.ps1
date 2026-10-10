$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$template = "E:\ICSIP2026_PV_Contamination_Paper\Template.docx"
$outputExternal = "E:\ICSIP2026_PV_Contamination_Paper\PV_Contamination_ICSIP_Draft.docx"
$outputLocal = Join-Path $PSScriptRoot "PV_Contamination_ICSIP_Draft.docx"
$assetDir = Join-Path $PSScriptRoot "assets"

$word = $null
$doc = $null

function Add-Para {
    param(
        [object]$Selection,
        [string]$Text,
        [int]$Size = 11,
        [bool]$Bold = $false,
        [int]$Align = 0
    )
    $Selection.ParagraphFormat.Alignment = $Align
    $Selection.Font.Size = $Size
    $Selection.Font.Bold = [int]$Bold
    $Selection.TypeText($Text)
    $Selection.TypeParagraph()
}

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Add($template)
    $doc.Range().Text = ""
    $sel = $word.Selection

    Add-Para -Selection $sel -Text "A Robust Lightweight Framework for UAV-Based Photovoltaic Panel Contamination Detection Under Complex Illumination" -Size 16 -Bold $true -Align 1
    Add-Para -Selection $sel -Text "Author information to be completed before submission" -Size 11 -Align 1
    Add-Para -Selection $sel -Text "Replace this block with the final author list, affiliations, and emails." -Size 10 -Align 1

    Add-Para -Selection $sel -Text "Abstract" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "Visible-light inspection of photovoltaic plants from unmanned aerial vehicles offers a low-cost alternative to manual patrol, but contamination detection remains difficult under strong reflection, cast shadow, viewpoint variation, and mixed background clutter. This paper presents a lightweight panel-aware framework for PV contamination detection that combines illumination-robust preprocessing, CBAM-enhanced YOLOv8 panel segmentation, and a YOLO11 detector for dust, crack, and biological stain localization at the panel level. The framework is designed for a self-built dataset of approximately 3000 UAV and field images, and its deployment target is an RTX 4060-class inspection workstation. A preliminary dust-only model already achieved an F1-score of 0.97, supporting the feasibility of the proposed unified framework."

    Add-Para -Selection $sel -Text "Keywords" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "photovoltaic inspection; contamination detection; UAV vision; object detection; image processing; complex illumination"

    Add-Para -Selection $sel -Text "1 Introduction" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "Photovoltaic plants operate in open outdoor environments and therefore suffer from surface contamination and structural degradation caused by dust deposition, cracks, and biological residues. UAV-based RGB inspection is attractive because it provides wide-area coverage with relatively low equipment cost, but strong reflection, cast shadow, viewpoint variation, and background clutter make robust detection difficult."
    Add-Para -Selection $sel -Text "This paper focuses on a single technical line: panel-aware contamination detection and localization under complex illumination. The method first segments PV panels and then detects contamination only inside panel-aware regions of interest."

    Add-Para -Selection $sel -Text "2 Related Work" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "Recent PV inspection work spans infrared diagnosis, electroluminescence analysis, and RGB-image-based contamination analysis. Aerial PV panel detection is also relevant because panel extraction quality directly affects downstream contamination detection. Attention mechanisms such as CBAM and class-imbalance-aware losses such as Focal Loss are useful in this setting because the scene is visually complex and the defect categories are imbalanced."

    Add-Para -Selection $sel -Text "3 Method" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "The proposed framework first applies illumination normalization to suppress overexposure and improve local contrast in shadow regions. A YOLOv8m-seg model with CBAM-enhanced features then extracts panel masks. Each segmented panel is cropped and normalized before contamination detection. A YOLO11 detector predicts three classes: dust, crack, and biological stain. The final analysis module aggregates panel-level coverage and severity cues into a maintenance-oriented risk score."

    $framework = Join-Path $assetDir "framework_overview.png"
    if (Test-Path $framework) {
        $shape = $sel.InlineShapes.AddPicture($framework)
        $shape.Width = 430
        Add-Para -Selection $sel -Text "Fig. 1. Overview of the proposed panel-aware contamination detection framework." -Size 10 -Align 1
    }

    Add-Para -Selection $sel -Text "4 Experiments" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "The project is based on a self-built RGB PV inspection dataset containing approximately 3000 images acquired from UAV views and close-range field observations. The current draft assumes a 70/15/15 train/validation/test split; this setting should be updated if the final protocol differs. All experiments target an NVIDIA RTX 4060 GPU."
    Add-Para -Selection $sel -Text "Table 1 summarizes the main comparison placeholders that must be filled with real training logs."

    $tableRange = $doc.Range($sel.Start, $sel.Start)
    $table = $doc.Tables.Add($tableRange, 5, 7)
    $table.Borders.Enable = 1
    $headers = @("Method", "Precision (%)", "Recall (%)", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)", "Params (M)", "FPS")
    for ($i = 1; $i -le 7; $i++) {
        $table.Cell(1, $i).Range.Text = $headers[$i - 1]
    }
    $rows = @(
        @("YOLOv8n direct detection", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X"),
        @("YOLOv8m direct detection", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X"),
        @("YOLO11n panel-aware detection", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X"),
        @("Proposed method", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X", "XX.X")
    )
    for ($r = 0; $r -lt $rows.Count; $r++) {
        for ($c = 0; $c -lt 7; $c++) {
            $table.Cell($r + 2, $c + 1).Range.Text = $rows[$r][$c]
        }
    }
    $sel.SetRange($table.Range.End, $table.Range.End)
    $sel.TypeParagraph()
    Add-Para -Selection $sel -Text "Table 1. Main comparison on the PV contamination test set." -Size 10 -Align 1

    $examples = Join-Path $assetDir "pv_examples.png"
    if (Test-Path $examples) {
        $shape = $sel.InlineShapes.AddPicture($examples)
        $shape.Width = 430
        Add-Para -Selection $sel -Text "Fig. 2. Representative contamination patterns in the project dataset." -Size 10 -Align 1
    }

    $qualitative = Join-Path $assetDir "qualitative_results.png"
    if (Test-Path $qualitative) {
        $shape = $sel.InlineShapes.AddPicture($qualitative)
        $shape.Width = 430
        Add-Para -Selection $sel -Text "Fig. 3. Qualitative panel-aware detection visualization." -Size 10 -Align 1
    }

    Add-Para -Selection $sel -Text "5 Conclusion" -Size 12 -Bold $true
    Add-Para -Selection $sel -Text "This paper presents a panel-aware visual inspection framework for UAV-based PV contamination detection under complex illumination. The draft already matches the correct ICSIP writing logic; the remaining work before submission is to replace all placeholder quantitative values with the final training and evaluation logs."

    Add-Para -Selection $sel -Text "References" -Size 12 -Bold $true
    $refs = @(
        "[1] M. Islam et al., ""Artificial Intelligence in Photovoltaic Fault Identification and Diagnosis: A Systematic Review,"" Energies, 2023.",
        "[2] E. Arnaudo et al., ""A Comparative Evaluation of Deep Learning Techniques for Photovoltaic Panel Detection From Aerial Images,"" IEEE Access, 2023.",
        "[3] R. Cavieres et al., ""Automatic soiling and partial shading assessment on PV modules through RGB images analysis,"" Applied Energy, 2022.",
        "[4] B. I. Evstatiev et al., ""PV Module Soiling Detection Using Visible Spectrum Imaging and Machine Learning,"" Energies, 2024.",
        "[5] S. Mehta et al., ""DeepSolarEye: Power Loss Prediction and Weakly Supervised Soiling Localization via Fully Convolutional Networks for Solar Panels,"" WACV, 2018.",
        "[6] A. Rahman, ""Solar Panel Surface Defect and Dust Detection: Deep Learning Approach,"" Journal of Imaging, 2025.",
        "[7] S. Woo et al., ""CBAM: Convolutional Block Attention Module,"" ECCV, 2018.",
        "[8] T.-Y. Lin et al., ""Focal Loss for Dense Object Detection,"" ICCV, 2017.",
        "[9] S. Jumaboev et al., ""Photovoltaics Plant Fault Detection Using Deep Learning Techniques,"" Remote Sensing, 2022.",
        "[10] J. Redmon et al., ""You Only Look Once: Unified, Real-Time Object Detection,"" CVPR, 2016."
    )
    foreach ($ref in $refs) {
        Add-Para -Selection $sel -Text $ref -Size 10
    }

    $doc.SaveAs2([string]$outputExternal)
    $doc.SaveAs2([string]$outputLocal)
}
finally {
    if ($doc -ne $null) {
        $doc.Close()
    }
    if ($word -ne $null) {
        $word.Quit()
    }
}
