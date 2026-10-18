"""Professional Plotly charts for the BCDS dashboard."""

import math

import plotly.graph_objects as go

from config import BANK_COLORS, DIGITAL_CODES, GROUP_ORDER
from ui_components import number


# ---------------------------------------------------------------------
# Report palette
# ---------------------------------------------------------------------

CHART_TEXT = "#17305F"
CHART_MUTED = "#6C83A7"
CHART_GRID = "#E3EDF7"
CHART_AXIS = "#D4E2F0"
CHART_BLUE = "#2563EB"
CHART_BLUE_2 = "#3B82F6"
CHART_SKY = "#38BDF8"
CHART_LIGHT = "#EAF3FF"
CHART_HOVER = "#FFFFFF"

HEATMAP_SCALE = [
    [0.00, "#F8D7DA"],   # soft coral
    [0.18, "#FCE3C3"],   # peach
    [0.36, "#FFF3C4"],   # warm cream
    [0.55, "#DDF2D1"],   # soft lime
    [0.72, "#BFE8DC"],   # mint
    [0.88, "#A9D7F5"],   # sky
    [1.00, "#B9A7E8"],   # lavender
]


def apply_report_theme(figure, height=350):
    """Shared light-blue report theme."""
    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(
            family="Segoe UI Variable Text, Segoe UI, system-ui, sans-serif",
            size=11,
            color=CHART_TEXT,
        ),
        margin=dict(
            l=16,
            r=24,
            t=28,
            b=28,
        ),
        hoverlabel=dict(
            bgcolor=CHART_HOVER,
            bordercolor=CHART_AXIS,
            font=dict(
                color=CHART_TEXT,
                size=11,
            ),
        ),
        legend=dict(
            orientation="h",
            x=0,
            y=1.08,
            yanchor="bottom",
            title=None,
            font=dict(
                size=10,
                color=CHART_TEXT,
            ),
        ),
    )

    figure.update_xaxes(
        showline=False,
        zeroline=False,
        showgrid=True,
        gridcolor=CHART_GRID,
        linecolor=CHART_AXIS,
        tickfont=dict(
            color=CHART_MUTED,
            size=10,
        ),
        title_font=dict(
            color=CHART_TEXT,
            size=11,
        ),
        fixedrange=True,
        automargin=True,
    )

    figure.update_yaxes(
        showline=False,
        zeroline=False,
        showgrid=True,
        gridcolor=CHART_GRID,
        linecolor=CHART_AXIS,
        tickfont=dict(
            color=CHART_MUTED,
            size=10,
        ),
        title_font=dict(
            color=CHART_TEXT,
            size=11,
        ),
        fixedrange=True,
        automargin=True,
    )

    return figure


style = apply_report_theme


# ---------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------

def ranking_bar(
    ranking,
    height=320,
    *,
    overview=False,
):
    """Horizontal ranking bars; bank colors are kept for identification."""
    data = ranking.sort_values(
        "rank",
        kind="stable",
    )

    figure = go.Figure(
        go.Bar(
            x=data.total_score,
            y=data.ticker,
            orientation="h",
            width=0.46,
            marker_color=[
                BANK_COLORS.get(
                    ticker,
                    CHART_BLUE,
                )
                for ticker in data.ticker
            ],
            marker_line=dict(
                color="rgba(255,255,255,.82)",
                width=1,
            ),
            text=[
                number(value)
                for value in data.total_score
            ],
            textposition="outside",
            cliponaxis=False,
            customdata=data[
                [
                    "bank",
                    "rank",
                ]
            ],
            hovertemplate=(
                "%{customdata[0]} (%{y})"
                "<br>Hạng: %{customdata[1]}"
                "<br>Tổng điểm: %{x:.2f} / 100"
                "<extra></extra>"
            ),
        )
    )

    style(
        figure,
        height,
    )

    figure.update_layout(
        showlegend=False,
        margin=dict(
            l=0 if overview else 14,
            r=38,
            t=8 if overview else 18,
            b=26,
        ),
    )

    figure.update_xaxes(
        range=[
            0,
            104,
        ],
        tickvals=[
            0,
            20,
            40,
            60,
            80,
            100,
        ],
    )

    figure.update_yaxes(
        autorange="reversed",
        showgrid=False,
    )

    return figure


