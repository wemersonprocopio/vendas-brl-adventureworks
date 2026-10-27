


 /*  AdventureWorksDW2014 — recorte para análise no Brasil (R$)
   Ordem: 1) evidência  2) cotação BRL  3) vendas em R$  4) conferência */

USE AdventureWorksDW2014;
GO

/* ---------------------------------------------------------------------
   1) EVIDÊNCIA — que países existem? (Brasil não aparece)
   --------------------------------------------------------------------- */
SELECT EnglishCountryRegionName AS Pais, COUNT(*) AS Cidades
FROM DimGeography
GROUP BY EnglishCountryRegionName
ORDER BY Cidades DESC;

-- O que o banco tem de Brasil: a moeda e a cotação diária
SELECT * FROM DimCurrency WHERE CurrencyAlternateKey = 'BRL';
GO

/* ---------------------------------------------------------------------
   2) COTAÇÃO BRL por dia
   AverageRate = quantos USD vale 1 unidade da moeda (JPY ≈ 0,008; GBP ≈ 1,48)
   Logo: valor em R$ = valor em USD / AverageRate
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW dbo.vw_CotacaoBRL AS
SELECT
    r.DateKey,
    r.Date                      AS Data,
    r.AverageRate               AS USD_por_BRL,
    1.0 / r.AverageRate         AS BRL_por_USD
FROM FactCurrencyRate r
JOIN DimCurrency c ON c.CurrencyKey = r.CurrencyKey
WHERE c.CurrencyAlternateKey = 'BRL';
GO

/* ---------------------------------------------------------------------
   3) VENDAS EM R$ — Internet + Revenda num só fato, com rótulos em PT
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW dbo.vw_VendasBRL AS
SELECT
    'Internet'                      AS Canal,
    f.SalesOrderNumber              AS Pedido,
    f.SalesOrderLineNumber          AS LinhaPedido,
    f.OrderDateKey,
    CAST(f.OrderDate AS date)       AS DataPedido,
    f.ProductKey,
    f.SalesTerritoryKey,
    f.CustomerKey,
    CAST(NULL AS int)               AS ResellerKey,
    f.OrderQuantity                 AS Quantidade,
    f.SalesAmount                   AS Receita_USD,
    f.TotalProductCost              AS Custo_USD,
    f.SalesAmount      / cb.USD_por_BRL AS Receita_BRL,
    f.TotalProductCost / cb.USD_por_BRL AS Custo_BRL,
    cb.BRL_por_USD                  AS Cotacao
FROM FactInternetSales f
JOIN dbo.vw_CotacaoBRL cb ON cb.DateKey = f.OrderDateKey
UNION ALL
SELECT
    'Revenda',
    f.SalesOrderNumber,
    f.SalesOrderLineNumber,
    f.OrderDateKey,
    CAST(f.OrderDate AS date),
    f.ProductKey,
    f.SalesTerritoryKey,
    CAST(NULL AS int),
    f.ResellerKey,
    f.OrderQuantity,
    f.SalesAmount,
    f.TotalProductCost,
    f.SalesAmount      / cb.USD_por_BRL,
    f.TotalProductCost / cb.USD_por_BRL,
    cb.BRL_por_USD
FROM FactResellerSales f
JOIN dbo.vw_CotacaoBRL cb ON cb.DateKey = f.OrderDateKey;
GO

/* ---------------------------------------------------------------------
   4) CONFERÊNCIA — nenhuma linha pode se perder no JOIN com a cotação
   --------------------------------------------------------------------- */
SELECT 'Internet' AS Canal,
       (SELECT COUNT(*) FROM FactInternetSales)                          AS Linhas_Fato,
       (SELECT COUNT(*) FROM dbo.vw_VendasBRL WHERE Canal = 'Internet')  AS Linhas_View
UNION ALL
SELECT 'Revenda',
       (SELECT COUNT(*) FROM FactResellerSales),
       (SELECT COUNT(*) FROM dbo.vw_VendasBRL WHERE Canal = 'Revenda');

-- Receita e margem por ano e canal, em R$
SELECT
    YEAR(DataPedido)                               AS Ano,
    Canal,
    FORMAT(SUM(Receita_BRL), 'C', 'pt-BR')          AS Receita,
    FORMAT(SUM(Receita_BRL - Custo_BRL), 'C', 'pt-BR') AS Margem,
    FORMAT(SUM(Receita_BRL - Custo_BRL) / SUM(Receita_BRL), 'P1', 'pt-BR') AS Margem_pct,
    FORMAT(AVG(Cotacao), 'N2', 'pt-BR')             AS Cotacao_media
FROM dbo.vw_VendasBRL
GROUP BY YEAR(DataPedido), Canal
ORDER BY Ano, Canal;
 


