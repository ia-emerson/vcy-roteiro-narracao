"""Preparação do texto para narração: limpeza, números por extenso e divisão em partes."""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------- limpeza

_LINHA_DIRECAO = re.compile(r"^\s*[\[(][^\])]*[\])]\s*$")       # [corte para...] sozinho na linha
_DIRECAO_INLINE = re.compile(r"\[[^\]]*\]")                    # [instruções] no meio do texto
_TITULO_MD = re.compile(r"^\s*#{1,6}\s+")
_MARCAS_MD = re.compile(r"(\*\*|__|\*|`)")
_SEPARADOR = re.compile(r"^\s*([-*_=]\s*){3,}$")


def limpar(texto: str) -> list[str]:
    """Remove marcações e devolve a lista de parágrafos narráveis."""
    texto = texto.replace("\r\n", "\n").replace(" ", " ")
    paragrafos: list[str] = []
    atual: list[str] = []
    for linha in texto.split("\n"):
        if not linha.strip() or _SEPARADOR.match(linha) or _LINHA_DIRECAO.match(linha):
            if atual:
                paragrafos.append(" ".join(atual))
                atual = []
            continue
        if _TITULO_MD.match(linha):          # títulos de seção não são narrados
            if atual:
                paragrafos.append(" ".join(atual))
                atual = []
            continue
        linha = _DIRECAO_INLINE.sub("", linha)
        linha = _MARCAS_MD.sub("", linha)
        linha = re.sub(r"^\s*[-•]\s+", "", linha)
        atual.append(linha.strip())
    if atual:
        paragrafos.append(" ".join(atual))
    return [re.sub(r"\s{2,}", " ", p).strip() for p in paragrafos if p.strip()]


# ------------------------------------------------------- números por extenso

_LOCALE = {"pt": "pt_BR", "en": "en", "es": "es", "fr": "fr", "de": "de", "it": "it",
           "nl": "nl", "pl": "pl", "ru": "ru", "tr": "tr", "id": "id", "ja": "ja", "ko": "ko"}
# idiomas que usam vírgula como separador decimal e ponto como milhar
_VIRGULA_DECIMAL = {"pt", "es", "fr", "de", "it", "nl", "pl", "ru", "tr", "id"}

_PALAVRAS = {
    "pt": {"pct": "por cento", "reais": "reais", "real": "real", "dolares": "dólares",
           "dolar": "dólar", "euros": "euros", "euro": "euro", "virgula": "vírgula"},
    "es": {"pct": "por ciento", "dolares": "dólares", "dolar": "dólar", "euros": "euros",
           "euro": "euro", "reais": "reales", "real": "real", "virgula": "coma"},
    "en": {"pct": "percent", "dolares": "dollars", "dolar": "dollar", "euros": "euros",
           "euro": "euro", "reais": "reais", "real": "real", "virgula": "point"},
}


def _n2w(valor, idioma: str, **kw) -> str:
    from num2words import num2words

    loc = _LOCALE.get(idioma, idioma)
    # num2words às vezes põe vírgulas ("mil, novecentos"), que viram pausas na fala
    return num2words(valor, lang=loc, **kw).replace(",", "")


def _parse(token: str, idioma: str):
    if idioma in _VIRGULA_DECIMAL:
        milhar, decimal = ".", ","
    else:
        milhar, decimal = ",", "."
    # "1.000" em pt é mil; mas "3.5" em pt provavelmente é decimal digitado à inglesa
    partes = token.split(milhar)
    if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]) and decimal not in partes[-1]:
        token = token.replace(milhar, "")
    elif len(partes) > 1 and decimal not in token:
        token = token.replace(milhar, decimal)   # separador trocado
    else:
        token = token.replace(milhar, "")
    if decimal in token:
        inteiro, frac = token.split(decimal, 1)
        return int(inteiro or 0), frac
    return int(token), None


