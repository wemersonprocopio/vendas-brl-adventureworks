/*  AdventureWorksDW2014 — vendas convertidas para R$ (2011–2013)
    Ordem: 1) evidência  2) view_cotacaobrl  3) view_vendasbrl  4) conferência  5) limpeza */

USE AdventureWorksDW2014;
GO

/* ---------------------------------------------------------------------
   1) EVIDÊNCIA — que países existem? (Brasil não aparece)
   --------------------------------------------------------------------- */
SELECT EnglishCountryRegionName AS País, COUNT(*) AS Cidades
FROM DimGeography
GROUP BY EnglishCountryRegionName
ORDER BY Cidades DESC;

-- O que o banco tem de Brasil: a moeda e a cotação diária
SELECT * FROM DimCurrency WHERE CurrencyAlternateKey = 'BRL';
GO

/* ---------------------------------------------------------------------
   2) COTAÇÃO DO REAL POR DIA — view_cotacaobrl
   AverageRate = quantos US$ vale 1 unidade da moeda
   Logo: valor em R$ = valor em US$ / AverageRate
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW dbo.view_cotacaobrl AS
SELECT
    r.DateKey               AS ChaveData,
    r.Date                  AS Data,
    r.AverageRate           AS USD_por_BRL,
    1.0 / r.AverageRate     AS BRL_por_USD
FROM FactCurrencyRate r
JOIN DimCurrency c ON c.CurrencyKey = r.CurrencyKey
WHERE c.CurrencyAlternateKey = 'BRL';
GO

/* ---------------------------------------------------------------------
   3) VENDAS EM R$ — view_vendasbrl
      Internet + Revenda num só fato, com colunas e valores em português.
      Período: 01/01/2011 a 31/12/2013 (anos civis completos).
      Atenção: a Revenda não tem vendas em dezembro/2013 (a base termina
      em 29/11/2013); a Internet tem os 36 meses.
   --------------------------------------------------------------------- */
CREATE OR ALTER VIEW dbo.view_vendasbrl AS
WITH vendas AS (
    SELECT
        N'Internet'             AS Canal,
        f.SalesOrderNumber      AS Pedido,
        f.SalesOrderLineNumber  AS LinhaPedido,
        f.OrderDateKey          AS ChaveData,
        CAST(f.OrderDate AS date) AS DataPedido,
        f.ProductKey            AS ChaveProduto,
        f.SalesTerritoryKey     AS ChaveTerritorio,
        f.CustomerKey           AS ChaveCliente,
        CAST(NULL AS int)       AS ChaveRevenda,
        f.OrderQuantity         AS Quantidade,
        f.SalesAmount           AS Receita_USD,
        f.TotalProductCost      AS Custo_USD
    FROM FactInternetSales f
    WHERE f.OrderDate >= '2011-01-01'
      AND f.OrderDate <  '2014-01-01'
    UNION ALL
    SELECT
        N'Revenda',
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
        f.TotalProductCost
    FROM FactResellerSales f
    WHERE f.OrderDate >= '2011-01-01'
      AND f.OrderDate <  '2014-01-01'
)
SELECT
    v.Canal,
    v.Pedido,
    v.LinhaPedido,
    v.ChaveData,
    v.DataPedido,
    v.ChaveProduto,
    v.ChaveTerritorio,
    v.ChaveCliente,
    v.ChaveRevenda,
    CASE t.SalesTerritoryCountry
        WHEN 'United States'  THEN N'Estados Unidos'
        WHEN 'Canada'         THEN N'Canadá'
        WHEN 'France'         THEN N'França'
        WHEN 'Germany'        THEN N'Alemanha'
        WHEN 'Australia'      THEN N'Austrália'
        WHEN 'United Kingdom' THEN N'Reino Unido'
        ELSE t.SalesTerritoryCountry
    END                                     AS [País],
    CASE t.SalesTerritoryRegion
        WHEN 'Northwest'      THEN N'Noroeste (EUA)'
        WHEN 'Northeast'      THEN N'Nordeste (EUA)'
        WHEN 'Central'        THEN N'Central (EUA)'
        WHEN 'Southwest'      THEN N'Sudoeste (EUA)'
        WHEN 'Southeast'      THEN N'Sudeste (EUA)'
        WHEN 'Canada'         THEN N'Canadá'
        WHEN 'France'         THEN N'França'
        WHEN 'Germany'        THEN N'Alemanha'
        WHEN 'Australia'      THEN N'Austrália'
        WHEN 'United Kingdom' THEN N'Reino Unido'
        ELSE t.SalesTerritoryRegion
    END                                     AS [Região],
    CASE t.SalesTerritoryGroup
        WHEN 'North America'  THEN N'América do Norte'
        WHEN 'Europe'         THEN N'Europa'
        WHEN 'Pacific'        THEN N'Pacífico'
        ELSE t.SalesTerritoryGroup
    END                                     AS Continente,
    v.Quantidade,
    v.Receita_USD,
    v.Custo_USD,
    v.Receita_USD / c.USD_por_BRL           AS Receita_BRL,
    v.Custo_USD   / c.USD_por_BRL           AS Custo_BRL,
    c.BRL_por_USD                           AS Cotacao
