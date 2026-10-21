# Automação de Conciliação Bancária com Python

Aplicação local para apoiar rotinas de conciliação em operações financeiras, BPOs e escritórios contábeis. O sistema compara lançamentos de um extrato bancário com um relatório financeiro, destaca correspondências e organiza divergências para revisão.

## Objetivo

Reduzir o trabalho repetitivo de comparar registros linha a linha e ajudar a equipe a direcionar sua atenção para diferenças, lançamentos ausentes e dados inválidos. A ferramenta apoia a análise; a validação e a decisão contábil continuam sob responsabilidade do profissional.

## Funcionalidades disponíveis

- Importação de arquivos CSV e Excel `.xlsx` pela interface Streamlit.
- Seleção das colunas de data, valor e histórico para cada arquivo.
- Tratamento de datas e valores monetários, inclusive no padrão brasileiro, como `1.234,56`.
- Leitura de valores em colunas separadas de débito e crédito, calculados como crédito menos débito.
- Comparação de lançamentos por valor e proximidade de data, com tolerâncias configuráveis.
- Identificação de itens conciliados, presentes apenas em um dos arquivos ou com dados inválidos.
- Visualização dos resultados na página e exportação integral para CSV ou Excel.
- Arquivos de demonstração em `dados_entrada/` para experimentar sem enviar dados próprios.

## Tecnologias

- Python
- Pandas
- Streamlit
- openpyxl, para exportação em Excel
- Decimal, para representar valores monetários com precisão decimal

## Como executar no Windows

No terminal, dentro da pasta do projeto:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run codigo.py
```

Se `py` não estiver disponível, use o executável Python instalado para criar o ambiente virtual. O Streamlit exibirá um endereço local para abrir a aplicação no navegador.

## Como usar

1. Escolha **Usar demonstração** ou **Enviar arquivos** na configuração lateral.
2. Envie o extrato bancário e o relatório financeiro em CSV ou Excel `.xlsx`.
3. Para cada arquivo, selecione as colunas de data e valor e, se houver, a coluna de histórico.
4. Se os valores estiverem em colunas separadas, habilite a opção de débito e crédito e selecione ambas as colunas.
5. Defina as tolerâncias de data e valor e clique em **Conciliar**.
6. Revise os status e baixe o resultado em CSV ou Excel.

## Como funciona a comparação

O sistema procura correspondências no relatório financeiro dentro das tolerâncias informadas e busca maximizar a quantidade de lançamentos conciliados. Para escolher entre opções, considera primeiro a menor diferença de valor e depois a menor diferença de data. Cada lançamento financeiro é usado no máximo uma vez.

Débitos são tratados como saídas negativas e créditos como entradas positivas quando as colunas são separadas. Para que a comparação seja coerente, os arquivos devem seguir a mesma convenção de sinais. Linhas com data ou valor inválido são preservadas e sinalizadas para revisão.

## Limites atuais

- A entrada aceita CSV e Excel `.xlsx`; arquivos OFX e PDF não são importados diretamente.
- A exportação gera o resultado da conciliação em CSV ou Excel, não um layout específico de ERP.
- A aplicação não cria ou corrige lançamentos e não substitui revisão profissional ou validação contábil.
- Os exemplos em `dados_entrada/` são fictícios. Avalie a confidencialidade antes de processar dados reais em qualquer ambiente compartilhado.

## Estrutura do projeto

- `codigo.py`: interface Streamlit, importação e exportação.
- `conciliacao.py`: preparação dos dados e lógica de comparação.
- `test_conciliacao.py`: testes automatizados da lógica de conciliação.
- `dados_entrada/`: arquivos fictícios para demonstração.

## Impacto esperado

Ao automatizar a organização inicial dos registros, a equipe pode reduzir o tempo dedicado à conferência manual e concentrar a análise nas exceções. O ganho depende da qualidade e da padronização dos arquivos de entrada; resultados conciliados devem ser revisados conforme os procedimentos da operação.