def logo_ranking_bar(
    ranking,
    height=254,
    *,
    overview=False,
):
    figure = ranking_bar(
        ranking,
        height,
        overview=overview,
    )

    figure.update_layout(
        margin=dict(
            l=34,
            r=32,
            t=10,
            b=34,
        )
    )

    figure.update_yaxes(
        autorange=False,
        range=[
            len(figure.data[0].y) - 0.5,
            -0.5,
        ],
    )

    return figure


def comparison_ranking_bar(
    ranking,
    height=254,
):
    return logo_ranking_bar(
        ranking,
        height,
    )


# ---------------------------------------------------------------------
# 4-group heatmap
# ---------------------------------------------------------------------

def _ordered_groups(groups):
    available = set(
        groups.group.astype(str)
    )

    ordered = [
        code
        for code in GROUP_ORDER
        if code in available
    ]

    ordered += [
        code
        for code in groups.group.astype(str).unique()
        if code not in ordered
    ]

    return ordered


def group_comparison(
    groups,
    tickers,
):
    """
    Heatmap of the four group scores across selected banks.

    This replaces the dense 20-column chart with a compact comparison grid.
    """
    codes = _ordered_groups(
        groups
    )

    labels = (
        groups
        .drop_duplicates("group")
        .set_index("group")
        .group_label
        .to_dict()
    )

    short_labels = {
        "credit": "Chất lượng tín dụng",
        "capital": "Vốn & nguồn vốn",
        "profitability": "Sinh lời & hiệu quả",
        "digital": "Chuyển đổi số",
    }

    z = []

    for code in codes:
        row = []

        for ticker in tickers:
            match = groups.loc[
                groups.ticker.eq(ticker)
                & groups.group.eq(code),
                "group_score_100",
            ]

            row.append(
                float(match.iloc[0])
                if not match.empty
                else None
            )

        z.append(
            row
        )

    y_labels = [
        short_labels.get(
            code,
            labels.get(
                code,
                code,
            ),
        )
        for code in codes
    ]

    text_matrix = [
        [
            ""
            if value is None
            or not math.isfinite(value)
            else f"{value:.2f}"
            for value in row
        ]
        for row in z
    ]

    figure = go.Figure(
        go.Heatmap(
            z=z,
            x=tickers,
            y=y_labels,
            zmin=0,
            zmax=100,
            colorscale=HEATMAP_SCALE,
            xgap=5,
            ygap=5,
            text=text_matrix,
            texttemplate="%{text}",
            textfont=dict(
                size=11,
                color="#17305F",
            ),
            colorbar=dict(
                title=dict(
                    text="Điểm",
                    font=dict(
                        size=10,
                        color=CHART_TEXT,
                    ),
                ),
                thickness=10,
                len=0.78,
                tickvals=[
                    0,
                    25,
                    50,
                    75,
                    100,
                ],
                outlinewidth=0,
                tickfont=dict(
                    size=9,
                    color=CHART_MUTED,
                ),
            ),
            hovertemplate=(
                "%{x}"
                "<br>%{y}"
                "<br>Điểm nhóm: %{z:.2f} / 100"
                "<extra></extra>"
            ),
        )
    )

    style(
        figure,
        300,
    )

    figure.update_layout(
        margin=dict(
            l=8,
            r=16,
            t=22,
            b=18,
        ),
    )

    figure.update_xaxes(
        showgrid=False,
        side="top",
        tickfont=dict(
            size=10,
            color=CHART_TEXT,
        ),
    )

    figure.update_yaxes(
        showgrid=False,
        autorange="reversed",
        tickfont=dict(
            size=10,
            color=CHART_TEXT,
        ),
    )

    return figure


# ---------------------------------------------------------------------
# Radar / spider chart for one bank
# ---------------------------------------------------------------------

