# PDF 支持安装指南

## 问题现象

上传 PDF 发票时显示错误：
```
PDF 处理失败：Unable to get page count. Is poppler installed and in PATH?
```

---

## 原因

PDF 转图像功能依赖 `pdf2image` Python 库 + `poppler` 系统工具。  
`poppler` 未安装或未添加到系统 PATH。

---

## 解决方案

### Windows 用户（推荐使用自动脚本）

#### 方法 1：自动安装（推荐）

1. **以管理员身份运行 PowerShell**
2. **运行安装脚本**：
   ```powershell
   cd "f:\SynologyDrive\Claude code\Tax_Auto_System"
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install_poppler_windows.ps1
   ```
3. **重启终端**（让 PATH 生效）
4. **重新运行应用**：
   ```powershell
   streamlit run app.py
   ```

#### 方法 2：手动安装

1. **下载 Poppler for Windows**  
   访问：https://github.com/oschwartz10612/poppler-windows/releases  
   下载最新的 `Release-xx.zip`

2. **解压到固定位置**  
   例如：`C:\Program Files\poppler`

3. **添加到系统 PATH**  
   - Win + R → `sysdm.cpl` → 高级 → 环境变量
   - 在系统变量中找到 `Path`，点击编辑
   - 新建并添加：`C:\Program Files\poppler\Library\bin`
   - 确定并重启终端

4. **验证安装**  
   ```powershell
   pdftoppm -v
   ```
   应显示版本信息

---

### Linux 用户

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install poppler-utils
```

#### CentOS/RHEL
```bash
sudo yum install poppler-utils
```

#### Arch Linux
```bash
sudo pacman -S poppler
```

---

### macOS 用户

使用 Homebrew：
```bash
brew install poppler
```

---

## 验证安装

安装完成后，运行以下命令验证：

```bash
# 检查 poppler 是否在 PATH 中
pdftoppm -v

# 或者
pdfinfo -v
```

如果显示版本信息，说明安装成功。

---

## 替代方案：使用图片发票

如果暂时无法安装 poppler，可以：

1. **将 PDF 转换为图片**（使用在线工具或其他软件）
2. **上传 JPG/PNG 格式的发票**

系统完全支持图片格式发票，无需 poppler。

---

## 常见问题

### Q: 安装后仍然报错？
**A:** 需要重启终端（或 VS Code）让 PATH 生效。

### Q: Windows 脚本执行被阻止？
**A:** 以管理员身份运行 PowerShell，并执行：
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Q: 不想安装 poppler，能否继续用系统？
**A:** 可以！直接上传 JPG/PNG 格式的发票图片，功能完全相同。

---

## 技术细节

- **pdf2image**：Python 包装库（已在 requirements-paddle.txt 中）
- **poppler**：底层 PDF 渲染引擎（系统级工具）
- **使用的命令**：`pdftoppm`（PDF to PPM/PNG/JPEG 转换器）

---

## 需要帮助？

如遇到问题，请提供以下信息：

1. 操作系统和版本
2. 错误消息截图
3. `pdftoppm -v` 命令输出（如果有）

我们会尽快帮您解决！