def _numero_falado(token: str, idioma: str) -> str:
    inteiro, frac = _parse(token, idioma)
    falado = _n2w(inteiro, idioma)
    if frac:
        if idioma in ("en",):
            falado += " point " + " ".join(_n2w(int(d), idioma) for d in frac)
        else:
            sep = _PALAVRAS.get(idioma, {}).get("virgula", ",")
            falado += f" {sep} " + (_n2w(int(frac), idioma) if not frac.startswith("0")
                                    else " ".join(_n2w(int(d), idioma) for d in frac))
    return falado


def _feminino_pt(ordinal: str) -> str:
    return " ".join(p[:-1] + "a" if p.endswith("o") else p for p in ordinal.split())


# substantivos masculinos terminados em -a/-as (exceções da regra de gênero)
_MASC_EM_A = {
    "dia", "problema", "sistema", "programa", "tema", "mapa", "planeta", "idioma", "poema",
    "drama", "clima", "telefonema", "cinema", "esquema", "dilema", "diploma", "fantasma",
    "pijama", "sofá", "guarda", "atleta", "artista", "jornalista", "policial", "cometa",
    "teorema", "trauma", "aroma", "enigma", "carisma", "dogma", "lema", "panorama", "prisma",
    "milhão", "bilhão", "trilhão", "milhões", "bilhões", "trilhões", "mil", "fã",
}
# palavras que não indicam gênero (o número fica no masculino)
_NEUTRAS = {"de", "a", "e", "o", "ou", "em", "por", "para", "anos", "ano"}
# femininos que a regra de terminação não pega
_FEM_EXTRA = {"vez", "vezes", "mulher", "mulheres", "noite", "noites", "tarde", "tardes",
              "cor", "cores", "flor", "flores", "dor", "dores", "lei", "leis", "mão", "mãos",
              "foto", "fotos", "tribo", "tribos", "rede", "redes", "parede", "paredes"}


def _proxima_feminina(resto: str) -> bool:
    m = re.match(r"\s+([A-Za-zÀ-ÿ]+)", resto)
    if not m:
        return False
    palavra = m.group(1).lower()
    if palavra in _NEUTRAS:
        return False
    if palavra in _FEM_EXTRA:
        return True
    singular = palavra[:-1] if palavra.endswith("s") else palavra
    if singular in _MASC_EM_A or palavra in _MASC_EM_A:
        return False
    return singular.endswith(("a", "ã", "ade", "ção", "são", "gem", "agem"))


def _numero_feminino_pt(falado: str) -> str:
    trocas = {"um": "uma", "dois": "duas"}
    saida = []
    for p in falado.split():
        if p in trocas:
            p = trocas[p]
        elif p.endswith("entos"):
            p = p[:-5] + "entas"
        saida.append(p)
    return " ".join(saida)