def group_radar(
    groups,
    ticker,
    height=300,
):
    """
    Radar chart for one bank across the four BCDS groups.
    """
    codes = _ordered_groups(
        groups
    )

    labels = (
        groups
        .drop_duplicates("group")
        .set_index("group")
        .group_label
        .to_dict()
    )

    short_labels = {
        "credit": "Tín dụng",
        "capital": "Vốn & nguồn vốn",
        "profitability": "Sinh lời",
        "digital": "Chuyển đổi số",
    }

    part = (
        groups.loc[
            groups.ticker.eq(
                ticker
            )
        ]
        .set_index("group")
        .reindex(codes)
    )

    theta = [
        short_labels.get(
            code,
            labels.get(
                code,
                code,
            ),
        )
        for code in codes
    ]

    values = [
        float(value)
        if value is not None
        and math.isfinite(float(value))
        else 0.0
        for value in part.group_score_100
    ]

    if theta:
        theta_closed = theta + [
            theta[0]
        ]
        values_closed = values + [
            values[0]
        ]
    else:
        theta_closed = []
        values_closed = []

    figure = go.Figure(
        go.Scatterpolar(
            r=values_closed,
            theta=theta_closed,
            mode="lines+markers",
            fill="toself",
            line=dict(
                color="#7C6ED6",
                width=2.6,
            ),
            marker=dict(
                size=7,
                color="#5FB7A7",
                line=dict(
                    color="#FFFFFF",
                    width=1.5,
                ),
            ),
            fillcolor="rgba(124,110,214,.16)",
            text=[
                f"{value:.2f}"
                for value in values_closed
            ],
            hovertemplate=(
                "%{theta}"
                "<br>%{r:.2f} / 100"
                "<extra>"
                + ticker
                + "</extra>"
            ),
            name=ticker,
        )
    )

    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            l=36,
            r=36,
            t=28,
            b=28,
        ),
        showlegend=False,
        font=dict(
            family="Segoe UI Variable Text, Segoe UI, system-ui, sans-serif",
            color=CHART_TEXT,
            size=10,
        ),
        polar=dict(
            bgcolor="rgba(255,255,255,0)",
            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    100,
                ],
                tickvals=[
                    25,
                    50,
                    75,
                    100,
                ],
                tickfont=dict(
                    size=8,
                    color=CHART_MUTED,
                ),
                gridcolor="#D9E8F6",
                linecolor="#D9E8F6",
                angle=90,
            ),
            angularaxis=dict(
                gridcolor="#D9E8F6",
                linecolor="#C9DDEF",
                tickfont=dict(
                    size=10,
                    color=CHART_TEXT,
                ),
            ),
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D4E2F0",
            font=dict(
                color=CHART_TEXT,
            ),
        ),
    )

    return figure



# ---------------------------------------------------------------------
# Group contribution donut — Overview only
# ---------------------------------------------------------------------

def group_contribution_donut(
    groups,
    ticker,
    height=300,
):
    """
    Show how the four groups contribute to the selected bank's total score.

    Uses group_score (weighted contribution points), not group_score_100.
    This makes the Overview meaningfully different from the Comparison page.
    """
    codes = _ordered_groups(
        groups
    )

    labels = (
        groups
        .drop_duplicates("group")
        .set_index("group")
        .group_label
        .to_dict()
    )

    part = (
        groups.loc[
            groups.ticker.eq(
                ticker
            )
        ]
        .set_index("group")
        .reindex(codes)
    )

    values = [
        float(value)
        if value is not None
        and math.isfinite(float(value))
        else 0.0
        for value in part.group_score
    ]

    display_labels = [
        labels.get(
            code,
            code,
        )
        for code in codes
    ]

    palette = {
        "credit": "#4F8FEA",
        "capital": "#62BFA5",
        "profitability": "#E9AD53",
        "digital": "#8B78D8",
    }

    colors = [
        palette.get(
            code,
            "#58C4D8",
        )
        for code in codes
    ]

    total = sum(values)

    figure = go.Figure(
        go.Pie(
            labels=display_labels,
            values=values,
            hole=0.64,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=colors,
                line=dict(
                    color="#FFFFFF",
                    width=3,
                ),
            ),
            textinfo="percent",
            textfont=dict(
                size=10,
                color=CHART_TEXT,
            ),
            customdata=[
                [
                    code,
                    float(part.loc[code, "group_score_100"])
                    if code in part.index
                    and part.loc[code, "group_score_100"] is not None
                    else 0.0,
                ]
                for code in codes
            ],
            hovertemplate=(
                "%{label}"
                "<br>Đóng góp: %{value:.2f} điểm"
                "<br>Điểm nhóm: %{customdata[1]:.2f} / 100"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            l=20,
            r=20,
            t=24,
            b=24,
        ),
        font=dict(
            family="Segoe UI Variable Text, Segoe UI, system-ui, sans-serif",
            color=CHART_TEXT,
            size=10,
        ),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.04,
            yanchor="top",
            font=dict(
                size=9.5,
                color=CHART_TEXT,
            ),
        ),
        annotations=[
            dict(
                text=(
                    f"<b>{total:.2f}</b>"
                    "<br><span style='font-size:10px'>Tổng điểm</span>"
                ),
                x=0.5,
                y=0.5,
                showarrow=False,
                align="center",
                font=dict(
                    size=15,
                    color=CHART_TEXT,
                ),
            )
        ],
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D4E2F0",
            font=dict(
                color=CHART_TEXT,
            ),
        ),
    )

    return figure



