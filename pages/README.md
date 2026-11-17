# Site pessoal

Diário de projetos, observações, leituras e trajetória, publicado em
<https://lucas1silva.github.io/pages/>.

As páginas são geradas por um gerador estático próprio, em Python (pasta `sitegen/`):
ele lê arquivos Markdown, valida tudo e grava HTML.

## Rodar na sua máquina

No Git Bash, na pasta do projeto:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --require-hashes --no-deps -r requirements.txt

python -m unittest discover -s tests   # testes
python -m sitegen --servir             # prévia em http://127.0.0.1:8000/pages/
```

`python -m sitegen` sem opções gera o site em `_site/`, que é o que a esteira publica.

## Estrutura

```
content/
  diario/      entradas do diário (eventos, com data)
  projetos/    um arquivo por projeto
  leituras/    um arquivo por livro ou artigo
static/
  css/         estilo do site
  img/         imagens
templates/     moldes HTML (Jinja2)
sitegen/       o gerador
tests/         testes
site.toml      nome, descrição, links e caminho base do site
```

## Escrever conteúdo

Cada arquivo começa com metadados em TOML entre duas linhas `+++`, seguidos do texto em
Markdown. O nome do arquivo vira o endereço da página, então use só letras minúsculas,
números e hífens: `content/diario/este-site.md` vira `/pages/diario/este-site/`.

Datas vão sem aspas (`2026-11-14`); textos vão entre aspas.

### Entrada do diário

```toml
+++
titulo = "Título da entrada"
data = 2026-11-14
tipo = "projeto"            # projeto, observacao, leitura ou trajetoria
resumo = "Uma ou duas frases que aparecem na lista do diário."
projeto = "site-pessoal"    # opcional: nome de um arquivo em content/projetos
leitura = "nome-do-livro"   # opcional: nome de um arquivo em content/leituras

[[imagens]]                 # opcional, pode repetir
arquivo = "site-pessoal/inicio.png"
alt = "O que a imagem mostra, para quem não consegue vê-la"
+++

Texto em Markdown.
```

A entrada que aponta para um projeto aparece automaticamente no "Registro do projeto".

### Projeto

```toml
+++
titulo = "Nome do projeto"
resumo = "O que ele faz, em uma frase."
inicio = 2026-11-14
tecnologias = ["Python", "SQL"]                    # opcional
repositorio = "https://github.com/Lucas1Silva/x"  # opcional
+++

## O problema

## Decisões
```

### Leitura

```toml
+++
titulo = "Título do livro"
autor = "Nome do autor"
status = "lido"             # lendo ou lido
lido_em = 2026-10-01        # obrigatório quando status = "lido"
tema = "Engenharia de dados"   # opcional
indico_para = "Quem trabalha com pipelines"  # opcional
+++

O que a leitura mudou no seu trabalho.
```

## Imagens

- Ficam em `static/img/`, de preferência numa subpasta por projeto.
- Formatos aceitos: `.jpg`, `.png` e `.webp`, com até 2 MB.
- Não podem ter metadados EXIF ou XMP, que podem guardar a localização de uma foto.
  Para fotos JPEG no Windows: botão direito no arquivo → Propriedades → Detalhes →
  "Remover Propriedades e Informações Pessoais" → criar uma cópia sem as propriedades.

Toda imagem da pasta é verificada, mesmo as que nenhuma página usa, porque todas são publicadas.

## O que o build verifica

O build para e lista todos os problemas de uma vez quando encontra:

- metadados faltando, com tipo errado ou com nome desconhecido (um erro de digitação, por exemplo);
- referência a um projeto, leitura ou imagem que não existe;
- imagem sem `alt`, grande demais ou com metadados;
- qualquer texto com formato de e-mail nas páginas geradas;
- link interno quebrado, link sem `https://` ou link fora do caminho base (`/pages/`).

Num link para outra página do site, escreva o caminho completo, como `/pages/projetos/`.

## Publicação

Cada push na `main` dispara a esteira (`.github/workflows/deploy.yml`): instala as
dependências, roda os testes, gera e verifica o site e só então publica. Se algo falhar,
o site no ar continua como estava.

Pull requests rodam as mesmas verificações, sem publicar.

## Dependências

As dependências diretas estão em `requirements.in`. O `requirements.txt` fixa a versão exata
e o hash de cada pacote, e a instalação recusa qualquer arquivo com hash diferente.

Para atualizar:

```bash
python -m pip install pip-tools
pip-compile --generate-hashes --strip-extras --no-emit-index-url requirements.in
```

O Dependabot abre um pull request por semana quando há versão nova de uma dependência
ou de uma action da esteira.
