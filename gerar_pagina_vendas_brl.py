"""Gera a página PBIR "Vendas em R$" no projeto vw_VendasBRL.pbip.

Uso (com o Power BI Desktop FECHADO):
    python gerar_pagina_vendas_brl.py "<pasta>\\vw_VendasBRL.Report"

Faz backup de pages.json antes de alterar. Rodar de novo recria a página.
Estilo igual ao 2_analise_vendas: fundo #F3F5F6, título em faixa #1B2327, destaque #008080.
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

PAGE_ID = "b7e1c4a9d2f60358e1a7"
PAGE_NAME = "Vendas em R$"

ESCURO, TEAL, CLARO, BORDA = "#1B2327", "#008080", "#F3F5F6", "#D5DDE0"
FATO = "vw_VendasBRL"

SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"


# ---------- helpers de expressão ----------
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def cor(hex_):
    return {"solid": {"color": lit(f"'{hex_}'")}}


def cor_medida(medida, tabela=FATO):
    return {"solid": {"color": {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": medida}}}}}


def medida(nome, tabela=FATO):
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}},
        "queryRef": f"{tabela}.{nome}",
        "nativeQueryRef": nome,
    }


def coluna(tabela, nome, active=False):
    p = {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}},
        "queryRef": f"{tabela}.{nome}",
        "nativeQueryRef": nome,
    }
    if active:
        p["active"] = True
    return p


def ordem(proj, direcao):
    return {"sort": [{"field": proj["field"], "direction": direcao}]}


def container(titulo, borda=False):
    """Fundo branco, cantos 8, título na faixa escura (padrão 2_analise_vendas)."""
    obj = {
        "background": [{"properties": {"show": lit("true"), "color": cor("#FFFFFF"), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true" if borda else "false"), "color": cor(BORDA), "radius": lit("8D")}}],
        "subTitle": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"top": lit("4D"), "bottom": lit("6D"), "left": lit("8D"), "right": lit("8D")}}],
    }
    if titulo:
        obj["title"] = [{"properties": {
            "show": lit("true"), "text": lit(f"'{titulo}'"), "fontColor": cor("#FFFFFF"),
            "background": cor(ESCURO), "bold": lit("true"), "fontSize": lit("13D"),
            "alignment": lit("'left'"), "titleWrap": lit("false"), "fontFamily": lit("'Segoe UI Semibold'"),
        }}]
    else:
        obj["title"] = [{"properties": {"show": lit("false")}}]
    return obj


# ---------- montagem dos visuais ----------
visuais = []


def add(tipo, x, y, w, h, visual):
    nome = hashlib.md5(f"{PAGE_ID}-{len(visuais)}-{tipo}".encode()).hexdigest()[:20]
    z = len(visuais) * 1000
    visual = {"visualType": tipo, **visual, "drillFilterOtherVisuals": True}
    visuais.append({
        "$schema": SCHEMA_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": visual,
    })


# Título
add("textbox", 16, 12, 1888, 64, {
    "objects": {"general": [{"properties": {"paragraphs": [{
        "textRuns": [{"value": "VENDAS EM R$ · ADVENTURE WORKS (INTERNET + REVENDA)",
                      "textStyle": {"fontWeight": "bold", "fontFamily": "Segoe UI", "fontSize": "24pt", "color": "#ffffff"}}],
        "horizontalTextAlignment": "center"}]}}]},
    "visualContainerObjects": {
        "background": [{"properties": {"show": lit("true"), "color": cor(ESCURO), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": cor(TEAL), "radius": lit("8D")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"top": lit("8D")}}],
    },
})

# Segmentações
for x, (tab, col, titulo) in zip((16, 651, 1286), (
        ("DimDate", "CalendarYear", "Ano"),
        (FATO, "Canal", "Canal"),
        ("DimSalesTerritory", "SalesTerritoryCountry", "País"))):
    add("slicer", x, 88, 618, 84, {
        "query": {"queryState": {"Values": {"projections": [coluna(tab, col, active=True)]}}},
        "objects": {
            "data": [{"properties": {"mode": lit("'Basic'")}}],
            "header": [{"properties": {"show": lit("false")}}],
            "items": [{"properties": {"fontColor": cor(ESCURO)}}],
            "general": [{"properties": {"orientation": lit("1D")}}],
        },
        "visualContainerObjects": container(titulo, borda=True),
    })

# Cartões de KPI
cards = [
    ("Receita R$", "Receita", None),
    ("Margem R$", "Margem", None),
    ("Margem %", "Margem %", "Cor Margem"),
    ("Txt Crescimento", "Crescimento a.a.", "Cor Crescimento"),
    ("Pedidos", "Pedidos", None),
    ("Ticket Médio R$", "Ticket Médio", None),
]
for i, (m, titulo, cor_m) in enumerate(cards):
    x = (16, 333, 651, 968, 1286, 1603)[i]
    add("card", x, 184, 301, 106, {
        "query": {"queryState": {"Values": {"projections": [medida(m)]}}},
        "objects": {
            "labels": [{"properties": {
                "color": cor_medida(cor_m) if cor_m else cor(ESCURO),
                "fontSize": lit("26D"), "labelDisplayUnits": lit("0D"),
                "fontFamily": lit("'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"),
            }}],
            "categoryLabels": [{"properties": {"show": lit("false")}}],
        },
        "visualContainerObjects": container(titulo),
    })

# Receita (colunas) x Margem % (linha) por mês
mes = coluna("DimDate", "Mês Ano", active=True)
add("lineClusteredColumnComboChart", 16, 306, 1180, 372, {
    "query": {
        "queryState": {
            "Category": {"projections": [mes]},
            "Y": {"projections": [medida("Receita R$")]},
            "Y2": {"projections": [medida("Margem %")]},
        },
        "sortDefinition": ordem(mes, "Ascending"),
    },
    "objects": {
        "dataPoint": [
            {"properties": {"fill": cor(TEAL)}, "selector": {"metadata": f"{FATO}.Receita R$"}},
            {"properties": {"fill": cor(ESCURO)}, "selector": {"metadata": f"{FATO}.Margem %"}},
        ],
        "lineStyles": [{"properties": {"strokeWidth": lit("3D"), "showMarker": lit("true")}}],
        "valueAxis": [{"properties": {"gridlineShow": lit("false"), "secShow": lit("true")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
        "legend": [{"properties": {"show": lit("true"), "position": lit("'TopRight'")}}],
        "labels": [{"properties": {"show": lit("false")}}],
    },
    "visualContainerObjects": container("Receita e margem % por mês"),
})

# Receita por país
rec = medida("Receita R$")
add("barChart", 1212, 306, 692, 372, {
    "query": {
        "queryState": {
            "Category": {"projections": [coluna("DimSalesTerritory", "SalesTerritoryCountry", active=True)]},
            "Y": {"projections": [rec]},
            "Tooltips": {"projections": [medida("Margem %"), medida("Pedidos")]},
        },
        "sortDefinition": ordem(rec, "Descending"),
    },
    "objects": {
        "dataPoint": [{"properties": {"fill": cor(TEAL)}}],
        "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "fontSize": lit("10D")}}],
        "labels": [{"properties": {"show": lit("true"), "fontSize": lit("9D"), "labelDisplayUnits": lit("0D")}}],
    },
    "visualContainerObjects": container("Receita por país"),
})

# Tabela ano x canal
ano = coluna("DimDate", "CalendarYear")
add("tableEx", 16, 694, 1180, 370, {
    "query": {
        "queryState": {"Values": {"projections": [
            ano, coluna(FATO, "Canal"),
            medida("Receita R$"), medida("Receita R$ Ano Anterior"), medida("Crescimento % a.a."),
            medida("Margem %"), medida("Pedidos"), medida("Ticket Médio R$"),
        ]}},
        "sortDefinition": ordem(ano, "Ascending"),
    },
    "objects": {
        "columnHeaders": [{"properties": {"fontColor": cor(ESCURO), "backColor": cor("#E3F1F1"), "bold": lit("true"),
                                          "fontSize": lit("11D"), "wordWrap": lit("true")}}],
        "values": [{"properties": {"fontSize": lit("11D"), "fontColorPrimary": cor(ESCURO),
                                   "backColorPrimary": cor("#FFFFFF"), "backColorSecondary": cor("#F6FAFA")}}],
        "total": [{"properties": {"totals": lit("true"), "fontColor": cor("#FFFFFF"), "backColor": cor(TEAL),
                                  "bold": lit("true"), "fontSize": lit("11D")}}],
        "grid": [{"properties": {"rowPadding": lit("6D"), "gridVertical": lit("false")}}],
    },
    "visualContainerObjects": container("Resumo por ano e canal"),
})

# Cotação média por mês
mes2 = coluna("DimDate", "Mês Ano", active=True)
add("lineChart", 1212, 694, 692, 370, {
    "query": {
        "queryState": {
            "Category": {"projections": [mes2]},
            "Y": {"projections": [medida("Cotação Média")]},
        },
        "sortDefinition": ordem(mes2, "Ascending"),
    },
    "objects": {
        "dataPoint": [{"properties": {"fill": cor(TEAL)}}],
        "lineStyles": [{"properties": {"strokeWidth": lit("3D")}}],
        "valueAxis": [{"properties": {"gridlineShow": lit("false"), "showAxisTitle": lit("false")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
        "labels": [{"properties": {"show": lit("false")}}],
    },
    "visualContainerObjects": container("Cotação média BRL/USD (R$ por US$)"),
})


# ---------- gravação ----------
def gravar(report_dir: Path):
    pages = report_dir / "definition" / "pages"
    pages_json = pages / "pages.json"
    if not pages_json.exists():
        sys.exit(f"Não achei {pages_json}")

    backup = report_dir.parent / f"_backup_{datetime.now():%Y-%m-%d_%H%M%S}"
    shutil.copytree(report_dir, backup / report_dir.name)

    destino = pages / PAGE_ID
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "visuals").mkdir(parents=True)

    page = {
        "$schema": SCHEMA_PAGE, "name": PAGE_ID, "displayName": PAGE_NAME,
        "displayOption": "FitToPage", "height": 1080, "width": 1920,
        "objects": {k: [{"properties": {"color": cor(CLARO), "transparency": lit("0D")}}]
                    for k in ("background", "outspace")},
    }
    (destino / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
    for v in visuais:
        d = destino / "visuals" / v["name"]
        d.mkdir()
        (d / "visual.json").write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = json.loads(pages_json.read_text(encoding="utf-8"))
    meta["pageOrder"] = [PAGE_ID] + [p for p in meta["pageOrder"] if p != PAGE_ID]
    meta["activePageName"] = PAGE_ID
    pages_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Página '{PAGE_NAME}' gravada com {len(visuais)} visuais em {destino}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    gravar(Path(sys.argv[1]))
