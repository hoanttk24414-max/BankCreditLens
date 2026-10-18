"""Run: python -m streamlit run dashboard/app.py. Read-only presentation."""
from pathlib import Path
import sys

# Support Streamlit, AppTest and launch commands from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

import charts
import data_adapter as data
import ui_components as ui
from config import (
    CRITERION_LABELS,
    DEFINITION_ALIASES,
    DIGITAL_CODES,
    DIRECTION_LABELS,
    GROUP_ORDER,
    PAGES,
    YEAR,
)

st.set_page_config(
    page_title="BCDS 2025 · Đánh giá chất lượng tín dụng",
    page_icon="▥",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.html(
    "<style>"
    + Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    + ui.bank_selector_logo_css()
    + "</style>"
)

LABELS = {
    "bank": "Ngân hàng",
    "ticker": "Mã",
    "year": "Năm",
    "rank": "Hạng",
    "criterion": "Tiêu chí",
    "group": "Mã nhóm",
    "group_label": "Nhóm",
    "raw_value": "Giá trị gốc",
    "normalized_0_1": "Chuẩn hóa (0–1)",
    "base_weight": "Trọng số gốc (điểm)",
    "effective_weight": "Trọng số hiệu lực (điểm)",
    "weighted_score": "Điểm đóng góp",
    "direction": "Chiều đánh giá",
    "status": "Trạng thái",
    "total_score": "Tổng điểm",
    "group_score": "Điểm đóng góp nhóm",
    "group_max": "Tối đa nhóm",
    "group_score_100": "Điểm nhóm (0–100)",
    "variable": "Biến",
    "value_clean": "Giá trị",
    "unit_clean": "Đơn vị",
    "source": "Nguồn",
    "source_title": "Tên tài liệu",
    "source_url": "Tài liệu nguồn",
    "evidence_text": "Bằng chứng",
    "bank_code": "Mã",
    "bank_name": "Ngân hàng",
    "indicator_code": "Tiêu chí",
    "indicator_name": "Nội dung đánh giá",
    "score_0_3": "Điểm (0–3)",
    "score_100": "Điểm (0–100)",
    "source_description": "Mô tả nguồn",
    "source_type": "Loại nguồn",
    "page_or_section": "Trang / Mục",
    "note": "Ghi chú",
    "as_of": "Thời điểm",
    "rubric_rule": "Khung chấm điểm",
    "score_rationale": "Lý do chấm điểm",
    "index_status": "Trạng thái chỉ số",
    "score_status": "Trạng thái kết quả",
}


def load(loader, **kwargs):
    try:
        return loader(**kwargs)
    except data.DataIssue as exc:
        st.warning(str(exc))
        return None


def plot(figure, key):
    st.plotly_chart(
        figure,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
        key=key,
    )


def remember_bank(widget_key):
    st.session_state["selected_bank"] = st.session_state[widget_key]


def bank_picker(frame, key, bank_column="ticker", name_column="bank"):
    options = frame[bank_column].drop_duplicates().tolist()
    names = (
        frame.drop_duplicates(bank_column)
        .set_index(bank_column)[name_column]
        .to_dict()
    )

    selected = st.session_state.get("selected_bank", options[0])

    if selected not in options:
        selected = options[0]

    return st.selectbox(
        "Ngân hàng",
        options,
        index=options.index(selected),
        format_func=lambda t: f"{t} · {names[t]}",
        key=key,
        on_change=remember_bank,
        args=(key,),
    )


def group_order(frame):
    order = {g: i for i, g in enumerate(GROUP_ORDER)}
    return frame.sort_values(
        "group",
        key=lambda values: values.map(order).fillna(len(order)),
        kind="stable",
    )


def ranking_status(ranking):
    if "score_status" in ranking:
        badges = " ".join(
            ui.status_badge(v, show_review=True)
            for v in ranking.score_status.drop_duplicates()
        )
        ui.html('<div class="ranking-status">' + badges + "</div>")


def criterion_units(definitions):
    units = {code: "điểm" for code in DIGITAL_CODES}

    if definitions is None or not {"indicator", "unit"}.issubset(definitions.columns):
        return units

    aliases = {
        definition: code
        for code, definition in DEFINITION_ALIASES.items()
    }

    for record in (
        definitions[["indicator", "unit"]]
        .dropna(subset=["indicator"])
        .to_dict("records")
    ):
        code = aliases.get(record["indicator"], record["indicator"])
        unit = str(record["unit"]).strip()
        units[code] = unit if unit else "—"

    return units



def overview_snapshot(ranking, groups):
    """
    Build a compact, data-derived snapshot for the Overview page.
    """
    if ranking is None or ranking.empty:
        return None

    ordered = ranking.sort_values(
        ["rank", "ticker"],
        kind="stable",
    )

    leader_row = ordered.iloc[0]

    result = {
        "ticker": leader_row.get("ticker", "N/A"),
        "bank": leader_row.get("bank", "N/A"),
        "score": leader_row.get("total_score"),
        "rank": leader_row.get("rank"),
        "strongest": [],
        "weakest": [],
        "strongest_score": None,
        "weakest_score": None,
        "spread": None,
    }

    if groups is None or groups.empty:
        return result

    part = groups.loc[
        groups.ticker.eq(
            result["ticker"]
        )
    ].copy()

    if part.empty:
        return result

    part["group_score_100"] = pd.to_numeric(
        part["group_score_100"],
        errors="coerce",
    )

    valid = part.dropna(
        subset=["group_score_100"]
    )

    if valid.empty:
        return result

    best = float(
        valid.group_score_100.max()
    )
    weakest = float(
        valid.group_score_100.min()
    )

    result["strongest"] = (
        valid.loc[
            valid.group_score_100.eq(best),
            "group_label",
        ]
        .astype(str)
        .tolist()
    )

    result["weakest"] = (
        valid.loc[
            valid.group_score_100.eq(weakest),
            "group_label",
        ]
        .astype(str)
        .tolist()
    )

    result["strongest_score"] = best
    result["weakest_score"] = weakest
    result["spread"] = best - weakest

    return result


def overview():
    ui.page_header(
        "Đánh giá chất lượng tín dụng ngân hàng tích hợp chuyển đổi số",
        "Chỉ số nghiên cứu gồm 12 tiêu chí tài chính + 3 tiêu chí chuyển đổi số",
        PAGES[0],
        overview=True,
    )

    ranking = load(
        data.load_ranking
    )

    criteria = load(
        data.load_criterion_scores
    )

    metadata = load(
        data.load_scoring_metadata
    )

    groups = load(
        data.load_group_scores
    )

    leaders = (
        ranking.loc[
            ranking["rank"].eq(
                ranking["rank"].min()
            )
        ]
        if ranking is not None
        and not ranking.empty
        else None
    )

    leader = (
        " · ".join(
            leaders.ticker
        )
        if leaders is not None
        else "N/A"
    )

    ui.metrics(
        [
            (
                "Ngân hàng",
                ranking.ticker.nunique()
                if ranking is not None
                else "N/A",
                "Phạm vi nghiên cứu",
            ),
            (
                "Tiêu chí",
                metadata.get(
                    "criteria_count_defined",
                    "N/A",
                )
                if metadata
                else "N/A",
                "12 tài chính + 3 chuyển đổi số",
            ),
            (
                "Dẫn đầu",
                leader,
                "Theo tổng điểm BCDS",
            ),
            (
                "Điểm cao nhất",
                ui.number(
                    ranking.total_score.max()
                )
                if ranking is not None
                else "N/A",
                "Thang điểm 100",
            ),
        ]
    )


    # --------------------------------------------------------------
    # Executive overview: ranking + sample-level group picture
    # --------------------------------------------------------------

    if ranking is not None:
        left, right = st.columns(
            [1, 1.08],
            gap="medium",
        )

        with left, ui.panel(
            "overview_table"
        ):
            ui.section_header(
                "Xếp hạng tổng quan",
                "Thứ hạng tổng điểm của 5 ngân hàng trong mẫu nghiên cứu",
                "trophy",
                "gold",
            )

            ui.ranking_table(
                ranking
            )

        if groups is not None and not groups.empty:
            with right, ui.panel(
                "overview_sample_groups"
            ):
                ui.section_header(
                    "Điểm trung bình theo nhóm",
                    "Trung bình 5 ngân hàng; thấp nhất–cao nhất được xem khi rê chuột",
                    "bars",
                    "violet",
                )

                plot(
                    charts.group_sample_range(
                        groups,
                        height=255,
                    ),
                    "overview_sample_range",
                )

    # --------------------------------------------------------------
    # Quick insight
    # --------------------------------------------------------------

    snapshot = overview_snapshot(
        ranking,
        groups,
    )

    if snapshot is not None:
        with ui.panel(
            "overview_quick_insight"
        ):
            ui.section_header(
                "Nhận xét nhanh",
                "Tóm tắt điều đáng chú ý nhất từ kết quả hiện tại",
                "bulb",
                "blue",
            )

            strongest = (
                " · ".join(
                    snapshot["strongest"]
                )
                or "N/A"
            )

            weakest = (
                " · ".join(
                    snapshot["weakest"]
                )
                or "N/A"
            )

            ui.html(
                '<div class="premium-insight-copy">'
                f'<p><strong>{ui.safe(snapshot["ticker"])}</strong> dẫn đầu với '
                f'<b>{ui.safe(ui.number(snapshot["score"]))} điểm</b>. '
                + (
                    f'Ngân hàng nổi bật ở <b>{ui.safe(strongest)}</b>, '
                    f'trong khi <b>{ui.safe(weakest)}</b> là nhóm có điểm thấp nhất.'
                    if snapshot["strongest_score"] is not None
                    and snapshot["weakest_score"] is not None
                    else ""
                )
                + '</p>'
                '</div>'
            )

            if groups is not None and not groups.empty:
                dispersion = (
                    groups.groupby(
                        ["group", "group_label"],
                        as_index=False,
                    )["group_score_100"]
                    .agg(["min", "max"])
                    .reset_index()
                )

                dispersion["spread"] = (
                    dispersion["max"]
                    - dispersion["min"]
                )

                if not dispersion.empty:
                    widest = dispersion.loc[
                        dispersion["spread"].idxmax()
                    ]

                    narrowest = dispersion.loc[
                        dispersion["spread"].idxmin()
                    ]

                    ui.html(
                        '<div class="premium-implication">'
                        f'{ui.icon("trend-up", "gold")}'
                        '<div>'
                        '<strong>Hàm ý</strong>'
                        f'<p>Mức độ phân hóa lớn nhất nằm ở '
                        f'<b>{ui.safe(widest["group_label"])}</b> '
                        f'({ui.safe(ui.number(widest["spread"]))} điểm), '
                        f'trong khi <b>{ui.safe(narrowest["group_label"])}</b> '
                        f'đồng đều hơn giữa các ngân hàng '
                        f'({ui.safe(ui.number(narrowest["spread"]))} điểm).</p>'
                        '</div>'
                        '</div>'
                    )

    # --------------------------------------------------------------
    # Leader profile

    # --------------------------------------------------------------
    # Leader profile — intentionally different from Comparison page
    # --------------------------------------------------------------

    if groups is not None and not groups.empty:
        selected_ticker = (
            ranking.sort_values(
                "rank"
            ).ticker.iloc[0]
            if ranking is not None
            and not ranking.empty
            else groups.ticker.iloc[0]
        )

        with ui.panel(
            "overview_groups"
        ):
            ui.section_header(
                f"Hồ sơ ngân hàng dẫn đầu ({selected_ticker})",
                "Một góc nhìn về cấu trúc điểm và mức đóng góp của từng nhóm",
                "shield",
                "gold",
            )

            radar_col, donut_col = st.columns(
                [1, 1],
                gap="medium",
            )

            with radar_col:
                st.markdown(
                    f"**Cấu trúc điểm nhóm · {selected_ticker}**"
                )

                plot(
                    charts.group_radar(
                        groups,
                        selected_ticker,
                        height=300,
                    ),
                    "overview_group_radar",
                )

            with donut_col:
                st.markdown(
                    f"**Cơ cấu đóng góp vào tổng điểm · {selected_ticker}**"
                )

                plot(
                    charts.group_contribution_donut(
                        groups,
                        selected_ticker,
                        height=300,
                    ),
                    "overview_group_donut",
                )


def comparison():
    ui.page_header(
        "So sánh ngân hàng",
        "So sánh nhanh tổng điểm, điểm theo nhóm và cấu trúc thế mạnh của các ngân hàng.",
        PAGES[1],
    )

    ranking = load(data.load_ranking)
    groups = load(data.load_group_scores)

    if ranking is None:
        return

    ranking = ranking.sort_values(
        "rank",
        kind="stable",
    )

    options = ranking.ticker.tolist()

    with ui.panel("comparison_filter"):
        selected = st.multiselect(
            "Chọn từ 2 đến 5 ngân hàng",
            options,
            default=options,
            max_selections=5,
            key="comparison_banks",
        )

    if len(selected) < 2:
        st.info(
            "Vui lòng chọn ít nhất 2 ngân hàng để so sánh."
        )
        return

    chosen = ranking.loc[
        ranking.ticker.isin(selected)
    ]

    selected_groups = (
        groups.loc[
            groups.ticker.isin(selected)
        ]
        if groups is not None
        else None
    )

    ui.bank_mini_cards(
        chosen,
        selected_groups,
    )

    left, right = st.columns(
        [1.2, 1],
        gap="medium",
    )

    if groups is not None:
        with left, ui.panel("comparison_groups"):
            ui.section_header(
                "So sánh theo nhóm tiêu chí",
                "Cùng thang 0–100 để so sánh trực tiếp",
                "bars",
            )
            plot(
                charts.group_comparison(
                    selected_groups,
                    chosen.ticker.tolist(),
                ),
                "compare_groups",
            )

    with right, ui.panel("comparison_totals"):
        ui.section_header(
            "So sánh tổng điểm",
            "So sánh trực tiếp tổng điểm BCDS",
            "trophy",
            "gold",
        )

        figure = charts.comparison_ranking_bar(
            chosen
        )

        with st.container(key="comparison_totals_chart"):
            logo_column, chart_column = st.columns(
                [1, 14],
                gap=None,
            )

            with logo_column:
                ui.bank_logo_axis(
                    figure.data[0].y,
                    height=figure.layout.height,
                    top=figure.layout.margin.t,
                    bottom=figure.layout.margin.b,
                )

            with chart_column:
                plot(
                    figure,
                    "compare_totals",
                )

    if groups is not None:
        left, right = st.columns(
            [1.2, 1],
            gap="medium",
        )

        with left, ui.panel("comparison_dispersion"):
            ui.section_header(
                "Mức độ phân hóa giữa các ngân hàng",
                "Khoảng cách cao nhất–thấp nhất của từng nhóm trong lựa chọn hiện tại",
                "layers",
                "teal",
            )

            plot(
                charts.group_dispersion(
                    selected_groups,
                    height=250,
                ),
                "compare_group_dispersion",
            )

        with right, ui.panel("comparison_summary"):
            ui.section_header(
                "Vị thế tương đối của ngân hàng",
                "Bấm từng ngân hàng để xem từng nhóm cao/thấp hơn trung bình của lựa chọn",
                "bulb",
                "gold",
            )

            ui.analytical_summary(
                chosen,
                selected_groups,
            )


def criterion_detail():
    ui.page_header(
        "Chi tiết tiêu chí",
        "Theo dõi giá trị gốc, điểm chuẩn hóa, trọng số và đóng góp đã được xuất.",
        PAGES[2],
    )

    criteria = load(
        data.load_criterion_scores
    )

    if criteria is None:
        return

    definitions = load(
        data.load_workbook_sheet,
        sheet="Metric_Definitions",
    )

    units = criterion_units(
        definitions
    )

    with ui.panel("criterion_filter"):
        a, b, c, d = st.columns(
            [1, 1.15, 0.85, 1.4],
            gap="medium",
        )

        with a:
            ticker = bank_picker(
                criteria,
                "criterion_bank",
            )

        with b:
            groups = (
                group_order(criteria)
                .drop_duplicates("group")
                .set_index("group")
                .group_label
                .to_dict()
            )

            group = st.selectbox(
                "Nhóm tiêu chí",
                [None] + list(groups),
                format_func=lambda v: (
                    "Tất cả nhóm"
                    if v is None
                    else groups[v]
                ),
                key="criterion_group",
            )

        with c:
            kind = st.selectbox(
                "Loại tiêu chí",
                [
                    "Tất cả",
                    "Định lượng",
                    "Định tính",
                ],
                key="criterion_kind",
            )

        filtered = data.filter_criteria(
            criteria,
            ticker,
            group,
            kind,
        )

        with d:
            codes = filtered.criterion.tolist()

            if (
                st.session_state.get(
                    "criterion_selected"
                )
                not in codes
            ):
                st.session_state[
                    "criterion_selected"
                ] = (
                    codes[0]
                    if codes
                    else None
                )

            code = st.selectbox(
                "Tiêu chí cần xem",
                codes,
                format_func=lambda v: (
                    f"{v} · "
                    f"{CRITERION_LABELS.get(v, v)}"
                ),
                key="criterion_selected",
                disabled=filtered.empty,
                placeholder="Không có tiêu chí phù hợp",
            )

    if filtered.empty:
        st.info(
            "Không có tiêu chí phù hợp với bộ lọc hiện tại. "
            "Hãy đổi nhóm hoặc loại tiêu chí."
        )
        return

    left, right = st.columns(
        [2.25, 1.20],
        gap="medium",
    )

    with left, ui.panel("criterion_results"):
        ui.section_header(
            f"Danh sách tiêu chí · {ticker}",
            f"{len(filtered)} tiêu chí phù hợp · chuẩn hóa thang 0–1",
            "file",
        )

        search = st.text_input(
            "Tìm kiếm tiêu chí",
            key="criterion_search",
            placeholder="Tìm theo mã hoặc tên tiêu chí",
        )

        visible = (
            filtered.loc[
                filtered.criterion.str.contains(
                    search,
                    case=False,
                    na=False,
                )
                | filtered.criterion.map(
                    lambda value: CRITERION_LABELS.get(
                        value,
                        value,
                    )
                ).str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ]
            if search
            else filtered
        )

        columns = [
            "criterion",
            "group_label",
            "raw_value",
            "normalized_0_1",
            "effective_weight",
            "weighted_score",
            "status",
        ]

        if st.checkbox(
            "Hiển thị trọng số gốc và chiều đánh giá",
            key="criterion_extra_columns",
        ):
            columns += [
                "base_weight",
                "direction",
            ]

        display = visible[
            [
                c
                for c in columns
                if c in visible
            ]
        ].copy()

        if "direction" in display:
            display["direction"] = (
                display.direction.map(
                    lambda v: DIRECTION_LABELS.get(
                        v,
                        v,
                    )
                )
            )

        compact_labels = {
            **LABELS,
            "normalized_0_1": "Chuẩn hóa (0–1)",
            "effective_weight": "Trọng số",
            "weighted_score": "Đóng góp",
        }

        ui.criterion_table(
            visible,
            units,
            code,
        )

        with st.container(
            key="criterion_table_native"
        ):
            ui.data_table(
                display,
                compact_labels,
                {
                    "raw_value": "%.2f",
                    "normalized_0_1": "%.2f",
                    "base_weight": "%.2f",
                    "effective_weight": "%.2f",
                    "weighted_score": "%.2f",
                },
                height=min(
                    528,
                    38 + len(display) * 32,
                ),
                key="criterion_table",
            )

    row = (
        filtered.loc[
            filtered.criterion.eq(code)
        ]
        .iloc[0]
    )

    with right, ui.panel("criterion_detail"):
        ui.section_header(
            "Chi tiết tiêu chí",
            ticker,
            "layers",
            "violet",
        )

        bank_name = (
            filtered.loc[
                filtered.ticker.eq(ticker),
                "bank",
            ]
            .iloc[0]
        )

        ui.html(
            f'<div class="criterion-bank-name">'
            f"{ui.safe(ticker)} · {ui.safe(bank_name)}"
            f"</div>"
        )

        ui.criterion_detail_card(
            row,
            units,
            bank_name,
        )

    with ui.panel("criterion_chart"):
        chart_mode = st.selectbox(
            "Hiển thị biểu đồ",
            [
                "Chuẩn hóa (0–1)",
                "Giá trị gốc",
            ],
            key="criterion_chart_mode",
        )

        mode = (
            "raw"
            if chart_mode == "Giá trị gốc"
            else "normalized"
        )

        ui.section_header(
            f"{code} · So sánh giữa các ngân hàng",
            (
                "So sánh "
                f"{'giá trị gốc' if mode == 'raw' else 'điểm chuẩn hóa'} "
                f"của tiêu chí {code} "
                f"(đơn vị: {units.get(code, '—')})"
            ),
            "bars",
        )

        plot(
            charts.criterion_comparison(
                criteria,
                code,
                mode=mode,
            ),
            "criterion_comparison",
        )

    with (
        st.container(key="criterion_context"),
        st.expander(
            "Giải thích tiêu chí và ngữ cảnh dữ liệu"
        ),
    ):
        if code in DIGITAL_CODES:
            st.write(
                "Đánh giá định tính trên thang 0–3 dựa trên bằng chứng. "
                "Dashboard chỉ đọc và trình bày kết quả đã được pipeline xuất."
            )

            rubric = ui.text(
                row.get("rubric_rule")
            )

            rationale = ui.text(
                row.get("score_rationale")
            )

            if rubric and rubric != "—":
                st.markdown(
                    "**Khung chấm điểm 0–3**"
                )
                st.write(rubric)

            if (
                rationale
                and rationale != "—"
            ):
                score = row.get(
                    "raw_value"
                )

                score_text = (
                    f"{float(score):.0f}/3"
                    if pd.notna(score)
                    else "—"
                )

                st.markdown(
                    f"**Lý do {ticker} được {score_text}**"
                )
                st.write(rationale)

            st.caption(
                "Rubric và lý do chấm được lấy từ dữ liệu evidence; "
                "Dashboard không tính lại điểm."
            )

        else:
            if (
                definitions is not None
                and {
                    "indicator",
                    "formula",
                    "unit",
                }.issubset(
                    definitions.columns
                )
            ):
                definition = definitions.loc[
                    definitions.indicator.eq(
                        DEFINITION_ALIASES.get(
                            code,
                            code,
                        )
                    )
                ]

                if not definition.empty:
                    st.write(
                        "Đơn vị: "
                        + ui.text(
                            definition.iloc[0]["unit"]
                        )
                    )

                    st.write(
                        "Công thức tham chiếu từ dự án: "
                        + ui.text(
                            definition.iloc[0]["formula"]
                        )
                    )

                    st.caption(
                        "Công thức chỉ phục vụ giải thích. "
                        "Dashboard không tính lại giá trị hay điểm."
                    )

        if st.checkbox(
            "Hiển thị dòng dữ liệu hợp nhất",
            key="show_merged",
        ):
            merged = load(
                data.load_merged_data
            )

            if merged is not None:
                contextual = (
                    data.select_bank(
                        merged,
                        ticker,
                    )
                    .drop(
                        columns=[
                            "included_in_BCDS_15"
                        ],
                        errors="ignore",
                    )
                )

                ui.source_detail_table(
                    contextual,
                    LABELS,
                    variant="criterion-context",
                    key="merged_context",
                    show_review=False,
                )


def digital():
    ui.page_header(
        "Chuyển đổi số D1–D3",
        "Từ định danh số đến tín dụng số và ứng dụng dữ liệu trong quản trị rủi ro.",
        PAGES[3],
    )

    dataset = load(
        data.load_digital_dataset
    )

    evidence = load(
        data.load_digital_evidence
    )

    ticker = None

    if dataset is not None:
        with ui.panel("digital_filter"):
            ticker = bank_picker(
                dataset,
                "digital_bank",
                "bank_code",
                "bank_name",
            )

        row = (
            data.select_bank(
                dataset,
                ticker,
                "bank_code",
            )
            .iloc[0]
            .to_dict()
        )

        ui.digital_cards(
            row,
            CRITERION_LABELS,
        )

        st.caption(
            "Thang điểm 0–3 · Đánh giá định tính dựa trên bằng chứng · "
            "Điểm và căn cứ chấm được đọc từ output của pipeline."
        )

        left, right = st.columns(
            [1.05, 1],
            gap="medium",
        )

        with left, ui.panel("digital_matrix"):
            ui.section_header(
                "Ma trận chuyển đổi số",
                "Điểm D1–D3 của toàn bộ ngân hàng trong nghiên cứu",
            )

            columns = [
                "bank_name",
                "bank_code",
            ] + [
                f"{code}_score_0_3"
                for code in DIGITAL_CODES
            ]

            labels = {
                **LABELS,
                **{
                    f"{code}_score_0_3": code
                    for code in DIGITAL_CODES
                },
            }

            ui.digital_matrix_table(
                dataset[columns],
                ticker,
            )

            with st.container(
                key="digital_matrix_native"
            ):
                ui.data_table(
                    dataset[columns],
                    labels,
                    {
                        f"{code}_score_0_3": "%d"
                        for code in DIGITAL_CODES
                    },
                    key="digital_matrix",
                )

        with right, ui.panel("digital_chart"):
            ui.section_header(
                "Điểm D1–D3 theo ngân hàng",
                f"Ngân hàng đang xem: {ticker} · thang điểm 0–3",
                "bars",
                "violet",
            )

            plot(
                charts.digital_comparison(
                    dataset,
                    ticker,
                ),
                "digital_comparison",
            )

    if evidence is not None:
        if ticker is None:
            ticker = bank_picker(
                evidence,
                "evidence_bank",
                "bank_code",
                (
                    "bank_name"
                    if "bank_name" in evidence
                    else "bank_code"
                ),
            )

        ui.section_header(
            f"Bằng chứng & nguồn tham chiếu · {ticker}",
            "Tài liệu tham chiếu cho điểm D1–D3; trạng thái bằng chứng xem tại Nguồn dữ liệu & phương pháp.",
            "file",
            "blue",
        )

        selected = data.select_bank(
            evidence,
            ticker,
            "bank_code",
        )

        for column, code in zip(
            st.columns(
                3,
                gap="medium",
            ),
            DIGITAL_CODES,
        ):
            with column:
                records = selected.loc[
                    selected.indicator_code.eq(code)
                ]

                if records.empty:
                    st.info(
                        f"{code}: không có bản ghi bằng chứng."
                    )

                for record in records.to_dict(
                    "records"
                ):
                    ui.evidence_card(
                        record,
                        ticker,
                    )

                    rubric = ui.text(
                        record.get(
                            "rubric_rule"
                        )
                    )

                    rationale = ui.text(
                        record.get(
                            "score_rationale"
                        )
                    )

                    with st.expander(
                        f"Căn cứ chấm {code}",
                        expanded=False,
                    ):
                        if (
                            rubric
                            and rubric != "—"
                        ):
                            st.markdown(
                                "**Khung chấm điểm 0–3**"
                            )
                            st.write(
                                rubric
                            )

                        if (
                            rationale
                            and rationale != "—"
                        ):
                            score = record.get(
                                "score_0_3"
                            )

                            score_text = (
                                f"{float(score):.0f}/3"
                                if pd.notna(score)
                                else "—"
                            )

                            st.markdown(
                                f"**Lý do {ticker} được {score_text}**"
                            )

                            st.write(
                                rationale
                            )


def sources():
    ui.page_header(
        "Nguồn dữ liệu & phương pháp",
        "Minh bạch nguồn tham chiếu, trạng thái bằng chứng và phạm vi của kết quả nghiên cứu.",
        PAGES[4],
    )

    finance = load(
        data.load_financial_sources
    )

    evidence = load(
        data.load_digital_evidence
    )

    metadata = load(
        data.load_scoring_metadata
    )

    ranking = load(
        data.load_ranking
    )

    if ranking is not None:
        ranking_status(
            ranking
        )

    ui.metrics(
        [
            (
                "Bản ghi tài chính",
                len(finance)
                if finance is not None
                else "N/A",
                "Dữ liệu đã tổng hợp",
            ),
            (
                "Bằng chứng D1–D3",
                len(evidence)
                if evidence is not None
                else "N/A",
                "Đánh giá chuyển đổi số",
            ),
            (
                "Nguồn tham chiếu số",
                evidence.source_url.dropna().nunique()
                if (
                    evidence is not None
                    and "source_url" in evidence
                )
                else "N/A",
                "Tài liệu nguồn phân biệt",
            ),
            (
                "Năm đánh giá",
                metadata.get(
                    "year",
                    "N/A",
                )
                if metadata
                else "N/A",
                "Phạm vi nghiên cứu",
            ),
        ]
    )

    left, center, right = st.columns(
        [1.35, 1.25, 1],
        gap="medium",
    )

    if finance is not None:
        with left, ui.panel("financial_sources"):
            ui.section_header(
                "Nguồn dữ liệu tài chính",
                "Bao gồm năm trước dùng cho số dư bình quân",
                "file",
            )

            a, b = st.columns(2)

            with a:
                year = st.selectbox(
                    "Năm dữ liệu tài chính",
                    [
                        None
                    ]
                    + sorted(
                        finance.year
                        .unique()
                        .tolist()
                    ),
                    format_func=lambda v: (
                        "Tất cả"
                        if v is None
                        else str(v)
                    ),
                    key="source_year",
                )

            with b:
                bank = st.selectbox(
                    "Ngân hàng trong nguồn tài chính",
                    [
                        None
                    ]
                    + finance.ticker.drop_duplicates().tolist(),
                    format_func=lambda v: (
                        "Tất cả ngân hàng"
                        if v is None
                        else v
                    ),
                    key="source_bank",
                )

            filtered = finance.loc[
                (
                    finance.year.eq(year)
                    if year is not None
                    else pd.Series(
                        True,
                        index=finance.index,
                    )
                )
                & (
                    finance.ticker.eq(bank)
                    if bank
                    else pd.Series(
                        True,
                        index=finance.index,
                    )
                )
            ]

            preferred = [
                "ticker",
                "year",
                "variable",
                "value_clean",
                "unit_clean",
                "source_url",
                "status",
                "source",
                "source_title",
                "evidence_text",
                "bank",
            ]

            provenance = [
                c
                for c in (
                    "ticker",
                    "year",
                    "source",
                    "status",
                    "source_url",
                )
                if c in filtered
            ]

            ui.source_table(
                filtered[
                    provenance
                ].drop_duplicates(),
                LABELS,
                height=360,
            )

            with st.expander(
                "Chi tiết dữ liệu tài chính"
            ):
                ui.source_detail_table(
                    filtered[
                        [
                            c
                            for c in preferred
                            if c in filtered
                        ]
                    ],
                    LABELS,
                    {
                        "value_clean": "%.2f",
                        "year": "%d",
                    },
                    variant="financial",
                    key="financial_raw",
                )

            st.caption(
                "Đơn vị ty_dong trong nguồn tương ứng tỷ đồng. "
                "URL trống được giữ là thiếu dữ liệu."
            )

            ui.source_summary(
                filtered,
                "source",
                "Tổng hợp theo loại nguồn",
            )

    if evidence is not None:
        with center, ui.panel("digital_sources"):
            ui.section_header(
                "Bằng chứng chuyển đổi số",
                "D1–D3 · nguồn, điểm và trạng thái",
                "layers",
                "violet",
            )

            source_types = (
                evidence.source_type
                .dropna()
                .drop_duplicates()
                .tolist()
                if "source_type" in evidence
                else []
            )

            source_type = st.selectbox(
                "Loại nguồn bằng chứng",
                [
                    None
                ]
                + source_types,
                format_func=lambda value: (
                    "Tất cả nguồn"
                    if value is None
                    else value
                ),
                key="evidence_source_type",
            )

            shown = (
                evidence.loc[
                    evidence.source_type.eq(
                        source_type
                    )
                ]
                if source_type is not None
                else evidence
            )

            preferred = [
                "bank_code",
                "indicator_code",
                "score_0_3",
                "status",
                "source_url",
            ]

            columns = [
                c
                for c in preferred
                if c in evidence
            ]

            ui.source_table(
                shown[columns],
                {
                    **LABELS,
                    "score_0_3": "Điểm",
                    "indicator_code": "Chỉ tiêu",
                    "source_url": "Nguồn",
                },
                height=444,
            )

            with st.expander(
                "Chi tiết bằng chứng và tài liệu"
            ):
                ui.source_detail_table(
                    shown,
                    LABELS,
                    variant="digital",
                    key="evidence_raw",
                )

            st.caption(
                "Bản ghi đang rà soát được giữ nguyên trạng thái từ dữ liệu nguồn."
            )

            if "source_type" in shown:
                ui.source_summary(
                    shown,
                    "source_type",
                    "Thống kê loại nguồn bằng chứng",
                )

    with right, ui.panel("methodology"):
        ui.section_header(
            "Phương pháp đánh giá",
            "12 định lượng + 3 định tính",
            "shield",
            "teal",
        )

        methodology_metadata = (
            metadata.copy()
            if metadata
            else metadata
        )

        if (
            methodology_metadata is not None
            and "criteria_count"
            not in methodology_metadata
        ):
            methodology_metadata[
                "criteria_count"
            ] = methodology_metadata.get(
                "criteria_count_defined"
            )

        ui.methodology_steps(
            methodology_metadata
        )

        criteria = load(
            data.load_criterion_scores
        )

        ui.group_weights_card(
            criteria
        )

    with ui.panel("disclaimer"):
        ui.section_header(
            "Lưu ý & tuyên bố",
            symbol="shield",
            tone="gold",
        )

        ui.html(
            '<p class="disclaimer-copy">'
            "Kết quả phục vụ nghiên cứu so sánh, "
            "không phải xếp hạng tín nhiệm chính thức. "
            "Bằng chứng có trạng thái đang rà soát "
            "chưa được xác thực độc lập."
            "</p>"
        )

        if metadata:
            st.caption(
                ui.text(
                    metadata.get(
                        "disclaimer"
                    )
                )
            )

            if metadata.get(
                "skipped_indicators"
            ):
                st.write(
                    "Tiêu chí được upstream bỏ qua: "
                    + ", ".join(
                        metadata[
                            "skipped_indicators"
                        ]
                    )
                )

    if st.checkbox(
        "Mở bảng tham chiếu Excel",
        key="show_workbook",
    ):
        candidate_sheets = [
            "Financial_Sources",
            "Metric_Definitions",
            "Missing_Check",
            "Consistency_Check",
            "Crawl_Status",
        ]

        workbook_tables = {
            name: load(
                data.load_workbook_sheet,
                sheet=name,
            )
            for name in candidate_sheets
        }

        available_sheets = [
            name
            for name, frame in workbook_tables.items()
            if (
                frame is not None
                and not frame.empty
                and frame.replace(
                    r"^\s*$",
                    pd.NA,
                    regex=True,
                ).notna().any(axis=None)
            )
        ]

        if available_sheets:
            if (
                st.session_state.get(
                    "workbook_sheet"
                )
                not in available_sheets
            ):
                st.session_state[
                    "workbook_sheet"
                ] = available_sheets[0]

            with st.container(
                key="workbook_reference"
            ):
                sheet = st.selectbox(
                    "Bảng tham chiếu",
                    available_sheets,
                    key="workbook_sheet",
                )

                ui.source_detail_table(
                    workbook_tables[
                        sheet
                    ],
                    LABELS,
                    variant="reference",
                    key="workbook_table",
                )

        else:
            st.session_state.pop(
                "workbook_sheet",
                None,
            )


with st.sidebar:
    ui.html(
        '<div class="sidebar-brand">'
        '<div class="brand-mark">B</div>'
        "<div>"
        "<strong>Banking Insights</strong>"
        "<span>Digital Banking Group Project</span>"
        "</div>"
        "</div>"
    )

    page = st.radio(
        "Điều hướng",
        PAGES,
        key="navigation",
        label_visibility="collapsed",
    )

    ui.html(
        '<div class="sidebar-model">'
        + ui.icon("bars")
        + "<div>"
        "<strong>Mô hình 12 + 3</strong>"
        "<p>"
        "12 chỉ tiêu định lượng<br>"
        "3 chỉ tiêu định tính<br>"
        "Tổng 15 tiêu chí"
        "</p>"
        "</div>"
        "</div>"
    )

    ui.html(
        f'<div class="sidebar-context">'
        f"<strong>Năm đánh giá: {YEAR}</strong>"
        f"<p>"
        f"Chỉ số nghiên cứu so sánh · không phải xếp hạng tín nhiệm"
        f"</p>"
        f"</div>"
    )

    if st.button(
        "Làm mới dữ liệu",
        width="stretch",
        key="refresh",
    ):
        data.refresh_data()
        st.toast(
            "Đã đọc lại dữ liệu đã xuất."
        )

    art = (
        ui.bank_art("sidebar")
    )

    ui.html(
        '<div class="sidebar-illustration">'
        + art
        + f"<p>Digital Banking<br>Vietnam {YEAR}</p>"
        + "</div>"
    )


if page == PAGES[0]:
    with st.container(
        key="overview_page"
    ):
        overview()

elif page == PAGES[1]:
    with st.container(
        key="comparison_page"
    ):
        comparison()

elif page == PAGES[2]:
    with st.container(
        key="criterion_detail_page"
    ):
        criterion_detail()

elif page == PAGES[3]:
    with st.container(
        key="digital_page"
    ):
        digital()

else:
    with st.container(
        key="sources_page"
    ):
        sources()


ui.html(
    '<div class="footer-note">'
    "Digital Banking · Nghiên cứu nhóm 2025 · "
    "Các giá trị và trạng thái được trình bày từ output của dự án."
    "</div>"
)
