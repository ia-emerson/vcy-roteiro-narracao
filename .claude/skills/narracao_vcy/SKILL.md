---
name: narracao_vcy
description: Gera a narração em áudio de um roteiro (.txt da pasta roteiros/) localmente com OmniVoice, clonando uma voz de referência da pasta voices/ no idioma detectado do roteiro, e entrega WAV + MP3 em narrações/. Use quando o usuário pedir para narrar, gerar a narração, locução, voz ou áudio de um roteiro ("narre o roteiro", "gera a narração", "quero o áudio"), ou após aprovar um roteiro da skill roteiro_vcy.
---

# Narração com OmniVoice (local)

Tudo roda no computador do usuário. Os comandos abaixo usam o Python do projeto:
- Windows: `.venv\Scripts\python -m narrador ...`
- macOS/Linux: `.venv/bin/python -m narrador ...`

Todos imprimem JSON no stdout (progresso vai para o stderr). Rode a partir da raiz do projeto.

## 0. Ambiente

Se `.venv` não existir ou `diagnostico` falhar (`"ok": false`), não tente consertar à mão:
peça ao usuário para rodar o instalador (`instalar.ps1` no Windows, `bash instalar.sh` no Mac/Linux)
e mostre o erro. `"cuda": false` sem GPU NVIDIA é normal (só fica mais lento); avise.

## 1. Roteiro

Use o arquivo indicado. Se nenhum foi indicado, pegue o `.txt` mais recente de `roteiros/`
(ignore `*.fontes.md`) e confirme com o usuário qual é.

## 2. Idioma

```
python -m narrador idioma "roteiros/<arquivo>.txt"
```
Informe o idioma detectado. Se `confianca` < 0.5, confirme com o usuário.

## 3. Voz

```
python -m narrador vozes --idioma <codigo>
```

- **Nenhuma voz utilizável** para o idioma: pare e oriente o usuário (abaixo). Se houver vozes com
  `problemas`, mostre os problemas de cada uma para ele corrigir.
- **Uma voz**: informe qual será usada e siga.
- **Mais de uma**: pergunte com AskUserQuestion qual usar (rótulo = nome; descrição = variante,
  duração e as primeiras palavras do texto). Mostre os `avisos` se houver.

Orientação quando falta voz (adapte ao idioma `<cod>`):

> Não há voz em **<idioma>** na pasta `voices/`. Você precisa de um áudio de ~10 s e um .txt com
> exatamente o que é falado. Duas opções:
>
> **A) Gravar sua voz:** grave 8 a 12 s lendo um trecho no tom da narração (lugar silencioso,
> sem música, microfone perto, sem cortar o fim). Salve como `voices/<cod>_<seunome>.wav` e crie
> `voices/<cod>_<seunome>.txt` com o texto lido, palavra por palavra.
>
> **B) Google AI Studio:** em aistudio.google.com abra *Generate speech*, escolha uma voz, cole um
> texto de ~25 palavras no idioma, gere e baixe o áudio. Salve como `voices/<cod>_<nome>.wav` e o
> texto idêntico em `voices/<cod>_<nome>.txt`.
>
> Use somente vozes que você tem direito de usar (a sua, de quem autorizou, ou geradas por você).
> Avise quando colocar os arquivos.

Quando o usuário avisar, rode `vozes` de novo.

## 4. Gerar

Rode **em segundo plano** (pode levar vários minutos) e espere a notificação; não fique consultando:

```
python -m narrador narrar "roteiros/<arquivo>.txt" --voz <id_da_voz>
```

Opções: `--saida <nome>` (nome do arquivo final), `--verificar` (confere cada parte com Whisper;
mais lento, baixa ~1,6 GB na 1ª vez; ofereça quando o usuário quiser máxima garantia),
`--refazer 3,7` (regenera só essas partes). A geração é retomável: se for interrompida, rodar o
mesmo comando continua de onde parou e reaproveita as partes prontas.

Como funciona (para explicar se perguntarem): o texto é limpo, números viram palavras, e ele é
dividido em partes de até ~15 s sem cortar frases; a voz de referência é processada uma vez e
usada em todas as partes; cada parte é conferida (duração, silêncio, distorção) e regenerada se
estiver suspeita; no fim as partes são unidas com pausas naturais e o volume é ajustado para
-14 LUFS com um ganho único (sem compressão).

## 5. Entrega

Do JSON final, informe com links markdown relativos:
- `narrações/<nome>.wav` (qualidade máxima, para edição) e `narrações/<nome>.mp3`,
- duração, tempo de geração, voz e idioma,
- partes regeneradas e, principalmente, as `suspeitas` (número da parte + texto) — sugira ouvir
  esses trechos e, se preciso, rodar com `--refazer <números>`.

Se o usuário pedir para mudar uma frase depois: edite o roteiro e rode `narrar` de novo; só as
partes alteradas são regeneradas. As partes ficam em `narrações/.trabalho/<nome>/` (podem ser
apagadas quando o vídeo estiver pronto).

Os ajustes de qualidade (passos, velocidade, pausas, volume) ficam em `config.toml`.