def numeros_por_extenso(texto: str, idioma: str) -> str:
    """Converte números em palavras. Idiomas não suportados ficam como estão."""
    try:
        _n2w(1, idioma)
    except Exception:
        return texto
    w = _PALAVRAS.get(idioma, _PALAVRAS["en"])
    num = r"\d+(?:[.,]\d+)*"

    def moeda(m, unidade_sing, unidade_plur):
        token = m.group("n")
        inteiro, _ = _parse(token, idioma)
        falado = _numero_falado(token, idioma)
        sufixo = (m.group("mult") or "").strip()
        if sufixo:
            plural = unidade_plur if idioma != "pt" else f"de {unidade_plur}"
            return f"{falado} {sufixo} {plural}"
        return f"{falado} {unidade_sing if inteiro == 1 and not _parse(token, idioma)[1] else unidade_plur}"

    mult = (r"(?P<mult>\s+(?:milhões|milhão|bilhões|bilhão|trilhões|trilhão|millions|million"
            r"|billions|billion|millones|millón|mil)(?!\w))?")
    texto = re.sub(rf"R\$\s?(?P<n>{num}){mult}", lambda m: moeda(m, w["real"], w["reais"]), texto)
    texto = re.sub(rf"(?:US\$|U\$|\$)\s?(?P<n>{num}){mult}", lambda m: moeda(m, w["dolar"], w["dolares"]), texto)
    texto = re.sub(rf"€\s?(?P<n>{num}){mult}", lambda m: moeda(m, w["euro"], w["euros"]), texto)
    texto = re.sub(rf"(?P<n>{num})\s?%", lambda m: f"{_numero_falado(m.group('n'), idioma)} {w['pct']}", texto)

    if idioma == "pt":
        texto = re.sub(r"(\d+)[º°]", lambda m: _n2w(int(m.group(1)), idioma, to="ordinal"), texto)
        texto = re.sub(r"(\d+)ª", lambda m: _feminino_pt(_n2w(int(m.group(1)), idioma, to="ordinal")), texto)
    elif idioma == "en":
        texto = re.sub(r"(\d+)(?:st|nd|rd|th)\b", lambda m: _n2w(int(m.group(1)), idioma, to="ordinal"), texto)
        # anos (1900-2099) lidos como "nineteen ninety-eight"
        texto = re.sub(r"\b(1[1-9]\d\d|20\d\d)\b(?![.,]\d)", lambda m: _n2w(int(m.group(1)), idioma, to="year"), texto)

    def comum(m):
        token = m.group(0).rstrip(".,")
        resto = m.group(0)[len(token):]
        try:
            falado = _numero_falado(token, idioma)
        except (ValueError, OverflowError):
            return m.group(0)
        if idioma == "pt" and _proxima_feminina(m.string[m.end():]):
            falado = _numero_feminino_pt(falado)
        return falado + resto

    texto = re.sub(num, comum, texto)
    return texto


# --------------------------------------------------------------- divisão

@dataclass
class Parte:
    indice: int
    texto: str
    fim_paragrafo: bool


_FIM_FRASE = re.compile(r"(?<=[.!?…])[\"'”’»)]*\s+(?=[\"'“‘«(¿¡A-ZÀ-ÖØ-Þ0-9])")


def _frases(paragrafo: str) -> list[str]:
    return [f.strip() for f in _FIM_FRASE.split(paragrafo) if f.strip()]


def _quebrar_longa(frase: str, maximo: int) -> list[str]:
    """Quebra uma frase longa em vírgulas/ponto e vírgula; em último caso, em espaços."""
    if len(frase) <= maximo:
        return [frase]
    pedacos = re.split(r"(?<=[,;:—–])\s+", frase)
    saida: list[str] = []
    atual = ""
    for p in pedacos:
        if len(p) > maximo:
            if atual:
                saida.append(atual)
                atual = ""
            palavras = p.split()
            linha = ""
            for pal in palavras:
                if linha and len(linha) + 1 + len(pal) > maximo:
                    saida.append(linha)
                    linha = pal
                else:
                    linha = f"{linha} {pal}".strip()
            if linha:
                saida.append(linha)
            continue
        if atual and len(atual) + 1 + len(p) > maximo:
            saida.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    if atual:
        saida.append(atual)
    return saida


def dividir(paragrafos: list[str], max_caracteres: int = 220) -> list[Parte]:
    partes: list[Parte] = []
    for paragrafo in paragrafos:
        blocos: list[str] = []
        atual = ""
        for frase in _frases(paragrafo):
            for pedaco in _quebrar_longa(frase, max_caracteres):
                if atual and len(atual) + 1 + len(pedaco) > max_caracteres:
                    blocos.append(atual)
                    atual = pedaco
                else:
                    atual = f"{atual} {pedaco}".strip()
        if atual:
            blocos.append(atual)
        for i, b in enumerate(blocos):
            partes.append(Parte(indice=len(partes) + 1, texto=b, fim_paragrafo=(i == len(blocos) - 1)))
    return partes


def preparar(texto: str, idioma: str, max_caracteres: int = 220) -> list[Parte]:
    paragrafos = [numeros_por_extenso(p, idioma) for p in limpar(texto)]
    return dividir(paragrafos, max_caracteres)
