"""
amostras_quests.py — coleta pedaços dos arquivos do FTB Quests para entendermos
o formato antes de escrever o extrator de quests.

Uso (Windows):
    python scripts\\amostras_quests.py                  (usa MODPACK_PATH do .env)
    python scripts\\amostras_quests.py "C:\\caminho\\do\\modpack"

Gera data/amostras_quests.txt
"""

import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.extratores.comum import ler_env  # noqa: E402


def trecho(arquivo: Path, limite: int) -> str:
    texto = arquivo.read_text(encoding="utf-8", errors="ignore")
    return texto[:limite] + (f"\n[... mais {len(texto) - limite} caracteres]" if len(texto) > limite else "")


def main() -> None:
    if len(sys.argv) > 1:
        pasta_modpack = Path(sys.argv[1])
    else:
        pasta_modpack = Path(ler_env(RAIZ / ".env").get("MODPACK_PATH", "."))
    quests = pasta_modpack / "config" / "ftbquests" / "quests"
    if not quests.exists():
        print(f"Não achei {quests}")
        sys.exit(1)

    saida = []
    escrever = saida.append

    lang = quests / "lang"
    idiomas = sorted(p.name for p in lang.iterdir()) if lang.exists() else []
    escrever(f"IDIOMAS em quests/lang: {idiomas}\n")
    escrever(f"Tem pt_br? {any('pt_br' in i for i in idiomas)}\n")

    merged = list(quests.rglob("*.snbt_merged"))
    pastas_merged = Counter(str(p.parent.relative_to(quests)) for p in merged)
    escrever(f"\nARQUIVOS .snbt_merged: {len(merged)} — pastas mais comuns:")
    for pasta, qtd in pastas_merged.most_common(8):
        escrever(f"  {qtd:>4}  {pasta}")

    capitulos = sorted((quests / "chapters").glob("*.snbt"), key=lambda p: p.stat().st_size)
    escrever(f"\nCAPÍTULOS: {len(capitulos)} arquivos")
    escrever("  " + ", ".join(p.stem for p in capitulos[:60]))

    def amostra(titulo: str, arquivo: Path | None, limite: int) -> None:
        if arquivo and arquivo.exists():
            escrever(f"\n\n########## {titulo}: {arquivo.relative_to(quests)}\n")
            escrever(trecho(arquivo, limite))
        else:
            escrever(f"\n\n########## {titulo}: (não encontrado)")

    amostra("data.snbt", quests / "data.snbt", 1200)

    if capitulos:
        meio = capitulos[len(capitulos) // 2]
        amostra("CAPÍTULO (tamanho mediano)", meio, 3500)
        for idioma in ("en_us", "pt_br"):
            for extensao in (".snbt", ".snbt_merged"):
                candidatos = list((lang / idioma).rglob(f"{meio.stem}{extensao}")) if (lang / idioma).exists() else []
                amostra(f"TEXTO DO CAPÍTULO em {idioma} ({extensao})", candidatos[0] if candidatos else None, 3000)

    amostra("lang/en_us.snbt", lang / "en_us.snbt", 2000)
    if merged:
        amostra("EXEMPLO .snbt_merged", merged[0], 2000)

    destino = RAIZ / "data" / "amostras_quests.txt"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text("\n".join(saida), encoding="utf-8")
    print(f"Amostras salvas em {destino}")


if __name__ == "__main__":
    main()
