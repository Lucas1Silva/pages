+++
titulo = "Site pessoal"
resumo = "Um gerador estático em Python que transforma arquivos Markdown nas páginas deste site."
inicio = 2026-11-14
tecnologias = ["Python", "Jinja2", "Markdown", "GitHub Actions"]
repositorio = "https://github.com/Lucas1Silva/pages"
+++

## O problema

Quem chega do LinkedIn já viu meu nome, foto e cargo. Faltava um lugar para mostrar o trabalho em si e o histórico de cada projeto.

## Decisões

- Gerador próprio em Python em vez de Jekyll, Hugo ou Astro: o site é simples e eu consigo explicar cada linha.
- Metadados em TOML, lidos pela biblioteca padrão do Python.
- Imagens ficam no repositório; os vídeos ficam no LinkedIn.
- A esteira é o portão de segurança: se uma verificação falhar, nada é publicado.
- O build recusa e-mails nas páginas e imagens com metadados, como localização.
