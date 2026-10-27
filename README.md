# Vendas AdventureWorks em R$ (2011–2013)

Análise das vendas da AdventureWorks convertidas para reais pela cotação do dia de cada pedido, do SQL Server ao Power BI, com todos os números validados contra o banco.

![Dashboard Vendas em R$](docs/dashboard.png)
*Página "Vendas em R$" filtrada em 2013.*

## Problema

A base AdventureWorksDW2014 registra as vendas em dólar. A pergunta foi: **como seria a leitura desse negócio para um gestor no Brasil, em R$?** Converter com uma taxa fixa esconde o efeito do câmbio, então cada venda foi convertida pela cotação BRL do dia em que o pedido foi feito.

## Fluxo

```
dados brutos → limpeza → transformação → análise → indicadores → visualização → validação → interpretação
```

| Etapa | O que foi feito |
|---|---|
| Dados brutos | `FactInternetSales`, `FactResellerSales` e a cotação diária `FactCurrencyRate` |
| Transformação (SQL) | Views `vw_CotacaoBRL` e `vw_VendasBRL`: os dois canais numa base só, já em R$ |
| Limpeza (Power Query) | Só anos com venda nos 12 meses; só territórios com venda |
| Modelo (Power BI) | Fato `vw_VendasBRL` ligado a data, produto, cliente, revenda e território |
| Indicadores (DAX) | 14 medidas: base, inteligência de tempo e textos/cores para formatação condicional |
| Visualização | Página "Vendas em R$": cartões, receita × margem por mês, receita por país, tabela ano/canal e evolução da cotação |
| Validação | Cada número do dashboard conferido com uma consulta SQL independente, até o centavo |

## Decisões e regras de negócio

- **Conversão pela cotação do dia do pedido.** Na `FactCurrencyRate`, `AverageRate` é quantos dólares vale 1 real; por isso `R$ = USD / AverageRate`.
- **Recorte 2011–2013.** A base tem 2010 com poucos dias de venda e 2014 só com janeiro. A consulta `AnosAnalise` (Power Query) mantém apenas anos com venda nos 12 meses, então o recorte vem dos dados e não de uma lista fixa.
- **Crescimento só entre anos inteiros.** O `Crescimento % a.a.` fica em branco quando o período atual ou o do ano anterior não está completo na base (por isso 2011 aparece como "s/ comparação").
- **Territórios sem venda saem do filtro de país** (ex.: o território "NA" da dimensão).
- **Cotação média ponderada pela receita**: `Receita R$ / Receita USD`, e não a média simples das cotações.

## Indicadores

| Pasta | Medidas |
|---|---|
| 1 Base | Receita R$, Custo R$, Margem R$, Margem %, Qtd Vendida, Pedidos, Ticket Médio R$, Cotação Média |
| 2 Tempo | Receita R$ YTD, Receita R$ Ano Anterior, Crescimento % a.a. |
| 3 Textos e Cores | Txt Crescimento, Cor Crescimento, Cor Margem |

## Resultados (2011–2013)

| Indicador | Valor |
|---|---|
| Receita | R$ 266.317.481,43 |
| Margem | R$ 31.398.923,67 (11,8%) |
| Pedidos | 30.532 |
| Ticket médio | R$ 8.722,57 |
| Quantidade vendida | 271.972 |
| Cotação média (BRL/USD) | 2,44 |
| Crescimento da receita | +71,7% em 2012 · +78,6% em 2013 |

Validação: 118.917 linhas; receita, margem, pedidos e ticket batem com o SQL no total, por ano/canal e por país.

## Principais achados

1. **Cerca de metade do crescimento em R$ veio do câmbio.** Em dólar, a receita cresceu cerca de +35% em 2012 e +47% em 2013; em reais, +72% e +79%. Quem olha só o número em R$ superestima o desempenho comercial.
2. **A margem da Revenda fica perto de zero e chega a ser negativa.** O lucro vem quase todo do canal Internet. Isso está na origem dos dados, não é efeito da conversão.
3. **O ticket da Internet caiu em 2013**, sinal de mudança no mix de produtos vendidos.

### Próximas perguntas

- Por que a margem da Revenda ficou negativa em 2013? (olhar por produto e por promoção, `DimPromotion`)
- Que categorias de produto explicam a queda do ticket na Internet em 2013?

## Estrutura do repositório

```
vw_CotacaoBRL_VendasBRL.sql     views no SQL Server + consultas de exploração e conferência
vw_VendasBRL.pbip               projeto do Power BI (abrir este arquivo)
vw_VendasBRL.SemanticModel/     modelo em TMDL: tabelas, relacionamentos, medidas DAX, Power Query
vw_VendasBRL.Report/            página do relatório em PBIR (JSON)
gerar_pagina_vendas_brl.py      script que gera a página "Vendas em R$" (visuais em JSON)
```

## Como reproduzir

1. Restaure o banco **AdventureWorksDW2014** num SQL Server.
2. Rode `vw_CotacaoBRL_VendasBRL.sql` para criar as views `dbo.vw_CotacaoBRL` e `dbo.vw_VendasBRL`.
3. Abra `vw_VendasBRL.pbip` no Power BI Desktop.
4. As consultas apontam para o SQL Server local do autor. Troque pelo nome do seu servidor em **Transformar dados → Configurações da fonte de dados** e atualize.

## Ferramentas

SQL Server (T-SQL, views) · Power BI Desktop (Power Query M, DAX, formato PBIP/TMDL/PBIR) · Python · IA (Claude) como apoio na construção e na validação