# ---------------------------------------------------------------------
# Sample-level overview charts
# ---------------------------------------------------------------------

def group_sample_range(groups, height=290):
    """
    Clean sample-level overview:
    average score of the 5-bank sample by group.

    Min/max remain available in hover only so the chart stays intuitive.
    """
    codes = _ordered_groups(groups)

    labels = (
        groups
        .drop_duplicates("group")
        .set_index("group")
        .group_label
        .to_dict()
    )

    short_labels = {
        "credit": "Chất lượng tín dụng",
        "capital": "Vốn & nguồn vốn",
        "profitability": "Sinh lời & hiệu quả",
        "digital": "Chuyển đổi số",
    }

    palette = {
        "credit": "#4F8FEA",
        "capital": "#62BFA5",
        "profitability": "#E9AD53",
        "digital": "#8B78D8",
    }

    rows = []

    for code in codes:
        part = groups.loc[
            groups.group.eq(code),
            ["ticker", "group_score_100"],
        ].dropna()

        if part.empty:
            continue

        values = part.group_score_100.astype(float)

        min_idx = values.idxmin()
        max_idx = values.idxmax()

        rows.append(
            {
                "group": code,
                "label": short_labels.get(
                    code,
                    labels.get(code, code),
                ),
                "mean": float(values.mean()),
                "min": float(values.min()),
                "max": float(values.max()),
                "min_bank": str(
                    groups.loc[min_idx, "ticker"]
                ),
                "max_bank": str(
                    groups.loc[max_idx, "ticker"]
                ),
            }
        )

    figure = go.Figure(
        go.Bar(
            x=[
                row["mean"]
                for row in rows
            ],
            y=[
                row["label"]
                for row in rows
            ],
            orientation="h",
            width=0.46,
            marker=dict(
                color=[
                    palette.get(
                        row["group"],
                        "#58C4D8",
                    )
                    for row in rows
                ],
                line=dict(
                    color="#FFFFFF",
                    width=1.4,
                ),
            ),
            text=[
                f'{row["mean"]:.1f}'
                for row in rows
            ],
            textposition="outside",
            cliponaxis=False,
            customdata=[
                [
                    row["min"],
                    row["max"],
                    row["min_bank"],
                    row["max_bank"],
                ]
                for row in rows
            ],
            hovertemplate=(
                "%{y}"
                "<br>Điểm trung bình: %{x:.2f} / 100"
                "<br>Thấp nhất: %{customdata[0]:.2f} (%{customdata[2]})"
                "<br>Cao nhất: %{customdata[1]:.2f} (%{customdata[3]})"
                "<extra></extra>"
            ),
        )
    )

    style(
        figure,
        height,
    )

    figure.update_layout(
        showlegend=False,
        margin=dict(
            l=8,
            r=42,
            t=18,
            b=24,
        ),
    )

    figure.update_xaxes(
        range=[0, 104],
        tickvals=[0, 25, 50, 75, 100],
        title=None,
    )

    figure.update_yaxes(
        showgrid=False,
        autorange="reversed",
    )

    return figure


