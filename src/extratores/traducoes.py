"""
Arquivos de tradução (assets/<mod>/lang/en_us.json).

Servem para duas coisas:
  1. Dicionário chave -> texto, para trocar IDs ("ae2:controller") por nomes
     ("ME Controller") nos outros extratores.
  2. Fonte de conhecimento: muitos mods colocam a DESCRIÇÃO dos itens (tooltip)
     no arquivo de tradução. Esses textos viram documentos.
"""

import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from .comum import Documento, ModJar, limpar_espacos

# Chaves que costumam guardar descrições, não só nomes
PADRAO_DESCRICAO = re.compile(r"(tooltip|desc|description|info|lore|hint|guide)", re.IGNORECASE)
TAMANHO_MINIMO = 40  # descrições muito curtas ("Shift for info") não ajudam


def _ler_json_tolerante(bruto: bytes) -> dict:
    texto = bruto.decode("utf-8-sig", errors="ignore")
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        # alguns mods deixam vírgula sobrando no final; tentamos corrigir
        try:
            return json.loads(re.sub(r",\s*}", "}", texto))
        except json.JSONDecodeError:
            return {}


def carregar_traducoes(mods: list[ModJar], pasta_modpack: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Retorna (traducoes, chave_para_mod):
      traducoes:      chave -> texto em inglês
      chave_para_mod: chave -> nome do mod que a definiu
    """
    traducoes: dict[str, str] = {}
    chave_para_mod: dict[str, str] = {}

    for mod in mods:
        try:
            with zipfile.ZipFile(mod.caminho) as jar:
                for nome in jar.namelist():
                    if nome.startswith("assets/") and nome.endswith("/lang/en_us.json"):
                        for chave, valor in _ler_json_tolerante(jar.read(nome)).items():
                            if isinstance(valor, str):
                                traducoes[chave] = valor
                                chave_para_mod[chave] = mod.nome
        except zipfile.BadZipFile:
            continue

    # O modpack pode ter itens próprios via KubeJS
    for arquivo in (pasta_modpack / "kubejs" / "assets").glob("*/lang/en_us.json"):
        for chave, valor in _ler_json_tolerante(arquivo.read_bytes()).items():
            if isinstance(valor, str):
                traducoes[chave] = valor
                chave_para_mod[chave] = "Modpack (KubeJS)"

    return traducoes, chave_para_mod


def _chave_base(chave: str, traducoes: dict[str, str]) -> str | None:
    """
    'item.mekanism.jetpack.tooltip.1' -> 'item.mekanism.jetpack' (se essa chave existir).
    Vai cortando o final até achar a chave do nome do item.
    """
    partes = chave.split(".")
    for fim in range(len(partes) - 1, 2, -1):
        candidata = ".".join(partes[:fim])
        if candidata in traducoes and candidata.split(".")[0] in ("item", "block"):
            return candidata
    return None


def extrair_descricoes(traducoes: dict[str, str], chave_para_mod: dict[str, str]) -> list[Documento]:
    """Agrupa as linhas de descrição por item e gera um documento por item."""
    por_item: dict[str, list[str]] = defaultdict(list)
    for chave, valor in traducoes.items():
        if not PADRAO_DESCRICAO.search(chave):
            continue
        base = _chave_base(chave, traducoes) or chave
        por_item[base].append(valor)

    documentos = []
    for base, linhas in por_item.items():
        texto = limpar_espacos("\n".join(linhas))
        if len(texto) < TAMANHO_MINIMO:
            continue
        titulo = limpar_espacos(traducoes.get(base, base)) if base in traducoes else base
        documentos.append(
            Documento(
                id=f"lang:{base}",
                fonte="descricao_item",
                mod=chave_para_mod.get(base, ""),
                titulo=titulo,
                texto=texto,
                origem=f"lang/en_us.json ({base})",
            )
        )
    return documentos
