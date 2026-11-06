"""
explorar_modpack.py — Etapa 0 do projeto.

Lê a pasta de um modpack (ex.: ATM10) e mostra QUAIS fontes de conhecimento
existem dentro dele, antes de escrevermos os extratores de verdade.

O que ele procura:
  - mods/*.jar  -> um .jar é só um arquivo .zip. Dentro dele procuramos:
      * arquivos de tradução (assets/<mod>/lang/en_us.json) -> nomes e descrições de itens
      * livros-guia no formato Patchouli (pastas "patchouli_books")
      * guias em Markdown (.md) dentro de assets (ex.: guia do AE2)
      * receitas (data/<mod>/recipe/ ou recipes/)
  - config/ftbquests/ -> as quests do modpack
  - kubejs/           -> scripts que o modpack usa para alterar receitas

Uso (Windows, dentro da pasta do projeto):
    python scripts\\explorar_modpack.py "C:\\caminho\\para\\pasta\\do\\ATM10"

Gera:
    - um resumo no terminal
    - data/relatorio_exploracao.json com o detalhe por mod

Só usa a biblioteca padrão do Python: não precisa instalar nada.
"""

import json
import sys
import zipfile
from collections import Counter
from pathlib import Path


def analisar_jar(caminho_jar: Path) -> dict:
    """Abre um .jar (zip) e conta as fontes de conhecimento que ele tem."""
    info = {
        "arquivo": caminho_jar.name,
        "mod_ids": set(),
        "lang_en_us_chaves": 0,
        "patchouli_arquivos": 0,
        "guia_markdown_arquivos": 0,
        "receitas": 0,
        "erro": None,
    }
    try:
        with zipfile.ZipFile(caminho_jar) as jar:
            for nome in jar.namelist():
                partes = nome.split("/")

                # assets/<modid>/... ou data/<modid>/... -> descobre o id do mod
                if len(partes) > 2 and partes[0] in ("assets", "data"):
                    info["mod_ids"].add(partes[1])

                if nome.endswith("lang/en_us.json"):
                    try:
                        dados = json.loads(jar.read(nome).decode("utf-8", errors="ignore"))
                        info["lang_en_us_chaves"] += len(dados)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass  # alguns mods têm JSON fora do padrão; ignoramos aqui

                elif "patchouli_books" in nome and nome.endswith(".json") and "/en_us/" in nome:
                    info["patchouli_arquivos"] += 1

                elif nome.startswith("assets/") and nome.endswith(".md"):
                    info["guia_markdown_arquivos"] += 1

                elif nome.startswith("data/") and ("/recipe/" in nome or "/recipes/" in nome) and nome.endswith(".json"):
                    info["receitas"] += 1
    except zipfile.BadZipFile:
        info["erro"] = "arquivo corrompido ou não é zip"

    info["mod_ids"] = sorted(info["mod_ids"])
    return info


def analisar_quests(pasta_modpack: Path) -> dict:
    """Mostra como as quests do FTB Quests estão organizadas nesta versão."""
    pasta = pasta_modpack / "config" / "ftbquests"
    if not pasta.exists():
        return {"encontrado": False}

    arquivos = [p for p in pasta.rglob("*") if p.is_file()]
    extensoes = Counter(p.suffix for p in arquivos)
    # Lista as subpastas para entendermos a estrutura (ex.: chapters/, lang/)
    subpastas = sorted({str(p.parent.relative_to(pasta)) for p in arquivos})
    # Guarda um pedacinho de 2 arquivos de exemplo para vermos o formato
    exemplos = {}
    for p in arquivos[:200]:
        if p.suffix == ".snbt" and len(exemplos) < 2:
            texto = p.read_text(encoding="utf-8", errors="ignore")
            exemplos[str(p.relative_to(pasta))] = texto[:800]

    return {
        "encontrado": True,
        "total_arquivos": len(arquivos),
        "extensoes": dict(extensoes),
        "subpastas": subpastas[:30],
        "exemplos": exemplos,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/explorar_modpack.py <pasta_do_modpack>")
        sys.exit(1)

    pasta_modpack = Path(sys.argv[1]).expanduser().resolve()
    pasta_mods = pasta_modpack / "mods"
    if not pasta_mods.exists():
        print(f"Não achei a pasta 'mods' em: {pasta_modpack}")
        print("Confira se você apontou para a pasta que CONTÉM 'mods' e 'config'.")
        sys.exit(1)

    jars = sorted(pasta_mods.glob("*.jar"))
    print(f"Analisando {len(jars)} mods em {pasta_mods} ...\n")

    mods = []
    for i, jar in enumerate(jars, start=1):
        mods.append(analisar_jar(jar))
        if i % 50 == 0:
            print(f"  {i}/{len(jars)} mods lidos...")

    quests = analisar_quests(pasta_modpack)
    tem_kubejs = (pasta_modpack / "kubejs").exists()

    # ---------- Resumo ----------
    def total(campo):
        return sum(m[campo] for m in mods)

    def qtd_mods_com(campo):
        return sum(1 for m in mods if m[campo] > 0)

    print("\n================ RESUMO ================")
    print(f"Mods (.jar):                    {len(mods)}")
    print(f"Chaves de tradução (en_us):     {total('lang_en_us_chaves'):>7}  em {qtd_mods_com('lang_en_us_chaves')} mods")
    print(f"Arquivos de livros Patchouli:   {total('patchouli_arquivos'):>7}  em {qtd_mods_com('patchouli_arquivos')} mods")
    print(f"Guias em Markdown (.md):        {total('guia_markdown_arquivos'):>7}  em {qtd_mods_com('guia_markdown_arquivos')} mods")
    print(f"Receitas (JSON):                {total('receitas'):>7}  em {qtd_mods_com('receitas')} mods")
    print(f"FTB Quests encontrado:          {quests.get('encontrado')}")
    if quests.get("encontrado"):
        print(f"  arquivos: {quests['total_arquivos']}  extensões: {quests['extensoes']}")
        print(f"  subpastas: {', '.join(quests['subpastas'][:10])}")
    print(f"Pasta kubejs/ existe:           {tem_kubejs}")

    print("\nTop 10 mods com mais conteúdo de guia (Patchouli + Markdown):")
    ranking = sorted(mods, key=lambda m: m["patchouli_arquivos"] + m["guia_markdown_arquivos"], reverse=True)
    for m in ranking[:10]:
        soma = m["patchouli_arquivos"] + m["guia_markdown_arquivos"]
        if soma:
            print(f"  {soma:>5}  {m['arquivo']}")

    erros = [m for m in mods if m["erro"]]
    if erros:
        print(f"\n{len(erros)} arquivos não puderam ser abertos (veja o relatório).")

    # ---------- Relatório completo ----------
    saida = Path(__file__).resolve().parent.parent / "data" / "relatorio_exploracao.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(
        json.dumps({"mods": mods, "quests": quests, "kubejs": tem_kubejs}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nRelatório completo salvo em: {saida}")


if __name__ == "__main__":
    main()
