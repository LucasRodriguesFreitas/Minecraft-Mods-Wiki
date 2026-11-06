"""
Livros-guia no formato Patchouli.

Cada "entrada" do livro é um JSON em:
    assets/<mod>/patchouli_books/<livro>/en_us/entries/<categoria>/<entrada>.json

Formato típico:
    {
      "name": "Spell Book",
      "category": "ars_nouveau:basics",
      "pages": [
        {"type": "patchouli:text", "text": "The $(item)Spell Book$() is..."},
        {"type": "patchouli:crafting", "recipe": "ars_nouveau:novice_spell_book"}
      ]
    }

O texto usa códigos de formatação do Patchouli ($(item), $(br), $(l:...))
que removemos. Alguns livros usam chaves de tradução no lugar do texto
(livros "i18n"): nesses casos trocamos a chave pelo texto do en_us.json.
"""

import json
import re
import zipfile

from .comum import Documento, ModJar, limpar_espacos, nome_do_item

PADRAO_ENTRADA = re.compile(r"^(assets|data)/([^/]+)/patchouli_books/([^/]+)/en_us/entries/(.+)\.json$")
CAMPOS_DE_ITEM = ("item", "recipe", "recipe2", "entity", "multiblock_id")


def limpar_patchouli(texto: str) -> str:
    texto = texto.replace("$(br2)", "\n\n").replace("$(br)", "\n")
    texto = texto.replace("$(li2)", "\n  - ").replace("$(li)", "\n- ")
    texto = re.sub(r"\$\(k:([^)]+)\)", r"[tecla \1]", texto)  # $(k:use) -> [tecla use]
    texto = re.sub(r"\$\([^)]*\)", "", texto)                   # todos os outros códigos
    return limpar_espacos(texto)


def _traduzir(valor, traducoes: dict[str, str]):
    if isinstance(valor, str):
        return traducoes.get(valor, valor)
    return valor


def _texto_da_pagina(pagina: dict, traducoes: dict[str, str]) -> str:
    if isinstance(pagina, str):  # formato antigo: página é só um texto
        return limpar_patchouli(_traduzir(pagina, traducoes))

    partes = []
    titulo = _traduzir(pagina.get("title"), traducoes)
    if isinstance(titulo, str) and titulo:
        partes.append(f"## {limpar_patchouli(titulo)}")

    for campo in CAMPOS_DE_ITEM:
        valor = pagina.get(campo)
        if isinstance(valor, str) and ":" in valor:
            nomes = [nome_do_item(v, traducoes) for v in valor.split(",")]
            rotulo = "Receita" if campo.startswith("recipe") else "Item"
            partes.append(f"({rotulo}: {', '.join(nomes)})")

    texto = _traduzir(pagina.get("text"), traducoes)
    if isinstance(texto, str) and texto:
        partes.append(limpar_patchouli(texto))
    return "\n".join(partes)


def _nomes_dos_livros(jar: zipfile.ZipFile, traducoes: dict[str, str]) -> dict[str, str]:
    """Lê os book.json para saber o nome de cada livro (ex.: 'Worn Notebook')."""
    nomes = {}
    for nome in jar.namelist():
        m = re.match(r"^(assets|data)/[^/]+/patchouli_books/([^/]+)/book\.json$", nome)
        if m:
            try:
                dados = json.loads(jar.read(nome).decode("utf-8", errors="ignore"))
                nomes[m.group(2)] = limpar_patchouli(_traduzir(dados.get("name", m.group(2)), traducoes))
            except json.JSONDecodeError:
                pass
    return nomes


def extrair_patchouli(mods: list[ModJar], traducoes: dict[str, str]) -> list[Documento]:
    documentos = []
    for mod in mods:
        try:
            jar = zipfile.ZipFile(mod.caminho)
        except zipfile.BadZipFile:
            continue
        with jar:
            nomes_livros = None
            for nome in jar.namelist():
                m = PADRAO_ENTRADA.match(nome)
                if not m:
                    continue
                if nomes_livros is None:
                    nomes_livros = _nomes_dos_livros(jar, traducoes)
                _, mod_id, livro, caminho_entrada = m.groups()
                try:
                    dados = json.loads(jar.read(nome).decode("utf-8", errors="ignore"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(dados, dict):
                    continue

                titulo = limpar_patchouli(str(_traduzir(dados.get("name", caminho_entrada), traducoes)))
                paginas = [_texto_da_pagina(p, traducoes) for p in dados.get("pages", [])]
                texto = limpar_espacos("\n\n".join(p for p in paginas if p))
                if len(texto) < 30:
                    continue

                nome_livro = nomes_livros.get(livro, livro)
                documentos.append(
                    Documento(
                        id=f"patchouli:{mod_id}:{livro}:{caminho_entrada}",
                        fonte="patchouli",
                        mod=mod.nome,
                        titulo=f"{nome_livro} › {titulo}",
                        texto=texto,
                        origem=f"{mod.caminho.name}/{nome}",
                    )
                )
    return documentos