FROM vendas v
JOIN dbo.view_cotacaobrl c   ON c.ChaveData = v.ChaveData
JOIN DimSalesTerritory t     ON t.SalesTerritoryKey = v.ChaveTerritorio;
GO

/* ---------------------------------------------------------------------
   4) CONFERÊNCIA — nenhuma linha do período pode se perder nos JOINs
   --------------------------------------------------------------------- */
SELECT N'Internet' AS Canal,
       (SELECT COUNT(*) FROM FactInternetSales
         WHERE OrderDate >= '2011-01-01' AND OrderDate < '2014-01-01')    AS Linhas_Fato,
       (SELECT COUNT(*) FROM dbo.view_vendasbrl WHERE Canal = N'Internet') AS Linhas_View
UNION ALL
SELECT N'Revenda',
       (SELECT COUNT(*) FROM FactResellerSales
         WHERE OrderDate >= '2011-01-01' AND OrderDate < '2014-01-01'),
       (SELECT COUNT(*) FROM dbo.view_vendasbrl WHERE Canal = N'Revenda');

-- Período da view: 01/01/2011 a 31/12/2013 (Revenda até 29/11/2013)
SELECT Canal, MIN(DataPedido) AS Primeira_Venda, MAX(DataPedido) AS Ultima_Venda
FROM dbo.view_vendasbrl
GROUP BY Canal;

-- Esperado: 118.917 linhas e receita de R$ 266.317.481,43
SELECT COUNT(*) AS Linhas, SUM(Receita_BRL) AS Receita_BRL
FROM dbo.view_vendasbrl;

-- Receita e margem por ano e canal, em R$
SELECT
    YEAR(DataPedido)                                   AS Ano,
    Canal,
    FORMAT(SUM(Receita_BRL), 'C', 'pt-BR')              AS Receita,
    FORMAT(SUM(Receita_BRL - Custo_BRL), 'C', 'pt-BR')  AS Margem,
    FORMAT(SUM(Receita_BRL - Custo_BRL) / SUM(Receita_BRL), 'P1', 'pt-BR') AS Margem_pct,
    FORMAT(SUM(Receita_BRL) / SUM(Receita_USD), 'N2', 'pt-BR')            AS Cotacao_media
FROM dbo.view_vendasbrl
GROUP BY YEAR(DataPedido), Canal
ORDER BY Ano, Canal;

-- Receita por país, em português
SELECT [País], Continente, FORMAT(SUM(Receita_BRL), 'C', 'pt-BR') AS Receita
FROM dbo.view_vendasbrl
GROUP BY [País], Continente
ORDER BY SUM(Receita_BRL) DESC;
GO
