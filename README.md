# Modpack AI Wiki 🧱🤖

Assistente de IA que responde perguntas sobre mods do Minecraft em português ("como faço uma ME Controller?", "qual o próximo passo para o ATM Star?") usando **o conteúdo do próprio modpack** como fonte: quests, livros-guia e descrições dos itens.

Testado com **All the Mods 10 (ATM10)**, NeoForge 1.21.1, mas a ideia é funcionar com qualquer modpack.

> 🚧 **Status:** em desenvolvimento, Etapa 0 (exploração dos dados).

## Como funciona

A técnica usada é **RAG (Retrieval-Augmented Generation)**: em vez de confiar no que o modelo "lembra", o sistema busca os trechos relevantes nos arquivos do modpack e entrega ao LLM junto com a pergunta.

```
          INGESTÃO (roda uma vez por versão do modpack)
arquivos do modpack ──► extratores ──► pedaços de texto ──► embeddings ──► ChromaDB
 (quests, guias, lang)

          PERGUNTA (a cada uso)
pergunta (PT-BR) ──► busca os trechos mais parecidos no ChromaDB
                 ──► LLM (Gemini) recebe pergunta + trechos
                 ──► resposta em PT-BR citando a fonte (quest / mod)
```

**Não é um mod.** Roda fora do jogo e não precisa do servidor ligado, só dos arquivos do modpack.

## Stack

| Parte | Tecnologia | Por quê |
|---|---|---|
| Linguagem | Python 3.12 | Ecossistema de IA |
| Extração | `zipfile` (stdlib) | Arquivos `.jar` são zips |
| Embeddings | `sentence-transformers` (modelo multilíngue) | Roda local, grátis, pergunta em PT e texto em EN |
| Banco vetorial | ChromaDB | Local, sem servidor |
| LLM | Gemini API (free tier) | Grátis para prototipar |
| Interface | CLI → bot de Discord | Discord não exige abrir portas no roteador |

## Roadmap

- [ ] **Etapa 0:** ambiente, repositório e exploração dos arquivos do modpack
- [ ] **Etapa 1:** extratores (quests, nomes/descrições de itens, livros-guia) → `data/documentos.jsonl`
- [ ] **Etapa 2:** indexação (embeddings + ChromaDB) e RAG pelo terminal, com citação das fontes
- [ ] **Etapa 3:** conjunto de perguntas de teste (`eval/`) para medir a qualidade + bot de Discord
- [ ] **Etapa 4:** documentação final, diagrama e GIF de demonstração
- [ ] Futuro: interface web, perguntas de dentro do jogo via RCON, painel do servidor

## Como rodar (Windows)

```powershell
git clone <url-do-repo>
cd modpack-ai-wiki
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # e preencha as chaves

# Etapa 0: ver o que existe dentro do modpack
python scripts\explorar_modpack.py "C:\caminho\para\o\modpack"
```

> ⚠️ Os arquivos do modpack **não** são versionados neste repositório (licenças dos mods). Cada pessoa usa a própria cópia baixada do CurseForge.

## Estrutura

```
modpack-ai-wiki/
├── scripts/      utilitários (exploração, ingestão)
├── src/          código principal (extratores, RAG, interfaces)
├── eval/         perguntas de teste e resultados
├── docs/         decisões técnicas e diagramas
└── data/         dados gerados (ignorado pelo git)
```
