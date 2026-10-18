"""
Đọc các file output đã được pipeline xuất sẵn.

Dashboard tuyệt đối không import hoặc chạy lại pipeline/scoring.
Nếu dữ liệu đầu vào không hợp lệ, module sẽ báo DataIssue
để giao diện Streamlit hiển thị lỗi rõ ràng.
"""

from pathlib import Path
import json

import pandas as pd
import streamlit as st

from config import (
    BANKS,
    DIGITAL_CODES,
    PROJECT_ROOT,
    YEAR,
)


class DataIssue(ValueError):
    """Lỗi dữ liệu có thể hiển thị trực tiếp trên Dashboard."""


# =========================================================
# Định nghĩa file, cột bắt buộc và khóa duy nhất
# =========================================================

SPECS = {
    "ranking": (
        "output/bank_ranking_2025.csv",
        (
            "ticker",
            "bank",
            "year",
            "total_score",
            "rank",
            "index_status",
            "score_status",
        ),
        (
            "ticker",
            "year",
        ),
    ),

    "groups": (
        "output/group_scores_2025.csv",
        (
            "ticker",
            "bank",
            "year",
            "group",
            "group_label",
            "group_score",
            "group_max",
            "group_score_100",
        ),
        (
            "ticker",
            "year",
            "group",
        ),
    ),

    "criteria": (
        "output/criterion_scores_2025.csv",
        (
            "ticker",
            "bank",
            "year",
            "criterion",
            "group",
            "group_label",
            "raw_value",
            "normalized_0_1",
            "base_weight",
            "effective_weight",
            "weighted_score",
            "direction",
            "status",
            "rubric_rule",
            "score_rationale",
        ),
        (
            "ticker",
            "year",
            "criterion",
        ),
    ),

    "merged": (
        "output/merged_dataset_2025.csv",
        (
            "ticker",
            "bank",
            "year",
        ),
        (
            "ticker",
            "year",
        ),
    ),

    "digital": (
        "digital_dataset_equal_2025.csv",
        (
            "bank_code",
            "bank_name",
            "year",

            "D1_score_0_3",
            "D1_score_100",
            "D1_status",
            "D1_rubric_rule",
            "D1_score_rationale",

            "D2_score_0_3",
            "D2_score_100",
            "D2_status",
            "D2_rubric_rule",
            "D2_score_rationale",

            "D3_score_0_3",
            "D3_score_100",
            "D3_status",
            "D3_rubric_rule",
            "D3_score_rationale",

            "digital_maturity_100",
            "index_status",
            "included_in_BCDS_15",
        ),
        (
            "bank_code",
            "year",
        ),
    ),

    "evidence": (
        "digital_evidence_2025.csv",
        (
            "bank_code",
            "year",
            "indicator_code",
            "score_0_3",
            "score_100",
            "status",
            "evidence_text",
            "source_description",
            "source_url",
            "rubric_rule",
            "score_rationale",
        ),
        (
            "bank_code",
            "year",
            "indicator_code",
        ),
    ),

    "financial": (
        "output/credit_data_clean.csv",
        (
            "ticker",
            "bank",
            "year",
            "variable",
            "value_clean",
        ),
        (
            "ticker",
            "year",
            "variable",
        ),
    ),
}


# =========================================================
# Các cột phải có dạng số
# =========================================================

NUMERIC = {
    "ranking": (
        "total_score",
        "rank",
    ),

    "groups": (
        "group_score",
        "group_max",
        "group_score_100",
    ),

    "criteria": (
        "raw_value",
        "normalized_0_1",
        "base_weight",
        "effective_weight",
        "weighted_score",
    ),

    "digital": (
        "D1_score_0_3",
        "D1_score_100",
        "D2_score_0_3",
        "D2_score_100",
        "D3_score_0_3",
        "D3_score_100",
        "digital_maturity_100",
    ),

    "evidence": (
        "score_0_3",
        "score_100",
    ),

    "financial": (
        "value_clean",
    ),
}


ALLOWED_DIGITAL_STATUSES = {
    "verified",
    "review",
    "missing",
}


# =========================================================
# Cache / đọc file
# =========================================================

