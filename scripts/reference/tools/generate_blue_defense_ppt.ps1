$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$templatePath = Join-Path $root "低碳科技20页蓝色系\模板.pptx"
$outputDir = Join-Path $root "paper"
$outputPath = Join-Path $outputDir "光伏板污染智能检测_答辩PPT_低碳科技蓝色系.pptx"

$sampleDust = Join-Path $root "backend\samples\dust-heavy.png"
$sampleCrack = Join-Path $root "backend\samples\crack-critical.png"
$sampleStain = Join-Path $root "backend\samples\bio-stain.png"
$frameworkImage = Join-Path $root "paper\assets\framework_overview.png"
$examplesImage = Join-Path $root "paper\assets\pv_examples.png"
$qualitativeImage = Join-Path $root "paper\assets\qualitative_results.png"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Copy-Item -LiteralPath $templatePath -Destination $outputPath -Force

function Set-ShapeText {
    param(
        [Parameter(Mandatory = $true)] $shape,
        [Parameter(Mandatory = $true)][string] $text,
        [double] $fontSize = 0
    )

    $shape.TextFrame.TextRange.Text = $text
    if ($fontSize -gt 0) {
        $shape.TextFrame.TextRange.Font.Size = $fontSize
    }
}

function Get-NavGroup {
    param([Parameter(Mandatory = $true)] $slide)

    foreach ($shape in $slide.Shapes) {
        if ($shape.Type -ne 6) {
            continue
        }

        foreach ($item in $shape.GroupItems) {
            try {
                if ($item.HasTextFrame -and $item.TextFrame.HasText) {
                    $text = $item.TextFrame.TextRange.Text
                    if ($text -like "*政策解读页面*") {
                        return $shape
                    }
                }
            }
            catch {
            }
        }
    }

    throw "Navigation group not found on slide $($slide.SlideIndex)"
}

function Set-NavText {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][string] $mainTitle
    )

    $group = Get-NavGroup -slide $slide
    $mapping = @{
        "政策解读页面" = $mainTitle
        "标题1" = "研究背景"
        "标题2" = "技术路线"
        "标题3" = "数据实验"
        "标题4" = "结果分析"
        "标题5" = "系统实现"
        "标题6" = "总结"
    }

    foreach ($item in $group.GroupItems) {
        try {
            if ($item.HasTextFrame -and $item.TextFrame.HasText) {
                $current = $item.TextFrame.TextRange.Text
                if ($mapping.ContainsKey($current)) {
                    Set-ShapeText -shape $item -text $mapping[$current] -fontSize 14
                }
            }
        }
        catch {
        }
    }
}

function Get-ShapeNear {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][double] $left,
        [Parameter(Mandatory = $true)][double] $top,
        [double] $maxDistance = 30
    )

    $best = $null
    $bestDistance = [double]::PositiveInfinity
    foreach ($shape in $slide.Shapes) {
        $distance = [math]::Abs($shape.Left - $left) + [math]::Abs($shape.Top - $top)
        if ($distance -lt $bestDistance) {
            $best = $shape
            $bestDistance = $distance
        }
    }

    if ($best -eq $null -or $bestDistance -gt $maxDistance) {
        throw "Shape not found near left=$left top=$top on slide $($slide.SlideIndex)"
    }

    return $best
}

function Add-OvalImage {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][double] $left,
        [Parameter(Mandatory = $true)][double] $top,
        [Parameter(Mandatory = $true)][double] $width,
        [Parameter(Mandatory = $true)][double] $height,
        [Parameter(Mandatory = $true)][string] $imagePath
    )

    $shape = $slide.Shapes.AddShape(9, $left, $top, $width, $height)
    $shape.Fill.UserPicture($imagePath)
    $shape.Line.Visible = 0
    return $shape
}

function Add-RectImage {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][double] $left,
        [Parameter(Mandatory = $true)][double] $top,
        [Parameter(Mandatory = $true)][double] $width,
        [Parameter(Mandatory = $true)][double] $height,
        [Parameter(Mandatory = $true)][string] $imagePath
    )

    return $slide.Shapes.AddPicture($imagePath, $false, $true, $left, $top, $width, $height)
}

function Set-GroupItemText {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][string] $groupName,
        [Parameter(Mandatory = $true)][string] $itemName,
        [Parameter(Mandatory = $true)][string] $text,
        [double] $fontSize = 0
    )

    $group = $slide.Shapes.Item($groupName)
    $item = $group.GroupItems.Item($itemName)
    Set-ShapeText -shape $item -text $text -fontSize $fontSize
}

