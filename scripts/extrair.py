"""
extrair.py — Etapa 1: transforma os arquivos do modpack em documentos de texto.

Uso (Windows):
    python scripts\\extrair.py                  (usa MODPACK_PATH do .env)
    python scripts\\extrair.py "C:\\caminho\\do\\modpack"

Gera:
    data/documentos.jsonl          um documento por linha (é o que a Etapa 2 indexa)
    data/exemplos_extracao.txt     alguns exemplos de cada fonte, para conferir a qualidade
"""

import random
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))  # permite "from src..." rodando de dentro de scripts/

from src.extratores.comum import ler_env, listar_mods          # noqa: E402
from src.extratores.guias_md import extrair_guias_md           # noqa: E402
from src.extratores.patchouli import extrair_patchouli         # noqa: E402
from src.extratores.traducoes import carregar_traducoes, extrair_descricoes  # noqa: E402


def descobrir_pasta_modpack() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    caminho = ler_env(RAIZ / ".env").get("MODPACK_PATH")
    if not caminho:
        print("Informe a pasta do modpack como argumento ou preencha MODPACK_PATH no .env")
        sys.exit(1)
    return Path(caminho).expanduser().resolve()


def main() -> None:
    inicio = time.time()
    pasta = descobrir_pasta_modpack()
    if not (pasta / "mods").exists():
        print(f"Não achei a pasta 'mods' em {pasta}")
        sys.exit(1)

    print("1/4 Lendo a lista de mods...")
    mods, avisos = listar_mods(pasta / "mods")
    for aviso in avisos:
        print(f"    aviso: {aviso}")
    print(f"    {len(mods)} mods únicos")

    print("2/4 Carregando traduções (en_us)...")
    traducoes, chave_para_mod = carregar_traducoes(mods, pasta)
    print(f"    {len(traducoes)} chaves")

    print("3/4 Extraindo documentos...")
    documentos = []
    for nome, funcao in [
        ("descrições de itens", lambda: extrair_descricoes(traducoes, chave_para_mod)),
        ("livros Patchouli", lambda: extrair_patchouli(mods, traducoes)),
        ("guias Markdown", lambda: extrair_guias_md(mods, traducoes)),
    ]:
        novos = funcao()
        print(f"    {nome}: {len(novos)}")
        documentos.extend(novos)

    # Remove IDs repetidos (pode acontecer com o mesmo guia em dois jars)
    unicos = {d.id: d for d in documentos}
    documentos = list(unicos.values())

    print("4/4 Salvando...")
    pasta_dados = RAIZ / "data"
    pasta_dados.mkdir(exist_ok=True)
    with open(pasta_dados / "documentos.jsonl", "w", encoding="utf-8") as f:
        for doc in documentos:
            f.write(doc.para_json() + "\n")

    # ---------- Estatísticas ----------
    por_fonte = Counter(d.fonte for d in documentos)
    caracteres = sum(len(d.texto) for d in documentos)
    print("\n================ RESULTADO ================")
    for fonte, qtd in por_fonte.most_common():
        media = sum(len(d.texto) for d in documentos if d.fonte == fonte) // qtd
        print(f"{fonte:<16} {qtd:>6} documentos   (média {media} caracteres)")
    print(f"{'TOTAL':<16} {len(documentos):>6} documentos   (~{caracteres // 4:,} tokens)")

    print("\nMods com mais documentos:")
    for mod, qtd in Counter(d.mod for d in documentos).most_common(10):
        print(f"  {qtd:>5}  {mod}")

    # ---------- Exemplos para conferência ----------
    random.seed(42)
    with open(pasta_dados / "exemplos_extracao.txt", "w", encoding="utf-8") as f:
        for fonte in por_fonte:
            docs_fonte = [d for d in documentos if d.fonte == fonte]
            for doc in random.sample(docs_fonte, min(3, len(docs_fonte))):
                f.write(f"=== [{doc.fonte}] {doc.mod} — {doc.titulo}\n")
                f.write(f"    origem: {doc.origem}\n")
                f.write(doc.texto[:700] + ("\n[...]" if len(doc.texto) > 700 else "") + "\n\n")

    print(f"\nPronto em {time.time() - inicio:.0f}s. Arquivos em {pasta_dados}")
    print("Confira data/exemplos_extracao.txt para ver se o texto ficou legível.")


if __name__ == "__main__":
    main()
