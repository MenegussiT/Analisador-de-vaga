# 🤖 AI Job Hunter Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.0-orange)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blueviolet)
![Status](https://img.shields.io/badge/Status-Functional-green)

> Um assistente de carreira inteligente que analisa currículos com IA Generativa, traça perfis profissionais e automatiza a busca de vagas em múltiplas plataformas (LinkedIn, RioVagas) com lógica de deduplicação e inteligência regional.

---

## 🚀 Sobre o Projeto

Este projeto nasceu da necessidade de otimizar a busca por empregos. Em vez de preencher filtros manuais repetidamente, o usuário envia seu currículo (PDF) para o bot. O sistema utiliza a API do **Google Gemini** para ler e interpretar a senioridade e o cargo ideal do candidato, salvando um perfil persistente.

A partir daí, o bot atua como um agregador inteligente de vagas, varrendo diferentes fontes da web, filtrando resultados de baixa qualidade e garantindo que o usuário nunca receba a mesma vaga duas vezes.

### ✨ Principais Funcionalidades

* **📄 Análise de Currículo com IA:** Extração automática de texto de PDFs e análise semântica via **Google Gemini 1.5/2.0 Flash** para determinar Cargo, Nível (Jr/Pl/Sr) e Habilidades.
* **💾 Persistência de Dados (SQLite):** Sistema de "Memória de Usuário". O bot reconhece usuários recorrentes, evitando novos cadastros.
* **🧠 Scraper Híbrido & Inteligente:**
    * **Multifonte:** Busca no LinkedIn (Global) e RioVagas (Regional).
    * **Lógica Regional:** Ativa crawlers específicos baseados na geolocalização do usuário (ex: só busca no RioVagas se o usuário estiver no RJ).
    * **Interleaving (Zip Longest):** Algoritmo que mistura resultados de diferentes fontes para garantir variedade na visualização.
    * **Filtro de Qualidade:** Remoção automática de vagas "ofuscadas" ou protegidas por anti-bots (ex: `***`).
* **🚫 Sistema Anti-Duplicidade:** Controle histórico via banco de dados (`UNIQUE constraints`) para impedir o reenvio de vagas já visualizadas.

---

## 🛠️ Arquitetura e Tecnologias

O projeto segue uma arquitetura modular para facilitar a manutenção e escalabilidade.

* **Linguagem:** Python 3.12+
* **IA / LLM:** Google GenAI SDK (Gemini 1.5 Flash)
* **Interface:** `python-telegram-bot` (Async ConversationHandler)
* **Web Scraping:** `BeautifulSoup4` e `Requests`
* **Banco de Dados:** SQLite3 (Nativo)

### 📂 Estrutura de Pastas

```text
📁 Analisador-de-Vaga/
│
├── 📂 core/
│   ├── cv_analyzer.py      # Integração com Gemini API
│   ├── job_scraper.py      # Lógica de scraping, filtros e interleaving
│   └── pdf_parser.py       # Extração de texto de arquivos PDF
│
├── 📂 profiles/
│   └── profile_manager.py  # CRUD do SQLite e controle de histórico de vagas
│
├── 📂 telegram_bot/
│   ├── bot.py              # Configuração do Application e Handlers
│   └── handlers.py         # Lógica de fluxo de conversa e UX
│
├── main.py                 # Ponto de entrada da aplicação
├── config.py               # Gerenciamento de variáveis de ambiente
├── .env                    # Chaves de API (não versionado)
└── requirements.txt        # Dependências do projeto