function Set-TableCellText {
    param(
        [Parameter(Mandatory = $true)] $slide,
        [Parameter(Mandatory = $true)][string] $tableShapeName,
        [Parameter(Mandatory = $true)][int] $row,
        [Parameter(Mandatory = $true)][int] $col,
        [Parameter(Mandatory = $true)][string] $text,
        [double] $fontSize = 12
    )

    $cellShape = $slide.Shapes.Item($tableShapeName).Table.Cell($row, $col).Shape
    Set-ShapeText -shape $cellShape -text $text -fontSize $fontSize
}

$powerPoint = New-Object -ComObject PowerPoint.Application
$powerPoint.Visible = $true
$presentation = $powerPoint.Presentations.Open($outputPath, $false, $false, $false)

try {
    $keepSlides = @(1, 6, 9, 11, 18, 20)
    for ($index = $presentation.Slides.Count; $index -ge 1; $index--) {
        if ($keepSlides -notcontains $index) {
            $presentation.Slides.Item($index).Delete()
        }
    }

    $presentation.Slides.Item(5).MoveTo(3)

    $slide1 = $presentation.Slides.Item(1)
    $slide2 = $presentation.Slides.Item(2)
    $slide3 = $presentation.Slides.Item(3)
    $slide4 = $presentation.Slides.Item(4)
    $slide5 = $presentation.Slides.Item(5)
    $slide6 = $presentation.Slides.Item(6)

    if ($slide1.Shapes.Item("Picture 11")) {
        $slide1.Shapes.Item("Picture 11").Delete()
    }

    Set-ShapeText -shape $slide1.Shapes.Item("TextBox 49") -text "大学生创新创业训练项目答辩" -fontSize 18
    Set-ShapeText -shape $slide1.Shapes.Item("TextBox 82") -text "光" -fontSize 110
    Set-ShapeText -shape $slide1.Shapes.Item("TextBox 83") -text "伏" -fontSize 110
    Set-ShapeText -shape $slide1.Shapes.Item("TextBox 85") -text "智" -fontSize 110
    Set-ShapeText -shape $slide1.Shapes.Item("TextBox 151") -text "检" -fontSize 110
    Set-ShapeText -shape $slide1.Shapes.Item("Rectangle 80") -text "基于 YOLO 的光伏板污染智能检测与可视化分析系统" -fontSize 24
    Set-GroupItemText -slide $slide1 -groupName "Group 157" -itemName "TextBox 161" -text "算法：YOLOv8 分割 + YOLO11 分类" -fontSize 16
    Set-GroupItemText -slide $slide1 -groupName "Group 188" -itemName "TextBox 192" -text "系统：Flask 后端 + 蓝色系可视化前端" -fontSize 16
    Set-GroupItemText -slide $slide1 -groupName "Group 218" -itemName "TextBox 227" -text "口径：面板分割 + 污染等级分类" -fontSize 16

    $coverBadge = $slide1.Shapes.AddTextbox(1, 760, 22, 130, 28)
    Set-ShapeText -shape $coverBadge -text "2026 答辩版" -fontSize 16

    Set-NavText -slide $slide2 -mainTitle "项目背景与研究目标"
    Set-ShapeText -shape $slide2.Shapes.Item("文本框 5") -text "项目背景与研究目标" -fontSize 24
    Set-ShapeText -shape $slide2.Shapes.Item("TextBox 179") -text "人工巡检成本高`r效率低且依赖经验" -fontSize 18
    Set-ShapeText -shape $slide2.Shapes.Item("TextBox 180") -text "复杂背景、阴影与反光`r增加视觉分析难度" -fontSize 18
    Set-ShapeText -shape $slide2.Shapes.Item("TextBox 181") -text "目标：实现面板分割、`r污染分级与网页展示" -fontSize 18
    Set-ShapeText -shape $slide2.Shapes.Item("圆角矩形 35") -text "服务于巡检可视化系统" -fontSize 18
    Set-ShapeText -shape $slide2.Shapes.Item("圆角矩形 37") -text "三类典型污染样本" -fontSize 18

    Add-OvalImage -slide $slide2 -left 44 -top 158 -width 188 -height 188 -imagePath $sampleDust | Out-Null
    Add-OvalImage -slide $slide2 -left 276 -top 84 -width 188 -height 188 -imagePath $sampleCrack | Out-Null
    Add-OvalImage -slide $slide2 -left 510 -top 78 -width 188 -height 188 -imagePath $sampleStain | Out-Null
    Add-OvalImage -slide $slide2 -left 748 -top 142 -width 188 -height 188 -imagePath $qualitativeImage | Out-Null

    Set-NavText -slide $slide3 -mainTitle "技术路线与系统实现"
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦33") -text "后端算法" -fontSize 22
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦34") -text "YOLOv8 对输入图像进行光伏板区域分割" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦35") -text "分类识别" -fontSize 22
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦36") -text "YOLO11 输出高污染、中度污染、低污染三类结果" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦37") -text "系统联调" -fontSize 22
    Set-ShapeText -shape $slide3.Shapes.Item("方能演亦38") -text "Flask 提供分析接口，前端完成上传、回显与可视化展示" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 12") -text "分割数据" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 10") -text "898/98/99" -fontSize 20
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 14") -text "分类测试" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 13") -text "1921 张" -fontSize 20
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 16") -text "运行环境" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 15") -text "CPU" -fontSize 20
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 18") -text "系统状态" -fontSize 16
    Set-ShapeText -shape $slide3.Shapes.Item("Rectangle 17") -text "已跑通" -fontSize 20

    Set-NavText -slide $slide4 -mainTitle "数据集与实验设置"
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 13") -text "数据集与实验设置" -fontSize 26
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 316") -text "任务划分与实验对象" -fontSize 18
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 82") -text "任务1：面板分割" -fontSize 18
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 83") -text "任务2：污染等级三分类" -fontSize 18
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 84") -text "任务3：前后端联调" -fontSize 18
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 89") -text "数据来源：两套已标注 YOLO training data" -fontSize 10
    Set-ShapeText -shape $slide4.Shapes.Item("TextBox 317") -text "分割 898/98/99；分类测试集 1921 张；当前为 CPU 轻量基线" -fontSize 10
    Add-RectImage -slide $slide4 -left 506 -top 146 -width 410 -height 300 -imagePath $frameworkImage | Out-Null
    Add-RectImage -slide $slide4 -left 38 -top 282 -width 455 -height 228 -imagePath $examplesImage | Out-Null

    Set-NavText -slide $slide5 -mainTitle "核心实验结果"
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 93 -top 75) -text "核心实验结果" -fontSize 24
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 223 -top 107) -text "两条真实基线均已完成测试，结果来自实际训练输出" -fontSize 16
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 96 -top 153) -text "面板分割" -fontSize 20
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 116 -top 221) -text "58.08%" -fontSize 28
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 51 -top 407) -text "Mask mAP@0.5" -fontSize 18
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 423 -top 193) -text "Macro-F1 92.63%" -fontSize 18
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 458 -top 301) -text "92.66%" -fontSize 32
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 764 -top 162) -text "系统状态" -fontSize 20
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 756 -top 213) -text "前后端已打通" -fontSize 22
    Set-ShapeText -shape (Get-ShapeNear -slide $slide5 -left 781 -top 407) -text "支持上传与可视化" -fontSize 16

    Set-NavText -slide $slide6 -mainTitle "总结与展望"
    try {
        $slide6.Shapes.Item("公众号：康帅PPT9").Delete()
    }
    catch {
    }
    Set-ShapeText -shape $slide6.Shapes.Item("TextBox 22") -text "谢谢各位老师" -fontSize 24
    Set-ShapeText -shape $slide6.Shapes.Item("TextBox 190") -text "已完成" -fontSize 18
    Set-ShapeText -shape $slide6.Shapes.Item("TextBox 191") -text "当前局限" -fontSize 18
    Set-ShapeText -shape $slide6.Shapes.Item("TextBox 192") -text "下一步" -fontSize 18

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 1 -text "模块" -fontSize 11
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 2 -text "任务定义" -fontSize 11
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 3 -text "模型/系统" -fontSize 11
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 4 -text "数据规模" -fontSize 11
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 5 -text "核心结果" -fontSize 11
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 1 -col 6 -text "现状" -fontSize 11

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 1 -text "面板分割" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 2 -text "单类 mask 分割" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 3 -text "YOLOv8n-seg" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 4 -text "898/98/99" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 5 -text "mAP@0.5 58.08%" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 2 -col 6 -text "已跑通" -fontSize 10

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 1 -text "污染分级" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 2 -text "高/中/低三分类" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 3 -text "YOLO11n-cls" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 4 -text "test 1921" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 5 -text "Acc 92.66% / F1 92.63%" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 3 -col 6 -text "已跑通" -fontSize 10

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 1 -text "后端服务" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 2 -text "图像上传与分析接口" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 3 -text "Flask" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 4 -text "API + 结果图" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 5 -text "可返回分析结果" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 4 -col 6 -text "已完成" -fontSize 10

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 1 -text "前端展示" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 2 -text "上传、预览、可视化" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 3 -text "大屏模板改造" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 4 -text "011 蓝色大屏" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 5 -text "已适配后端接口" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 5 -col 6 -text "已完成" -fontSize 10

    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 1 -text "后续工作" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 2 -text "补充缺陷框或 mask 标注" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 3 -text "扩展到精定位检测" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 4 -text "新增检测数据" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 5 -text "支撑论文升级" -fontSize 10
    Set-TableCellText -slide $slide6 -tableShapeName "Table 226" -row 6 -col 6 -text "进行中" -fontSize 10

    $presentation.Save()
}
finally {
    $presentation.Close()
    $powerPoint.Quit()
}

Write-Output "Generated: $outputPath"