def file_signature(path):
    """
    Tạo chữ ký file dựa trên đường dẫn,
    thời gian sửa và kích thước.

    Khi file thay đổi, Streamlit cache sẽ tự invalid.
    """
    path = Path(path).resolve()

    try:
        stat = path.stat()

        return (
            str(path),
            stat.st_mtime_ns,
            stat.st_size,
        )

    except OSError as exc:
        raise DataIssue(
            f"Không tìm thấy hoặc không đọc được {path.name}. "
            "Hãy kiểm tra output đã được xuất. "
            "Nếu chưa có, hãy chạy pipeline riêng "
            "trước khi mở Dashboard."
        ) from exc


@st.cache_data(
    show_spinner=False,
    max_entries=48,
)
def _read_csv(
    path,
    modified_ns,
    size,
):
    """
    Các tham số signature tham gia cache invalidation.
    """
    return pd.read_csv(
        path,
        encoding="utf-8-sig",
    )


@st.cache_data(
    show_spinner=False,
    max_entries=8,
)
def _read_json(
    path,
    modified_ns,
    size,
):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8-sig"
        )
    )


@st.cache_data(
    show_spinner=False,
    max_entries=12,
)
def _read_sheet(
    path,
    modified_ns,
    size,
    sheet,
):
    return pd.read_excel(
        path,
        sheet_name=sheet,
        engine="openpyxl",
    )


# =========================================================
# Validation chung
# =========================================================

