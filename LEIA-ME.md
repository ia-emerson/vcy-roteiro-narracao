# Roteiro + Narração (Claude Code + OmniVoice)

Duas skills para o Claude Code:

1. **roteiro_vcy**: escreve roteiros de YouTube seguindo as regras do `comando.txt`, com a duração que você pedir.
2. **narracao_vcy**: narra o roteiro **no seu computador** com o OmniVoice, clonando uma voz da pasta `voices/`.

## Instalação (uma vez)

Requisitos: Windows 10/11, macOS ou Linux, ~8 GB livres em disco e internet na instalação.
Uma placa NVIDIA deixa a narração muito mais rápida, mas não é obrigatória.

**Baixe o projeto** com git:

```
git clone https://github.com/ia-emerson/vcy-roteiro-narracao.git
cd vcy-roteiro-narracao
```

Sem git: na página do repositório, clique em **Code → Download ZIP** e extraia a pasta.
Para atualizar depois, rode `git pull` dentro da pasta.

**Windows:** clique com o botão direito em `instalar.ps1` e escolha **Executar com o PowerShell**,
ou no terminal:

```
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

**macOS / Linux:**

```
bash instalar.sh
```

O instalador:
- instala o `uv`, se faltar (no Mac/Linux ele mostra o comando para instalar);
- cria um Python 3.11 isolado na pasta `.venv`, sem mexer no Python do seu computador;
- instala o PyTorch certo para o seu hardware (NVIDIA/CUDA, Mac ou CPU);
- instala o OmniVoice e baixa o modelo (~2-3 GB);
- roda um diagnóstico no fim.

Use `-Cpu` (ou `--cpu`) para forçar a instalação sem GPU.

## Uso

1. Coloque uma voz em `voices/`. As instruções estão em [voices/LEIA-ME.txt](voices/LEIA-ME.txt).
2. Abra esta pasta no Claude Code.
3. Peça, por exemplo: **"crie um roteiro de 8 minutos sobre a história do Raul Seixas"**.
4. O Claude pesquisa o tema e mostra os tópicos. Depois de você aprovar, ele escreve o roteiro e salva em `roteiros/`.
5. Depois de você aprovar o roteiro, ele pergunta se quer a narração. Ela fica em `narrações/`, em WAV e MP3.

Também dá para pedir direto: **"narre o roteiro roteiros/xxx.txt"**.

## Personalizar

- **Estilo dos roteiros:** edite o `comando.txt`.
- **Qualidade, velocidade, pausas e volume da narração:** edite o `config.toml`.

## Estrutura

```
comando.txt            regras dos roteiros
config.toml            ajustes da narração
.claude/skills/        as duas skills
narrador/              código da narração (Python)
roteiros/  narrações/  voices/
```

## Licença do OmniVoice

Cada usuário é responsável por avaliar se o seu uso está de acordo com a licença.
O modelo também proíbe clonar a voz de alguém sem autorização.