def group_dispersion(groups, height=250):
    """Range (max-min) across selected banks for each group."""
    codes = _ordered_groups(groups)
    labels = (
        groups
        .drop_duplicates("group")
        .set_index("group")
        .group_label
        .to_dict()
    )

    short_labels = {
        "credit": "Chất lượng tín dụng",
        "capital": "Vốn & nguồn vốn",
        "profitability": "Sinh lời & hiệu quả",
        "digital": "Chuyển đổi số",
    }

    palette = {
        "credit": "#4F8FEA",
        "capital": "#62BFA5",
        "profitability": "#E9AD53",
        "digital": "#8B78D8",
    }

    rows = []
    for code in codes:
        part = groups.loc[
            groups.group.eq(code),
            ["ticker", "group_score_100"],
        ].dropna()
        if part.empty:
            continue
        values = part.group_score_100.astype(float)
        min_i = values.idxmin()
        max_i = values.idxmax()
        rows.append(
            {
                "group": code,
                "label": short_labels.get(code, labels.get(code, code)),
                "spread": float(values.max() - values.min()),
                "min": float(values.min()),
                "max": float(values.max()),
                "min_bank": str(groups.loc[min_i, "ticker"]),
                "max_bank": str(groups.loc[max_i, "ticker"]),
            }
        )

    rows = sorted(rows, key=lambda row: row["spread"], reverse=True)

    fig = go.Figure(
        go.Bar(
            x=[row["spread"] for row in rows],
            y=[row["label"] for row in rows],
            orientation="h",
            width=0.48,
            marker=dict(
                color=[palette.get(row["group"], "#58C4D8") for row in rows],
                opacity=0.84,
                line=dict(color="#FFFFFF", width=1),
            ),
            text=[f'{row["spread"]:.1f}' for row in rows],
            textposition="outside",
            customdata=[
                [row["min"], row["max"], row["min_bank"], row["max_bank"]]
                for row in rows
            ],
            hovertemplate=(
                "%{y}"
                "<br>Độ phân hóa: %{x:.2f} điểm"
                "<br>Thấp nhất: %{customdata[0]:.2f} (%{customdata[2]})"
                "<br>Cao nhất: %{customdata[1]:.2f} (%{customdata[3]})"
                "<extra></extra>"
            ),
        )
    )

    style(fig, height)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=8, r=45, t=14, b=24),
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


# ---------------------------------------------------------------------
# Criterion comparison — lollipop
# ---------------------------------------------------------------------

