# Windows Poppler 安装脚本
# 用于 PDF 转图像支持（pdf2image 依赖）

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Poppler 自动安装脚本（Windows）" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 检测是否已安装
$existingPoppler = Get-Command "pdftoppm.exe" -ErrorAction SilentlyContinue
if ($existingPoppler) {
    Write-Host "已安装 Poppler：$($existingPoppler.Source)" -ForegroundColor Green
    Write-Host ""
    Write-Host "如需重新安装，请先从 PATH 中移除现有版本" -ForegroundColor Yellow
    exit 0
}

Write-Host "Poppler 是 PDF 处理工具集，用于将 PDF 转换为图片" -ForegroundColor Gray
Write-Host "本脚本将下载并配置 Poppler for Windows" -ForegroundColor Gray
Write-Host ""

# 创建下载目录
$downloadDir = "$env:TEMP\poppler_install"
$installDir = "$env:ProgramFiles\poppler"

if (-not (Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

Write-Host "步骤 1/4: 下载 Poppler..." -ForegroundColor Cyan

# Poppler Windows 二进制下载地址
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"
$zipPath = "$downloadDir\poppler.zip"

try {
    Write-Host "  下载中...（约 30 MB）" -ForegroundColor Gray
    Invoke-WebRequest -Uri $popplerUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "  下载完成" -ForegroundColor Green
} catch {
    Write-Host "  下载失败：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "手动安装步骤：" -ForegroundColor Yellow
    Write-Host "  1. 访问：https://github.com/oschwartz10612/poppler-windows/releases"
    Write-Host "  2. 下载最新的 Release-xx.zip"
    Write-Host "  3. 解压到 C:\Program Files\poppler"
    Write-Host "  4. 将 C:\Program Files\poppler\Library\bin 添加到系统 PATH"
    exit 1
}

Write-Host ""
Write-Host "步骤 2/4: 解压文件..." -ForegroundColor Cyan

try {
    if (Test-Path $installDir) {
        Remove-Item $installDir -Recurse -Force
    }
    Expand-Archive -Path $zipPath -DestinationPath $downloadDir -Force
    
    # 查找解压后的目录
    $extractedDir = Get-ChildItem -Path $downloadDir -Directory | Where-Object { $_.Name -like "poppler*" } | Select-Object -First 1
    
    if (-not $extractedDir) {
        throw "无法找到解压后的 poppler 目录"
    }
    
    Move-Item -Path $extractedDir.FullName -Destination $installDir -Force
    Write-Host "  解压到：$installDir" -ForegroundColor Green
} catch {
    Write-Host "  解压失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "步骤 3/4: 配置环境变量..." -ForegroundColor Cyan

$binPath = "$installDir\Library\bin"
if (-not (Test-Path $binPath)) {
    $altBinPath = "$installDir\bin"
    if (Test-Path $altBinPath) {
        $binPath = $altBinPath
    } else {
        Write-Host "  无法找到 poppler bin 目录" -ForegroundColor Red
        Write-Host "  已安装目录：$installDir" -ForegroundColor Yellow
        Write-Host "  请手动将 bin 目录添加到 PATH" -ForegroundColor Yellow
        exit 1
    }
}

# 添加到系统 PATH（需要管理员权限）
try {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$binPath*") {
        $newPath = $currentPath + ";" + $binPath
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Host "  已添加到系统 PATH：$binPath" -ForegroundColor Green
        Write-Host "  （需要重启终端才能生效）" -ForegroundColor Yellow
    } else {
        Write-Host "  PATH 已包含 poppler" -ForegroundColor Green
    }
} catch {
    Write-Host "  添加到 PATH 失败（可能需要管理员权限）" -ForegroundColor Red
    Write-Host ""
    Write-Host "手动添加到 PATH：" -ForegroundColor Yellow
    Write-Host "  1. Win + R -> sysdm.cpl -> 高级 -> 环境变量"
    Write-Host "  2. 在系统变量中找到 Path，点击编辑"
    Write-Host "  3. 新建并添加：$binPath"
    Write-Host "  4. 确定并重启终端"
}

Write-Host ""
Write-Host "步骤 4/4: 验证安装..." -ForegroundColor Cyan

# 刷新当前会话的 PATH
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = $machinePath + ";" + $userPath

$pdftoppm = Get-Command "pdftoppm.exe" -ErrorAction SilentlyContinue
if ($pdftoppm) {
    Write-Host "  Poppler 安装成功！" -ForegroundColor Green
    Write-Host "  版本：" -NoNewline
    & pdftoppm -v 2>&1 | Select-Object -First 1
} else {
    Write-Host "  命令未找到（可能需要重启终端）" -ForegroundColor Yellow
    Write-Host "  安装路径：$binPath" -ForegroundColor Gray
}

# 清理临时文件
Remove-Item $downloadDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 重启终端（或 VS Code）" -ForegroundColor White
Write-Host "  2. 运行：streamlit run app.py" -ForegroundColor White
Write-Host "  3. 上传 PDF 发票测试" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
