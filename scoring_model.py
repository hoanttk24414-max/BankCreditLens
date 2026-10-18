"""
BCDS: Bộ chỉ số nghiên cứu gồm 12 tiêu chí tài chính
và 3 tiêu chí chuyển đổi số D1/D2/D3.

Đây là chỉ số so sánh phục vụ nghiên cứu,
không phải xếp hạng tín nhiệm (credit rating).
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"

BANKS = [
    "VCB",
    "BID",
    "CTG",
    "TCB",
    "MBB",
]


# ---------------------------------------------------------
# Bộ 15 tiêu chí
#
# weight: điểm phần trăm, tổng = 100
# direction:
#   high  -> càng cao càng tốt
#   low   -> càng thấp càng tốt
#   fixed -> điểm định tính 0–3, chuẩn hóa bằng score / 3
# ---------------------------------------------------------
CRITERIA = [
    ("NPL", "NPL_%", "credit", 14, "low"),
    ("Group2", "Group2_%", "credit", 7, "low"),
    ("LLR", "LLR_NPL_%", "credit", 8, "high"),
    ("CoR", "CoR_%", "credit", 6, "low"),

    ("CAR", "CAR_%", "capital", 7, "high"),
    (
        "EquityAssets",
        "Equity_Assets_%",
        "capital",
        5,
        "high",
    ),
    (
        "CASA",
        "CASA_%",
        "capital",
        4,
        "high",
    ),
    (
        "DepositsLiabilities",
        "Customer_Deposits_Liabilities_%",
        "capital",
        4,
        "high",
    ),

    ("ROA", "ROA_%", "profitability", 5, "high"),
    ("ROE", "ROE_%", "profitability", 5, "high"),
    ("NIM", "NIM_%", "profitability", 5, "high"),
    ("CIR", "CIR_%", "profitability", 5, "low"),

    ("D1", "D1_score_0_3", "digital", 25 / 3, "fixed"),
    ("D2", "D2_score_0_3", "digital", 25 / 3, "fixed"),
    ("D3", "D3_score_0_3", "digital", 25 / 3, "fixed"),
]


GROUP_LABELS = {
    "credit": "Chất lượng tín dụng",
    "capital": "Vốn và nguồn vốn",
    "profitability": "Sinh lời và hiệu quả",
    "digital": "Chuyển đổi số",
}


DIGITAL_CODES = (
    "D1",
    "D2",
    "D3",
)


def load_inputs(
    financial_path=None,
    digital_path=None,
    year=2025,
):
    """
    Đọc dữ liệu tài chính và dữ liệu D1–D3,
    kiểm tra đủ 5 ngân hàng rồi merge one-to-one.
    """

    financial_path = (
        Path(financial_path)
        if financial_path
        else ROOT / "output" / "credit_data.xlsx"
    )

    digital_path = (
        Path(digital_path)
        if digital_path
        else ROOT / "digital_dataset_equal_2025.csv"
    )

    # -----------------------------
    # Đọc financial
    # -----------------------------
    if financial_path.suffix.lower() in {
        ".xlsx",
        ".xls",
    }:
        finance = pd.read_excel(
            financial_path,
            sheet_name="BCDS_Metrics",
        )
    else:
        finance = pd.read_csv(
            financial_path
        )

    # -----------------------------
    # Đọc digital
    # -----------------------------
    digital = pd.read_csv(
        digital_path
    )

    # -----------------------------
    # Kiểm tra cột year
    # -----------------------------
    if "year" not in finance.columns:
        raise ValueError(
            "Financial dataset thiếu cột year."
        )

    if "year" not in digital.columns:
        raise ValueError(
            "Digital dataset thiếu cột year."
        )

    finance = finance.loc[
        finance["year"].eq(year)
    ].copy()

    digital = digital.loc[
        digital["year"].eq(year)
    ].copy()

    # -----------------------------
    # Kiểm tra khóa ngân hàng
    # -----------------------------
    for label, frame, key in [
        (
            "financial",
            finance,
            "ticker",
        ),
        (
            "digital",
            digital,
            "bank_code",
        ),
    ]:
        if key not in frame.columns:
            raise ValueError(
                f"{label}: thiếu cột khóa {key}."
            )

        if frame[key].duplicated().any():
            duplicated = (
                frame.loc[
                    frame[key].duplicated(
                        keep=False
                    ),
                    key,
                ]
                .astype(str)
                .tolist()
            )

            raise ValueError(
                f"{label}: duplicate bank/year keys: "
                f"{duplicated}"
            )

        received = set(
            frame[key]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        expected = set(BANKS)

        if received != expected:
            raise ValueError(
                f"{label}: expected {BANKS}; "
                f"received {sorted(received)}"
            )

    # Chuẩn hóa mã trước khi merge
    finance["ticker"] = (
        finance["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    digital["bank_code"] = (
        digital["bank_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # -----------------------------
    # Kiểm tra D1–D3
    # -----------------------------
    required_digital_columns = {
        "bank_code",
        "year",
        "included_in_BCDS_15",
    }

    for code in DIGITAL_CODES:
        required_digital_columns.update(
            {
                f"{code}_score_0_3",
                f"{code}_status",
                f"{code}_rubric_rule",
                f"{code}_score_rationale",
            }
        )

    missing_digital_columns = (
        required_digital_columns
        - set(digital.columns)
    )

    if missing_digital_columns:
        raise ValueError(
            "Digital dataset thiếu các cột bắt buộc: "
            f"{sorted(missing_digital_columns)}"
        )

    # D1–D3 là thành phần chính thức
    # của bộ 15 tiêu chí.
    included = (
        digital["included_in_BCDS_15"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valid_true = included.isin(
        {
            "true",
            "1",
            "yes",
        }
    )

    if not valid_true.all():
        bad_banks = digital.loc[
            ~valid_true,
            "bank_code",
        ].tolist()

        raise ValueError(
            "D1-D3 phải được xác nhận là thành phần "
            "của bộ BCDS 15 tiêu chí. "
            f"Kiểm tra included_in_BCDS_15 của: "
            f"{bad_banks}"
        )

    # -----------------------------
    # Merge
    # -----------------------------
    merged = finance.merge(
        digital,
        left_on=[
            "ticker",
            "year",
        ],
        right_on=[
            "bank_code",
            "year",
        ],
        how="inner",
        validate="one_to_one",
    )

    if len(merged) != len(BANKS):
        raise ValueError(
            "Merge financial + digital không tạo "
            "đủ 5 ngân hàng."
        )

    return (
        merged
        .set_index("ticker")
        .loc[BANKS]
        .reset_index()
    )


def _validate_digital_evidence(
    raw: pd.DataFrame,
):
    """
    Kiểm tra dữ liệu D1–D3 trước khi chấm điểm.
    """

    for code in DIGITAL_CODES:
        status_col = f"{code}_status"
        rubric_col = f"{code}_rubric_rule"
        rationale_col = (
            f"{code}_score_rationale"
        )

        statuses = (
            raw[status_col]
            .fillna("missing")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        if statuses.eq("missing").any():
            banks = raw.loc[
                statuses.eq("missing"),
                "ticker",
            ].tolist()

            raise ValueError(
                f"{code}: thiếu digital evidence "
                f"ở {banks}; không thể tạo ranking "
                "đủ 15 tiêu chí."
            )

        # Bản ghi có điểm phải có rubric.
        missing_rubric = (
            raw[rubric_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if missing_rubric.any():
            banks = raw.loc[
                missing_rubric,
                "ticker",
            ].tolist()

            raise ValueError(
                f"{code}: thiếu rubric_rule "
                f"ở {banks}."
            )

        # Bản ghi có điểm phải có lý do chấm.
        missing_rationale = (
            raw[rationale_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if missing_rationale.any():
            banks = raw.loc[
                missing_rationale,
                "ticker",
            ].tolist()

            raise ValueError(
                f"{code}: thiếu score_rationale "
                f"ở {banks}."
            )

        # Một tiêu chí phải dùng cùng 1 rubric
        # cho toàn bộ ngân hàng.
        rubric_count = (
            raw[rubric_col]
            .astype(str)
            .str.strip()
            .nunique()
        )

        if rubric_count != 1:
            raise ValueError(
                f"{code}: rubric không đồng nhất "
                "giữa các ngân hàng."
            )


def score_banks(
    financial_path=None,
    digital_path=None,
    year=2025,
):
    """
    Tính điểm BCDS cho 5 ngân hàng.
    """

    raw = load_inputs(
        financial_path,
        digital_path,
        year,
    )

    # -----------------------------
    # Kiểm tra tổng trọng số
    # -----------------------------
    total_weight = sum(
        criterion[3]
        for criterion in CRITERIA
    )

    if not np.isclose(
        total_weight,
        100.0,
    ):
        raise ValueError(
            f"Weights must sum to 100; "
            f"received {total_weight}"
        )

    # -----------------------------
    # Kiểm tra D1–D3
    # -----------------------------
    _validate_digital_evidence(
        raw
    )

    detail_rows = []
    skipped = []

    # -----------------------------
    # Chấm từng tiêu chí
    # -----------------------------
    for (
        code,
        column,
        group,
        weight,
        direction,
    ) in CRITERIA:

        if column not in raw.columns:
            raise ValueError(
                f"{code}: thiếu cột {column}."
            )

        values = pd.to_numeric(
            raw[column],
            errors="coerce",
        )

        if values.isna().any():
            bad_banks = raw.loc[
                values.isna(),
                "ticker",
            ].tolist()

            raise ValueError(
                f"{code}: missing/invalid values "
                f"ở {bad_banks}; "
                "không thay NA bằng 0."
            )

        # -----------------------------
        # D1–D3
        # -----------------------------
        if direction == "fixed":
            if (
                ~values.isin(
                    [
                        0,
                        1,
                        2,
                        3,
                    ]
                )
            ).any():
                raise ValueError(
                    f"{code}: score phải thuộc "
                    "0, 1, 2, 3."
                )

            normalized = (
                values / 3
            )

        # -----------------------------
        # Financial Min-Max
        # -----------------------------
        else:
            minimum = values.min()
            maximum = values.max()

            span = (
                maximum
                - minimum
            )

            # Không có khả năng phân biệt
            # giữa các ngân hàng.
            if np.isclose(
                span,
                0,
            ):
                skipped.append(
                    code
                )
                continue

            if direction == "high":
                normalized = (
                    values
                    - minimum
                ) / span

            elif direction == "low":
                normalized = (
                    maximum
                    - values
                ) / span

            else:
                raise ValueError(
                    f"{code}: direction "
                    f"không hợp lệ: {direction}"
                )

        # -----------------------------
        # Lưu bảng chi tiết
        # -----------------------------
        for i, bank in raw.iterrows():
            row = {
                "ticker": bank[
                    "ticker"
                ],
                "bank": bank[
                    "bank"
                ],
                "year": int(year),
                "criterion": code,
                "group": group,
                "group_label": (
                    GROUP_LABELS[group]
                ),
                "raw_value": float(
                    values.iloc[i]
                ),
                "normalized_0_1": float(
                    normalized.iloc[i]
                ),
                "base_weight": float(
                    weight
                ),
                "direction": direction,
            }

            if group == "digital":
                row["status"] = bank[
                    f"{code}_status"
                ]

                row[
                    "rubric_rule"
                ] = bank[
                    f"{code}_rubric_rule"
                ]

                row[
                    "score_rationale"
                ] = bank[
                    f"{code}_score_rationale"
                ]

            else:
                row["status"] = (
                    "provided"
                )

                row[
                    "rubric_rule"
                ] = ""

                row[
                    "score_rationale"
                ] = ""

            detail_rows.append(
                row
            )

    detail = pd.DataFrame(
        detail_rows
    )

    if detail.empty:
        raise ValueError(
            "Không còn tiêu chí hợp lệ "
            "để tính điểm."
        )

    # --------------------------------------------------
    # Nếu một financial indicator có max = min,
    # tiêu chí đó được loại vì không có khả năng
    # phân biệt. Trọng số các tiêu chí còn lại
    # được tái chuẩn hóa về 100.
    # --------------------------------------------------
    active_weights = (
        detail[
            [
                "criterion",
                "base_weight",
            ]
        ]
        .drop_duplicates(
            subset=["criterion"]
        )
    )

    active_weight = (
        active_weights[
            "base_weight"
        ].sum()
    )

    if (
        pd.isna(active_weight)
        or active_weight <= 0
    ):
        raise ValueError(
            "Tổng trọng số tiêu chí "
            "đang hoạt động không hợp lệ."
        )

    detail[
        "effective_weight"
    ] = (
        detail["base_weight"]
        * 100
        / active_weight
    )

    detail[
        "weighted_score"
    ] = (
        detail[
            "normalized_0_1"
        ]
        * detail[
            "effective_weight"
        ]
    )

    # --------------------------------------------------
    # Điểm theo nhóm
    # --------------------------------------------------
    groups = (
        detail.groupby(
            [
                "ticker",
                "bank",
                "year",
                "group",
                "group_label",
            ],
            as_index=False,
        )
        .agg(
            group_score=(
                "weighted_score",
                "sum",
            ),
            group_max=(
                "effective_weight",
                "sum",
            ),
        )
    )

    groups[
        "group_score_100"
    ] = np.where(
        groups["group_max"] > 0,
        (
            groups[
                "group_score"
            ]
            / groups[
                "group_max"
            ]
            * 100
        ),
        np.nan,
    )

    groups[
        "group_score"
    ] = groups[
        "group_score"
    ].round(4)

    groups[
        "group_max"
    ] = groups[
        "group_max"
    ].round(4)

    groups[
        "group_score_100"
    ] = groups[
        "group_score_100"
    ].round(4)

    # --------------------------------------------------
    # Tổng điểm
    # --------------------------------------------------
    totals = (
        detail.groupby(
            [
                "ticker",
                "bank",
                "year",
            ],
            as_index=False,
        )
        .agg(
            total_score=(
                "weighted_score",
                "sum",
            )
        )
    )

    totals[
        "total_score"
    ] = totals[
        "total_score"
    ].round(4)

    totals = (
        totals.sort_values(
            [
                "total_score",
                "ticker",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    totals["rank"] = (
        totals[
            "total_score"
        ]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    # --------------------------------------------------
    # Trạng thái evidence
    # --------------------------------------------------
    statuses = raw[
        [
            "ticker",
            "index_status",
        ]
    ].copy()

    totals = totals.merge(
        statuses,
        on="ticker",
        how="left",
        validate="one_to_one",
    )

    totals[
        "score_status"
    ] = np.where(
        totals[
            "index_status"
        ].eq(
            "verified"
        ),
        "verified",
        "provisional_review",
    )

    return {
        "raw": raw,
        "details": detail,
        "groups": groups,
        "ranking": totals,
        "skipped": skipped,
        "year": int(year),
    }


def export_results(
    result,
    output_dir=None,
):
    """
    Xuất các bảng kết quả và metadata.
    """

    output_dir = (
        Path(output_dir)
        if output_dir
        else OUT
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = [
        (
            "raw",
            "merged_dataset_2025.csv",
        ),
        (
            "details",
            "criterion_scores_2025.csv",
        ),
        (
            "groups",
            "group_scores_2025.csv",
        ),
        (
            "ranking",
            "bank_ranking_2025.csv",
        ),
    ]

    for key, filename in outputs:
        result[key].to_csv(
            output_dir / filename,
            index=False,
            encoding="utf-8-sig",
        )

    active_criteria = (
        result[
            "details"
        ][
            "criterion"
        ]
        .drop_duplicates()
        .tolist()
    )

    metadata = {
        "year": int(
            result.get(
                "year",
                2025,
            )
        ),
        "criteria_count_defined": len(
            CRITERIA
        ),
        "criteria_count_active": len(
            active_criteria
        ),
        "active_criteria": (
            active_criteria
        ),
        "digital_weights": (
            "equal_25_divided_by_3"
        ),
        "financial_normalization": (
            "cross_sectional_min_max"
        ),
        "digital_normalization": (
            "score_0_3_divided_by_3"
        ),
        "skipped_indicators": (
            result[
                "skipped"
            ]
        ),
        "missing_value_rule": (
            "do_not_replace_NA_with_zero"
        ),
        "identical_indicator_rule": (
            "remove_if_max_equals_min_then_"
            "renormalize_remaining_weights_to_100"
        ),
        "digital_evidence_rule": (
            "D1_D2_D3_require_rubric_and_score_rationale"
        ),
        "method": (
            "Min-Max for financial criteria; "
            "score/3 for D1-D3; "
            "weights expressed in percentage points."
        ),
        "disclaimer": (
            "Research comparison only; "
            "this is not a credit rating. "
            "Digital evidence marked review "
            "has not yet been independently verified."
        ),
    }

    (
        output_dir
        / "scoring_metadata.json"
    ).write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_dir


if __name__ == "__main__":
    result = score_banks()

    print(
        result[
            "ranking"
        ].to_string(
            index=False
        )
    )

    print(
        "Skipped indicators:",
        result[
            "skipped"
        ],
    )

    print(
        "Saved to:",
        export_results(
            result
        ),
    )