def validate_frame(
    frame,
    required,
    keys,
    label,
    bank_column="ticker",
    financial=False,
):
    """
    Kiểm tra:
    - cột bắt buộc;
    - dataset rỗng;
    - khóa thiếu;
    - duplicate;
    - tập 5 ngân hàng;
    - năm dữ liệu.
    """

    absent = (
        set(required)
        - set(frame.columns)
    )

    if absent:
        raise DataIssue(
            f"{label}: thiếu cột bắt buộc: "
            f"{', '.join(sorted(absent))}."
        )

    if frame.empty:
        raise DataIssue(
            f"{label}: không có dữ liệu."
        )

    if frame[
        list(keys)
    ].isna().any().any():
        raise DataIssue(
            f"{label}: khóa định danh bị thiếu."
        )

    if frame.duplicated(
        list(keys)
    ).any():
        raise DataIssue(
            f"{label}: trùng khóa "
            f"{', '.join(keys)}."
        )

    # ---------------------------------------------
    # Kiểm tra mã ngân hàng
    # ---------------------------------------------
    if bank_column:
        bank_values = set(
            frame[
                bank_column
            ]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        expected_banks = {
            str(bank)
            .strip()
            .upper()
            for bank in BANKS
        }

        if bank_values != expected_banks:
            raise DataIssue(
                f"{label}: tập mã ngân hàng "
                "không khớp dữ liệu nghiên cứu "
                "5 ngân hàng."
            )

    # ---------------------------------------------
    # Kiểm tra năm
    # ---------------------------------------------
    if "year" in frame.columns:
        years = set(
            pd.to_numeric(
                frame["year"],
                errors="coerce",
            )
            .dropna()
            .astype(int)
        )

        if YEAR not in years:
            raise DataIssue(
                f"{label}: không có dữ liệu "
                f"năm đánh giá {YEAR}."
            )

        # Các file output của scoring phải chỉ
        # chứa đúng năm nghiên cứu.
        if (
            not financial
            and years != {YEAR}
        ):
            raise DataIssue(
                f"{label}: dữ liệu chứa năm "
                f"khác năm đánh giá {YEAR}."
            )

    return frame


# =========================================================
# Validation riêng cho digital
# =========================================================

def _validate_digital_dataset(
    frame,
    relative,
):
    """
    Kiểm tra dataset D1/D2/D3 sau khi tổng hợp.
    """

    # D1-D3 phải chính thức nằm trong bộ BCDS 15.
    included = (
        frame[
            "included_in_BCDS_15"
        ]
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
        bad = frame.loc[
            ~valid_true,
            "bank_code",
        ].tolist()

        raise DataIssue(
            f"{relative}: "
            "included_in_BCDS_15 phải là True "
            f"cho D1-D3. Kiểm tra: {bad}."
        )

    for code in DIGITAL_CODES:
        score_col = (
            f"{code}_score_0_3"
        )

        status_col = (
            f"{code}_status"
        )

        rubric_col = (
            f"{code}_rubric_rule"
        )

        rationale_col = (
            f"{code}_score_rationale"
        )

        # Điểm 0–3
        scores = pd.to_numeric(
            frame[score_col],
            errors="coerce",
        )

        if (
            scores.isna().any()
            or not scores.isin(
                [
                    0,
                    1,
                    2,
                    3,
                ]
            ).all()
        ):
            raise DataIssue(
                f"{relative}: {score_col} "
                "phải thuộc thang 0–3."
            )

        # Status
        statuses = (
            frame[
                status_col
            ]
            .fillna("missing")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        invalid_status = (
            ~statuses.isin(
                ALLOWED_DIGITAL_STATUSES
            )
        )

        if invalid_status.any():
            raise DataIssue(
                f"{relative}: {status_col} "
                "có trạng thái không hợp lệ."
            )

        # Dashboard ranking đầy đủ
        # không chấp nhận evidence missing.
        if statuses.eq(
            "missing"
        ).any():
            banks = frame.loc[
                statuses.eq("missing"),
                "bank_code",
            ].tolist()

            raise DataIssue(
                f"{relative}: {code} "
                f"thiếu evidence tại {banks}."
            )

        # Rubric
        missing_rubric = (
            frame[
                rubric_col
            ]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if missing_rubric.any():
            raise DataIssue(
                f"{relative}: {code} "
                "thiếu rubric_rule."
            )

        # Cùng D1/D2/D3 phải dùng
        # cùng một rubric cho 5 ngân hàng.
        if (
            frame[
                rubric_col
            ]
            .astype(str)
            .str.strip()
            .nunique()
            != 1
        ):
            raise DataIssue(
                f"{relative}: {code} "
                "có rubric không đồng nhất "
                "giữa các ngân hàng."
            )

        # Lý do chấm điểm
        missing_rationale = (
            frame[
                rationale_col
            ]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if missing_rationale.any():
            raise DataIssue(
                f"{relative}: {code} "
                "thiếu score_rationale."
            )


def _validate_evidence(
    frame,
    relative,
):
    """
    Kiểm tra file evidence gốc D1–D3.
    """

    indicators = set(
        frame[
            "indicator_code"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    expected = {
        str(code)
        .strip()
        .upper()
        for code in DIGITAL_CODES
    }

    if indicators != expected:
        raise DataIssue(
            f"{relative}: tập D1/D2/D3 "
            "không đầy đủ."
        )

    statuses = (
        frame[
            "status"
        ]
        .fillna("missing")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    if (
        ~statuses.isin(
            ALLOWED_DIGITAL_STATUSES
        )
    ).any():
        raise DataIssue(
            f"{relative}: status "
            "không hợp lệ."
        )

    # Bản ghi đang dùng để chấm điểm
    # phải có rubric và lý do chấm.
    scored = (
        pd.to_numeric(
            frame[
                "score_0_3"
            ],
            errors="coerce",
        )
        .notna()
    )

    for column in (
        "rubric_rule",
        "score_rationale",
    ):
        missing = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        )

        if (
            scored
            & missing
        ).any():
            raise DataIssue(
                f"{relative}: "
                f"bản ghi có điểm nhưng thiếu {column}."
            )

    # Một D-code phải dùng cùng rubric
    # cho tất cả ngân hàng.
    for code in DIGITAL_CODES:
        part = frame.loc[
            frame[
                "indicator_code"
            ]
            .astype(str)
            .str.upper()
            .eq(
                str(code).upper()
            )
        ]

        if (
            part[
                "rubric_rule"
            ]
            .astype(str)
            .str.strip()
            .nunique()
            != 1
        ):
            raise DataIssue(
                f"{relative}: {code} "
                "có rubric không đồng nhất."
            )


# =========================================================
# Load dữ liệu
# =========================================================

def _load(
    kind,
    root=None,
):
    relative, required, keys = (
        SPECS[kind]
    )

    path = (
        Path(
            root
            or PROJECT_ROOT
        )
        / relative
    )

    try:
        frame = _read_csv(
            *file_signature(
                path
            )
        )

        validate_frame(
            frame,
            required,
            keys,
            relative,
            (
                "bank_code"
                if kind
                in (
                    "digital",
                    "evidence",
                )
                else "ticker"
            ),
            financial=(
                kind
                == "financial"
            ),
        )

        # ---------------------------------------------
        # Kiểm tra numeric
        # ---------------------------------------------
        for column in NUMERIC.get(
            kind,
            (),
        ):
            converted = (
                pd.to_numeric(
                    frame[column],
                    errors="coerce",
                )
            )

            original_has_value = (
                frame[column]
                .notna()
            )

            invalid = (
                original_has_value
                & (
                    converted.isna()
                    | np_is_inf(
                        converted
                    )
                )
            )

            if invalid.any():
                raise DataIssue(
                    f"{relative}: "
                    f"cột {column} "
                    "có giá trị số không hợp lệ."
                )

        # ---------------------------------------------
        # Kiểm tra coverage giữa ngân hàng
        # ---------------------------------------------
        if kind in (
            "groups",
            "criteria",
            "evidence",
        ):
            if kind == "evidence":
                bank_key = (
                    "bank_code"
                )

                item_key = (
                    "indicator_code"
                )

            elif kind == "groups":
                bank_key = (
                    "ticker"
                )

                item_key = (
                    "group"
                )

            else:
                bank_key = (
                    "ticker"
                )

                item_key = (
                    "criterion"
                )

            universe = set(
                frame[
                    item_key
                ]
            )

            for _, part in frame.groupby(
                bank_key
            ):
                if set(
                    part[
                        item_key
                    ]
                ) != universe:
                    raise DataIssue(
                        f"{relative}: "
                        "không đồng nhất độ phủ "
                        "tiêu chí/nhóm giữa "
                        "các ngân hàng."
                    )

        # ---------------------------------------------
        # Kiểm tra riêng digital
        # ---------------------------------------------
        if kind == "digital":
            _validate_digital_dataset(
                frame,
                relative,
            )

        elif kind == "evidence":
            _validate_evidence(
                frame,
                relative,
            )

        return frame.copy(
            deep=True
        )

    except DataIssue:
        raise

    except (
        OSError,
        ValueError,
        KeyError,
        UnicodeError,
    ) as exc:
        raise DataIssue(
            f"Không đọc được "
            f"{relative}: {exc}"
        ) from exc


def np_is_inf(series):
    """
    Kiểm tra +inf / -inf mà không cần import numpy.
    """
    return series.isin(
        [
            float("inf"),
            -float("inf"),
        ]
    )


# =========================================================
# Public loaders
# =========================================================

def load_ranking(
    root=None,
):
    return _load(
        "ranking",
        root,
    )


def load_group_scores(
    root=None,
):
    return _load(
        "groups",
        root,
    )


def load_criterion_scores(
    root=None,
):
    return _load(
        "criteria",
        root,
    )


def load_merged_data(
    root=None,
):
    return _load(
        "merged",
        root,
    )


def load_digital_dataset(
    root=None,
):
    return _load(
        "digital",
        root,
    )


def load_digital_evidence(
    root=None,
):
    return _load(
        "evidence",
        root,
    )


def load_financial_sources(
    root=None,
):
    return _load(
        "financial",
        root,
    )


# =========================================================
# Metadata scoring
# =========================================================

def load_scoring_metadata(
    root=None,
):
    path = (
        Path(
            root
            or PROJECT_ROOT
        )
        / "output"
        / "scoring_metadata.json"
    )

    try:
        data = _read_json(
            *file_signature(
                path
            )
        )

        if not isinstance(
            data,
            dict,
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "định dạng không hợp lệ."
            )

        if (
            data.get("year")
            != YEAR
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                f"năm không khớp {YEAR}."
            )

        # scoring_model mới dùng
        # criteria_count_defined và
        # criteria_count_active.
        defined = data.get(
            "criteria_count_defined"
        )

        active = data.get(
            "criteria_count_active"
        )

        if not isinstance(
            defined,
            int,
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "criteria_count_defined "
                "không hợp lệ."
            )

        if defined != 15:
            raise DataIssue(
                "scoring_metadata.json: "
                f"mô hình phải định nghĩa 15 tiêu chí, "
                f"nhận {defined}."
            )

        if not isinstance(
            active,
            int,
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "criteria_count_active "
                "không hợp lệ."
            )

        if (
            active <= 0
            or active > defined
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "số tiêu chí active "
                "không hợp lệ."
            )

        active_criteria = data.get(
            "active_criteria"
        )

        if not isinstance(
            active_criteria,
            list,
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "active_criteria "
                "không hợp lệ."
            )

        if (
            len(
                active_criteria
            )
            != active
        ):
            raise DataIssue(
                "scoring_metadata.json: "
                "criteria_count_active "
                "không khớp active_criteria."
            )

        return data

    except DataIssue:
        raise

    except (
        OSError,
        ValueError,
    ) as exc:
        raise DataIssue(
            "Không đọc được "
            f"scoring_metadata.json: {exc}"
        ) from exc


# =========================================================
# Workbook
# =========================================================

def load_workbook_sheet(
    sheet,
    root=None,
):
    try:
        path = (
            Path(
                root
                or PROJECT_ROOT
            )
            / "output"
            / "credit_data.xlsx"
        )

        return _read_sheet(
            *file_signature(
                path
            ),
            sheet,
        ).copy(
            deep=True
        )

    except DataIssue:
        raise

    except (
        OSError,
        ValueError,
        KeyError,
        ImportError,
    ) as exc:
        raise DataIssue(
            f"Không đọc được "
            f"sheet {sheet}: {exc}"
        ) from exc


# =========================================================
# Helper functions cho Dashboard
# =========================================================

def select_bank(
    frame,
    ticker,
    column="ticker",
):
    values = set(
        frame[
            column
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    ticker_normalized = (
        str(ticker)
        .strip()
        .upper()
    )

    if (
        ticker_normalized
        not in values
    ):
        raise DataIssue(
            f"Mã ngân hàng "
            f"không hợp lệ: {ticker}."
        )

    mask = (
        frame[
            column
        ]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq(
            ticker_normalized
        )
    )

    return frame.loc[
        mask
    ].copy()


def get_bank_summary(
    ticker,
    root=None,
):
    return (
        select_bank(
            load_ranking(
                root
            ),
            ticker,
        )
        .iloc[0]
        .to_dict()
    )


def get_bank_group_scores(
    ticker,
    root=None,
):
    return select_bank(
        load_group_scores(
            root
        ),
        ticker,
    )


def get_bank_criterion_scores(
    ticker,
    root=None,
):
    return select_bank(
        load_criterion_scores(
            root
        ),
        ticker,
    )


def get_digital_evidence(
    ticker,
    root=None,
):
    return select_bank(
        load_digital_evidence(
            root
        ),
        ticker,
        "bank_code",
    )


def filter_criteria(
    frame,
    ticker,
    group=None,
    kind="Tất cả",
):
    selected = select_bank(
        frame,
        ticker,
    )

    if group:
        selected = selected.loc[
            selected[
                "group"
            ].eq(
                group
            )
        ]

    if kind == "Định lượng":
        selected = selected.loc[
            ~selected[
                "criterion"
            ].isin(
                DIGITAL_CODES
            )
        ]

    elif kind == "Định tính":
        selected = selected.loc[
            selected[
                "criterion"
            ].isin(
                DIGITAL_CODES
            )
        ]

    return selected.copy()


def extreme_groups(
    frame,
    column="group_score_100",
    highest=True,
):
    valid = frame.dropna(
        subset=[
            column
        ]
    )

    if valid.empty:
        return []

    extreme = (
        valid[
            column
        ].max()
        if highest
        else valid[
            column
        ].min()
    )

    return (
        valid.loc[
            valid[
                column
            ].eq(
                extreme
            ),
            "group_label",
        ]
        .tolist()
    )


def refresh_data():
    """
    Xóa cache dữ liệu khi người dùng
    bấm refresh trên Dashboard.
    """
    _read_csv.clear()
    _read_json.clear()
    _read_sheet.clear()