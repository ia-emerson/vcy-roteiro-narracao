# Instalador do projeto Roteiro + Narracao (Windows)
# Uso: clique com o botao direito > "Executar com o PowerShell"
#   ou no terminal:  powershell -ExecutionPolicy Bypass -File .\instalar.ps1
# Opcoes: -Cpu  (forca instalacao sem placa de video NVIDIA)
#         -SemModelo (nao baixa o modelo agora; baixa no primeiro uso)
param([switch]$Cpu, [switch]$SemModelo)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Passo($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "    OK: $msg" -ForegroundColor Green }
function Aviso($msg) { Write-Host "    AVISO: $msg" -ForegroundColor Yellow }

$TorchVersao = "2.8.0"

# 1. uv (gerenciador de Python)
Passo "Verificando o uv (gerenciador de Python)"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Aviso "uv nao encontrado. Instalando pelo winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Nao consegui instalar o uv automaticamente." -ForegroundColor Red
        Write-Host "Instale manualmente: https://docs.astral.sh/uv/getting-started/installation/"
        Write-Host "Depois feche e abra o terminal e rode este instalador de novo."
        exit 1
    }
}
Ok (uv --version)

# 2. Hardware
Passo "Detectando o hardware"
$usarCuda = $false
if (-not $Cpu -and (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
    $gpu = (nvidia-smi --query-gpu=name,memory.total --format=csv,noheader) 2>$null
    if ($LASTEXITCODE -eq 0 -and $gpu) { $usarCuda = $true; Ok "Placa NVIDIA: $gpu" }
}
if (-not $usarCuda) { Aviso "Sem placa NVIDIA (ou -Cpu). A narracao vai funcionar, mas bem mais devagar." }

# 3. Ambiente Python isolado (.venv) com Python 3.11
Passo "Criando o ambiente Python (.venv, Python 3.11)"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    uv venv .venv --python 3.11
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar o ambiente." }
}
Ok "Ambiente pronto"
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# 4. PyTorch adequado ao hardware
Passo "Instalando PyTorch $TorchVersao (pode demorar alguns minutos)"
if ($usarCuda) { $indice = "https://download.pytorch.org/whl/cu128" } else { $indice = "https://download.pytorch.org/whl/cpu" }
uv pip install --python $py "torch==$TorchVersao" "torchaudio==$TorchVersao" --index-url $indice
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar o PyTorch." }
Ok "PyTorch instalado"

# 5. OmniVoice e demais dependencias
Passo "Instalando OmniVoice e dependencias do narrador"
uv pip install --python $py -e .
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependencias." }
Ok "Dependencias instaladas"

# 6. Pastas
# ("narracoes" com cedilha/til montado por codigo para o script continuar ASCII)
$pastaNarr = "narra$([char]0x00E7)$([char]0x00F5)es"
foreach ($p in @("roteiros", "voices", $pastaNarr)) { New-Item -ItemType Directory -Force $p | Out-Null }

# 7. Modelo + diagnostico
$env:PYTHONUTF8 = "1"
if (-not $SemModelo) {
    Passo "Baixando o modelo OmniVoice (~2-3 GB, so na primeira vez)"
    & $py -m narrador baixar-modelo
    if ($LASTEXITCODE -ne 0) { throw "Falha ao baixar o modelo." }
}
Passo "Diagnostico final"
& $py -m narrador diagnostico
if ($LASTEXITCODE -ne 0) { throw "O diagnostico encontrou problemas (veja acima)." }

Write-Host "`nInstalacao concluida!" -ForegroundColor Green
Write-Host "Coloque uma voz de referencia em 'voices' (veja voices\LEIA-ME.txt),"
Write-Host "abra esta pasta no Claude Code e peca: 'crie um roteiro sobre ...'"
