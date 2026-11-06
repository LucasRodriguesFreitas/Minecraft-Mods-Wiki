"""
Peças compartilhadas pelos extratores: o formato do Documento, a leitura dos
.jar dos mods e a limpeza de texto.
"""

import json
import re
import tomllib
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Documento:
    """Um pedaço de conhecimento extraído do modpack."""

    id: str      # único; ex.: "patchouli:ars_nouveau:basics/spell_book"
    fonte: str   # "quest" | "patchouli" | "guia_md" | "descricao_item"
    mod: str     # nome legível do mod (ex.: "Applied Energistics 2")
    titulo: str  # título da entrada / item / quest
    texto: str   # conteúdo já limpo
    origem: str  # arquivo de onde veio (para citar e depurar)

    def para_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class ModJar:
    caminho: Path
    mod_id: str
    nome: str
    versao: str


# ---------------------------------------------------------------- mods (.jar)

def _versao_como_tupla(versao: str) -> tuple:
    """'8.2.23+mc1.21.1' -> (8, 2, 23, 1, 21, 1). Serve para comparar versões."""
    return tuple(int(n) for n in re.findall(r"\d+", versao))


def ler_info_mod(caminho: Path) -> ModJar:
    """Lê o META-INF/neoforge.mods.toml do .jar para descobrir id, nome e versão."""
    padrao = ModJar(caminho, caminho.stem.lower(), caminho.stem, caminho.stem)
    try:
        with zipfile.ZipFile(caminho) as jar:
            for arquivo_toml in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
                if arquivo_toml in jar.namelist():
                    dados = tomllib.loads(jar.read(arquivo_toml).decode("utf-8", errors="ignore"))
                    mod = dados["mods"][0]
                    versao = str(mod.get("version", ""))
                    if "${" in versao:  # versão preenchida só no build; usa o nome do arquivo
                        versao = caminho.stem
                    return ModJar(caminho, mod["modId"], mod.get("displayName", mod["modId"]), versao)
    except (zipfile.BadZipFile, tomllib.TOMLDecodeError, KeyError, IndexError):
        pass
    return padrao


def listar_mods(pasta_mods: Path) -> tuple[list[ModJar], list[str]]:
    """
    Lista os mods da pasta. Se o mesmo mod aparecer duas vezes (ex.: duas
    versões do PneumaticCraft), fica só a versão mais nova.
    Retorna (mods, avisos).
    """
    por_id: dict[str, ModJar] = {}
    avisos = []
    for caminho in sorted(pasta_mods.glob("*.jar")):
        mod = ler_info_mod(caminho)
        atual = por_id.get(mod.mod_id)
        if atual:
            novo, velho = sorted([atual, mod], key=lambda m: _versao_como_tupla(m.versao), reverse=True)
            avisos.append(f"Mod duplicado '{mod.mod_id}': usando {novo.caminho.name}, ignorando {velho.caminho.name}")
            por_id[mod.mod_id] = novo
        else:
            por_id[mod.mod_id] = mod
    return list(por_id.values()), avisos


# ---------------------------------------------------------------- texto

def limpar_espacos(texto: str) -> str:
    texto = re.sub(r"§.", "", texto)              # códigos de cor do Minecraft (§a, §l...)
    texto = re.sub(r"[ \t]+", " ", texto)         # espaços repetidos
    texto = re.sub(r"\n\s*\n\s*\n+", "\n\n", texto)  # no máximo uma linha em branco
    return texto.strip()


def nome_do_item(item_id: str, traducoes: dict[str, str]) -> str:
    """'ae2:controller' -> 'ME Controller' (usando as traduções en_us)."""
    item_id = re.split(r"[\[{]", item_id, maxsplit=1)[0].strip()  # remove NBT/componentes
    if ":" not in item_id:
        return item_id
    mod_id, caminho = item_id.split(":", 1)
    chave = caminho.replace("/", ".")
    for prefixo in ("item", "block", "fluid", "entity"):
        nome = traducoes.get(f"{prefixo}.{mod_id}.{chave}")
        if nome:
            return limpar_espacos(nome)
    return caminho.replace("_", " ")


def ler_env(caminho: Path) -> dict[str, str]:
    """Leitor mínimo de .env (só a biblioteca padrão, sem instalar nada)."""
    valores = {}
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                valores[chave.strip()] = valor.strip().strip('"')
    return valores
