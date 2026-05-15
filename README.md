# 🏝️ Férias Smart: Otimizador de Calendário

O **Férias Smart** é uma ferramenta interativa desenvolvida em Python com Streamlit, projetada para ajudar trabalhadores a extraírem o máximo proveito dos seus dias de descanso. O algoritmo calcula as melhores combinações de datas para marcar férias, conectando os períodos escolhidos com feriados e fins de semana para criar "janelas reais" de descanso muito maiores que o período descontado no RH.

## 🚀 Funcionalidades

- **Cálculo de Eficiência:** Identifica quantas datas de descanso real ganhas para cada dia de férias utilizado.
- **Modos de Divisão:** - **Manual:** Tu defines exatamente os tamanhos dos lotes (ex: 15+15, 10+20).
  - **Automático:** O sistema testa todas as partições possíveis de dias para encontrar a mais eficiente.
- **Feriados Inteligentes:** - Base de feriados nacionais brasileiros (fixos e móveis como Carnaval e Corpus Christi).
  - Possibilidade de ativar/desativar feriados específicos.
  - Adição de feriados customizados (municipais ou pontes da empresa).
- **Filtros Avançados:** - Restrição de dias da semana para início das férias (ex: só começar à segunda-feira).
  - Filtro por meses específicos.
  - Customização da jornada de trabalho (quais os dias em que folgas normalmente).
- **Interface Intuitiva:** Ordenação por eficiência, total de dias ganhos ou ordem cronológica.

## 🛠️ Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/) (Interface Web)
- [Pandas](https://pandas.pydata.org/) (Manipulação de dados)
- [Itertools](https://docs.python.org/3/library/itertools.html) (Algoritmos de permutação e combinação)

## 📦 Como Instalar e Executar

1. **Clona o repositório:**
   ```bash
   git clone [https://github.com/teu-usuario/ferias-smart.git](https://github.com/teu-usuario/ferias-smart.git)
   cd ferias-smart

2. **Cria um ambiente virtual (opcional mas recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    # No Linux/Mac:
    source venv/bin/activate

3. **Instala as dependências:**
    ```bash
    pip install streamlit pandas

4. **Executa a aplicação:**
   ```bash
    streamlit run app.py

## 📂 Estrutura de Ficheiros

- `app.py`: Código principal da aplicação Streamlit.
- `data/feriados.csv`: (Opcional) Ficheiro CSV para carregar feriados personalizados de forma persistente.
- `README.md`: Documentação do projeto.

## 💡 Como usar

1. No menu lateral, insere o **total de dias** que tens direito (ex: 30).
2. Escolhe se queres que o sistema decida como dividir esses dias ou se preferes definir os lotes.
3. Configura o teu **período de interesse** (Início e Fim).
4. Seleciona os dias da semana em que trabalhas para que o sistema ignore as tuas folgas fixas no cálculo de "dias gastos".
5. Clica em **🚀 Calcular Possibilidades**.
6. Usa os filtros de ordenação para encontrar a opção que oferece a maior "Janela Real" de descanso.

---
Desenvolvido para transformar 30 dias de férias em muito mais! 🏖️
