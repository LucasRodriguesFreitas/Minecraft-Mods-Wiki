# Decisões técnicas

Registro curto de cada decisão importante: o que foi escolhido e por quê. Ajuda a explicar o projeto numa entrevista.

## 001: Escopo inicial só com a IA (wiki)
O painel de servidor fica para depois. Primeiro um assistente funcional e bem documentado.

## 002: RAG em vez de fine-tuning
O conteúdo muda a cada versão do modpack. Com RAG basta reindexar; o modelo não precisa ser treinado de novo. As respostas também podem citar a fonte.

## 003: Fonte = arquivos do próprio modpack
Quests, traduções e livros-guia estão dentro dos arquivos do modpack e batem com a versão que a gente joga. Wikis online podem estar desatualizadas ou ser de outra versão.

## 004: Embeddings locais e multilíngues
A pergunta vem em português e o conteúdo está em inglês. Um modelo multilíngue rodando local evita limites de requisição da API durante a ingestão (milhares de trechos) e não custa nada.

## 005: Discord como primeira interface para outras pessoas
O bot se conecta ao Discord "de dentro para fora", então não precisa abrir portas no roteador nem se preocupar com CGNAT. Os amigos já estão lá.

## 006: Mods duplicados → fica a versão mais nova
A pasta de mods do ATM10 tinha duas versões do PneumaticCraft (8.2.21 e 8.2.23). O extrator lê o `neoforge.mods.toml` de cada `.jar`, agrupa pelo `modId` e mantém só a versão mais nova, para não indexar conteúdo repetido.

## 007: Receitas ficam fora da primeira versão
São mais de 120 mil arquivos JSON de receita, e o ATM10 altera várias receitas com scripts KubeJS. Indexar os JSON originais poderia gerar respostas erradas. Os guias já citam as receitas principais pelo nome.

## 008: Guias em inglês, resposta em português
Os guias traduzidos dentro dos mods são incompletos. Indexamos o inglês (mais completo) e o LLM responde em português.