def criterion_comparison(
    criteria,
    code,
    mode="normalized",
):
    """
    Horizontal lollipop chart for one criterion.

    It uses less ink than bars and keeps bank-to-bank comparison precise.
    """
    data = criteria.loc[
        criteria.criterion.eq(
            code
        )
    ].copy()

    value_column = (
        "raw_value"
        if mode == "raw"
        else "normalized_0_1"
    )

    data[value_column] = (
        data[value_column]
        .astype(float)
    )

    maximum = float(
        data[value_column].max()
    )

    if mode == "raw":
        lower = min(
            0.0,
            float(
                data[value_column].min()
            ),
        )

        upper = (
            maximum * 1.14
            if maximum > 0
            else 1.0
        )
    else:
        lower = 0.0
        upper = 1.06

    figure = go.Figure()

    for _, row in data.iterrows():
        value = float(
            row[value_column]
        )

        figure.add_shape(
            type="line",
            x0=min(
                0,
                value,
            ),
            x1=max(
                0,
                value,
            ),
            y0=row["ticker"],
            y1=row["ticker"],
            line=dict(
                color="#C7DAEE",
                width=5,
            ),
            layer="below",
        )

    figure.add_trace(
        go.Scatter(
            x=data[value_column],
            y=data.ticker,
            mode="markers+text",
            marker=dict(
                size=14,
                color=[
                    BANK_COLORS.get(
                        ticker,
                        CHART_BLUE,
                    )
                    for ticker in data.ticker
                ],
                line=dict(
                    color="#FFFFFF",
                    width=2,
                ),
            ),
            text=[
                number(value)
                for value in data[value_column]
            ],
            textposition="middle right",
            customdata=data[
                [
                    "raw_value",
                    "weighted_score",
                ]
            ],
            hovertemplate=(
                "%{y}"
                "<br>Giá trị hiển thị: %{x:.4f}"
                "<br>Giá trị gốc: %{customdata[0]:.4f}"
                "<br>Đóng góp: %{customdata[1]:.4f}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    style(
        figure,
        280,
    )

    figure.update_layout(
        margin=dict(
            l=8,
            r=48,
            t=20,
            b=22,
        ),
    )

    figure.update_xaxes(
        range=[
            lower,
            upper,
        ],
        zeroline=True,
        zerolinecolor="#B7CDE4",
        tickformat=".2f",
    )

    figure.update_yaxes(
        showgrid=False,
        autorange="reversed",
    )

    return figure


# ---------------------------------------------------------------------
# Overview mini chart — lollipop instead of bars
# ---------------------------------------------------------------------

def group_mini(
    groups,
    tickers,
):
    """
    Compact lollipop chart for one group.
    """
    part = (
        groups
        .set_index("ticker")
        .reindex(tickers)
    )

    figure = go.Figure()

    for ticker, row in part.iterrows():
        value = float(
            row.group_score_100
        )

        figure.add_shape(
            type="line",
            x0=ticker,
            x1=ticker,
            y0=0,
            y1=value,
            line=dict(
                color="#D3E2F1",
                width=4,
            ),
            layer="below",
        )

    figure.add_trace(
        go.Scatter(
            x=part.index,
            y=part.group_score_100,
            mode="markers+text",
            marker=dict(
                size=12,
                color=[
                    BANK_COLORS.get(
                        ticker,
                        CHART_BLUE,
                    )
                    for ticker in part.index
                ],
                line=dict(
                    color="#FFFFFF",
                    width=1.5,
                ),
            ),
            text=[
                number(value)
                for value in part.group_score_100
            ],
            textposition="top center",
            customdata=part[
                [
                    "group_score",
                    "group_max",
                ]
            ],
            hovertemplate=(
                "%{x}"
                "<br>Điểm nhóm: %{y:.2f} / 100"
                "<br>Đóng góp: %{customdata[0]:.2f} / %{customdata[1]:.2f}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    style(
        figure,
        130,
    )

    figure.update_layout(
        margin=dict(
            l=2,
            r=2,
            t=28,
            b=4,
        ),
    )

    figure.update_xaxes(
        showgrid=False,
        tickfont=dict(
            size=9,
            color=CHART_MUTED,
        ),
    )

    figure.update_yaxes(
        range=[
            0,
            110,
        ],
        showticklabels=False,
        showgrid=False,
    )

    return figure


# ---------------------------------------------------------------------
# Digital D1-D3 — radar with selected bank highlighted
# ---------------------------------------------------------------------

def digital_comparison(
    dataset,
    selected,
):
    """
    Radar comparison for D1-D3.

    The selected bank is highlighted with fill; other banks provide a muted
    reference envelope without crowding the page with more bars.
    """
    theta = list(
        DIGITAL_CODES
    )

    order = [
        bank
        for bank in dataset.bank_code
        if bank != selected
    ]

    if selected in set(
        dataset.bank_code
    ):
        order.append(
            selected
        )

    figure = go.Figure()

    for bank in order:
        row = dataset.loc[
            dataset.bank_code.eq(
                bank
            )
        ]

        if row.empty:
            continue

        values = [
            float(
                row.iloc[0][
                    code + "_score_0_3"
                ]
            )
            for code in DIGITAL_CODES
        ]

        values_closed = values + [
            values[0]
        ]

        theta_closed = theta + [
            theta[0]
        ]

        is_selected = (
            bank == selected
        )

        figure.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=theta_closed,
                mode="lines+markers",
                fill=(
                    "toself"
                    if is_selected
                    else "none"
                ),
                fillcolor=(
                    "rgba(124,110,214,.18)"
                    if is_selected
                    else "rgba(0,0,0,0)"
                ),
                line=dict(
                    color=(
                        "#7C6ED6"
                        if is_selected
                        else "#A9BED5"
                    ),
                    width=(
                        3
                        if is_selected
                        else 1.1
                    ),
                ),
                marker=dict(
                    size=(
                        7
                        if is_selected
                        else 4
                    ),
                    color=(
                        "#5FB7A7"
                        if is_selected
                        else "#A9BED5"
                    ),
                ),
                opacity=(
                    1.0
                    if is_selected
                    else 0.55
                ),
                name=bank,
                hovertemplate=(
                    bank
                    + " · %{theta}"
                    + "<br>Điểm: %{r:.0f} / 3"
                    + "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        height=286,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            l=34,
            r=34,
            t=38,
            b=28,
        ),
        legend=dict(
            orientation="h",
            x=0,
            y=1.08,
            yanchor="bottom",
            font=dict(
                size=9.5,
                color=CHART_TEXT,
            ),
        ),
        font=dict(
            family="Segoe UI Variable Text, Segoe UI, system-ui, sans-serif",
            color=CHART_TEXT,
        ),
        polar=dict(
            bgcolor="rgba(255,255,255,0)",
            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    3,
                ],
                tickvals=[
                    1,
                    2,
                    3,
                ],
                tickfont=dict(
                    size=8,
                    color=CHART_MUTED,
                ),
                gridcolor="#D9E8F6",
                linecolor="#D9E8F6",
            ),
            angularaxis=dict(
                gridcolor="#D9E8F6",
                linecolor="#C9DDEF",
                tickfont=dict(
                    size=10,
                    color=CHART_TEXT,
                ),
            ),
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D4E2F0",
            font=dict(
                color=CHART_TEXT,
            ),
        ),
    )

    return figure
