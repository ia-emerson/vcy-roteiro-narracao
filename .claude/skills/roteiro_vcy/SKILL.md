---
name: roteiro_vcy
description: Cria roteiros de vídeo para YouTube seguindo as regras do comando.txt na raiz do projeto, com duração alvo em minutos, e salva em roteiros/. Use quando o usuário pedir um roteiro, script ou texto de vídeo sobre um tema, título, artista ou história ("crie um roteiro sobre...", "roteiro de 10 minutos sobre...", "write a script about...").
---

# Criação de roteiro

Você escreve roteiros de vídeo seguindo **rigorosamente** o `comando.txt` da raiz do projeto.
O `comando.txt` é do usuário e pode mudar: leia-o inteiro **toda vez** que esta skill for usada,
e siga-o mesmo que contradiga algum hábito seu. Se algo desta skill conflitar com o `comando.txt`,
o `comando.txt` vence (exceto: salvar o arquivo em `roteiros/` e o fluxo de aprovação abaixo).

## 1. Coletar o pedido

Precisa de: **tema/título**, **duração em minutos** e **idioma do roteiro**.

- Pergunte **antes de começar** o que faltar (não presuma). Junte as perguntas numa única
  chamada de AskUserQuestion:
  - **Duração** (se não informada): opções como 5, 8, 10 e 15 minutos (o usuário pode digitar outra).
  - **Idioma** (se não informado explicitamente, por exemplo "em inglês", "in Spanish"): **sempre pergunte**,
    mesmo que o pedido esteja em português, porque muitos canais publicam em outro idioma. Opções:
    Português, Inglês, Espanhol (o usuário pode digitar outro). Para indicar em quais idiomas a
    narração já está pronta, rode `.venv\Scripts\python -m narrador vozes` (se o ambiente existir) e
    acrescente "(voz disponível)" na descrição das opções que tiverem voz utilizável em `voices/`.
- Na mesma pergunta, se fizer sentido, ofereça anexar a **transcrição de um vídeo concorrente** (opcional;
  o `comando.txt` prevê isso). Se o usuário já colou uma transcrição, use-a como referência de assunto e
  ritmo, **sem copiar frases**. A transcrição pode estar em outro idioma; o roteiro sai no idioma escolhido.
- O `comando.txt` está em português, mas vale para qualquer idioma: aplique as mesmas regras e adapte
  os exemplos de frases, a censura de termos sensíveis e o enquadramento de especulação ao idioma
  escolhido (ex.: em inglês, "rumors suggest", "reports claim"), de forma natural para um nativo.
- Pesquise também em fontes do idioma/país do público quando isso trouxer informações melhores.

## 2. Pesquisa e tópicos (aprovação 1)

1. Pesquise o tema na web (WebSearch): fatos principais, e também rumores recentes, polêmicas e
   especulações, como o `comando.txt` pede. Anote as fontes (URLs).
2. Monte a estrutura: introdução + 6 a 8 seções + conclusão. Para cada seção, 1-2 linhas do que ela traz
   de novo e o gancho de transição para a próxima.
3. Apresente os tópicos ao usuário com a meta de palavras (passo 3) e **espere a aprovação** antes de
   escrever o roteiro completo. Ajuste quantas vezes ele pedir. Converse com o usuário no idioma dele;
   se o roteiro for em outro idioma, mostre os títulos dos tópicos no idioma do roteiro com uma
   tradução curta ao lado.

## 3. Tamanho certo para a duração

Meta de palavras = duração (min) × velocidade de fala:

| Idioma | palavras/min |
|---|---|
| português | 150 |
| inglês | 155 |
| espanhol | 160 |
| outros | 150 |

Distribua as palavras entre as seções (introdução e conclusão mais curtas). Depois de escrever, confira com:

```
.venv\Scripts\python -m narrador estimar "roteiros\<arquivo>.txt"
```

(macOS/Linux: `.venv/bin/python -m narrador estimar roteiros/<arquivo>.txt`). Se o ambiente ainda não
existir, conte as palavras você mesmo. Aceite ±7% da meta; fora disso, ajuste o texto antes de entregar.

## 4. Escrever e salvar

Regras do arquivo (para a narração sair limpa):

- Somente o texto que será **falado**, em parágrafos separados por uma linha em branco.
- Sem títulos de seção, sem "Introdução:", sem marcações markdown, sem `[instruções de cena]`,
  sem emojis, sem listas.
- Escreva números, valores e datas **por extenso, como se falam**, com a concordância certa
  ("duas mil e quinhentas pessoas", "mil novecentos e setenta e sete", "dois vírgula cinco milhões
  de reais"). O narrador converte algarismos que sobrarem, mas a concordância dele é aproximada.
  Siglas: escreva como devem ser lidas ("FBI" → "efe-bê-í" só se a leitura for ambígua).
- Siga a censura/reformulação de termos sensíveis e o enquadramento de especulação do `comando.txt`.

Salve em `roteiros/AAAA-MM-DD_<tema-em-minusculas-com-hifens>.txt` (UTF-8). Se já existir, acrescente
`-v2`, `-v3`. Salve também `roteiros/<mesmo-nome>.fontes.md` com os tópicos aprovados e as URLs das
fontes (para o usuário checar os fatos; esse arquivo não é narrado).

## 5. Entrega (aprovação 2)

Informe:
- o caminho do arquivo (como link markdown relativo, ex.: `[roteiros/2026-11-04_tema.txt](roteiros/2026-11-04_tema.txt)`),
- idioma, palavras e duração estimada,
- e pergunte se **aprova** ou quer **ajustes**.

Ajustes: edite o mesmo arquivo e repita a entrega. **Somente depois da aprovação** pergunte se deseja
gerar a narração. Se sim, use a skill `narracao_vcy` passando o caminho do roteiro.
