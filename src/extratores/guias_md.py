"""
Guias escritos em Markdown dentro dos .jar (ex.: o guia do AE2 e do ExtendedAE,
feitos com a biblioteca GuideME).

Formato típico:
    ---
    navigation:
      title: ME Controller
      parent: ae2-mechanics/index.md
    item_ids:
      - ae2:controller
    ---
    # The ME Controller
    <ItemImage id="controller" scale="4" />
    The controller is the "brain" of the network...
    <RecipeFor id="controller" />

Mantemos o texto e trocamos as tags especiais por algo legível.
Traduções do guia ficam em pastas como "_pt_br/" e são ignoradas aqui
(usamos o inglês, que é o mais completo).
"""

import re
import zipfile

from .comum import Documento, ModJar, limpar_espacos, nome_do_item

PADRAO_PASTA_IDIOMA = re.compile(r"^_[a-z]{2}_[a-z]{2}$")


def _id_completo(item_id: str, mod_id: str) -> str:
    return item_id if ":" in item_id else f"{mod_id}:{item_id}"


def limpar_markdown(texto: str, mod_id: str, traducoes: dict[str, str]) -> tuple[str, str | None]:
    """Retorna (texto_limpo, titulo_do_frontmatter)."""
    titulo = None
    frontmatter = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n", texto, re.S)
    if frontmatter:
        m = re.search(r"^\s*title:\s*(.+)$", frontmatter.group(1), re.M)
        if m:
            titulo = m.group(1).strip().strip("\"'")
        texto = texto[frontmatter.end():]

    def receita(m):
        return f"(Receita: {nome_do_item(_id_completo(m.group(1), mod_id), traducoes)})"

    def link_item(m):
        return nome_do_item(_id_completo(m.group(1), mod_id), traducoes)

    texto = re.sub(r"<GameScene.*?</GameScene>", "", texto, flags=re.S | re.I)   # cenas 3D
    texto = re.sub(r"<Recipes?For\s+id=\"([^\"]+)\"[^>]*/>", receita, texto)
    texto = re.sub(r"<ItemLink\s+id=\"([^\"]+)\"[^>]*/>", link_item, texto)
    texto = re.sub(r"<[^>]+>", "", texto)                       # demais tags (imagens, etc.)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)          # imagens markdown
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)      # links -> só o texto
    return limpar_espacos(texto), titulo


def extrair_guias_md(mods: list[ModJar], traducoes: dict[str, str]) -> list[Documento]:
    documentos = []
    for mod in mods:
        try:
            jar = zipfile.ZipFile(mod.caminho)
        except zipfile.BadZipFile:
            continue
        with jar:
            for nome in jar.namelist():
                if not (nome.startswith("assets/") and nome.endswith(".md")):
                    continue
                partes = nome.split("/")
                if any(PADRAO_PASTA_IDIOMA.match(p) for p in partes):
                    continue  # tradução do guia; usamos o original em inglês
                mod_id = partes[1]
                bruto = jar.read(nome).decode("utf-8", errors="ignore")
                texto, titulo = limpar_markdown(bruto, mod_id, traducoes)
                if len(texto) < 30:
                    continue
                if not titulo:
                    cabecalho = re.search(r"^#\s+(.+)$", texto, re.M)
                    titulo = cabecalho.group(1).strip() if cabecalho else partes[-1].removesuffix(".md")
                documentos.append(
                    Documento(
                        id=f"md:{mod_id}:{'/'.join(partes[2:])}",
                        fonte="guia_md",
                        mod=mod.nome,
                        titulo=titulo,
                        texto=texto,
                        origem=f"{mod.caminho.name}/{nome}",
                    )
                )
    return documentos
