"""
Tạo bộ dữ liệu chuyển đổi số năm 2025 từ digital_evidence_2025.csv.

Quy tắc:
- 5 ngân hàng: VCB, BID, CTG, TCB, MBB.
- 3 tiêu chí: D1, D2, D3.
- Mỗi tiêu chí có trọng số bằng nhau: 1/3.
- Điểm gốc của từng tiêu chí: 0–3.
- Điểm chuẩn hóa: score_0_3 / 3 * 100.
- Không tự tạo dữ liệu mẫu nếu file evidence bị thiếu.
- rubric_rule và score_rationale phải có đối với bản ghi có điểm.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


BANKS = [
    ("VCB", "Vietcombank"),
    ("BID", "BIDV"),
    ("CTG", "VietinBank"),
    ("TCB", "Techcombank"),
    ("MBB", "MB"),
]

INDICATORS = ("D1", "D2", "D3")

WEIGHTS = {
    key: 1 / len(INDICATORS)
    for key in INDICATORS
}

ALLOWED_STATUSES = {
    "verified",
    "review",
    "missing",
}

REQUIRED_COLUMNS = {
    "bank_code",
    "bank_name",
    "year",
    "indicator_code",
    "score_0_3",
    "score_100",
    "status",
    "rubric_rule",
    "score_rationale",
}


def _prepare_input_file(path: Path) -> Path:
    """
    Kiểm tra file evidence đầu vào.

    Không tự sinh dữ liệu mẫu để tránh trường hợp code âm thầm
    sử dụng một bộ evidence cũ hoặc chưa được xác minh.
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy file đầu vào: {path}\n"
            "Hãy đặt digital_evidence_2025.csv cạnh file "
            "digital_data_equal.py hoặc truyền đường dẫn bằng --input."
        )

    return path


def _read_rows(path: Path):
    """
    Đọc CSV và kiểm tra các cột bắt buộc.
    """
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)

        fieldnames = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - fieldnames

        if missing_columns:
            raise ValueError(
                "digital_evidence_2025.csv thiếu các cột bắt buộc: "
                f"{sorted(missing_columns)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("digital_evidence_2025.csv không có dữ liệu.")

    return rows


def _parse_score(value, status, key):
    """
    Kiểm tra điểm 0–3.
    """
    value = str(value or "").strip()

    if value.upper() in {"", "NA", "N/A", "NULL"}:
        if status == "verified":
            raise ValueError(
                f"{key}: status=verified nhưng không có điểm."
            )
        return None

    try:
        score = int(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"{key}: điểm phải là số nguyên 0, 1, 2, 3 hoặc NA."
        ) from None

    if str(score) != value or not 0 <= score <= 3:
        raise ValueError(
            f"{key}: điểm phải là số nguyên 0..3, nhận {value!r}."
        )

    if status == "missing":
        raise ValueError(
            f"{key}: status=missing thì score_0_3 phải để NA."
        )

    return score


def _validate_score_100(value, score, key):
    """
    Kiểm tra score_100 có nhất quán với score_0_3 hay không.
    """
    if score is None:
        return

    value = str(value or "").strip()

    if value.upper() in {"", "NA", "N/A", "NULL"}:
        raise ValueError(
            f"{key}: đã có score_0_3 nhưng thiếu score_100."
        )

    try:
        score_100 = float(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"{key}: score_100 phải là số."
        ) from None

    expected = round(score / 3 * 100, 2)

    if abs(score_100 - expected) > 0.02:
        raise ValueError(
            f"{key}: score_100={score_100} không khớp "
            f"score_0_3={score}. Giá trị đúng phải là {expected}."
        )


def build_dataset(records):
    """
    Tạo dataset tổng hợp D1–D3 cho 5 ngân hàng.
    """
    expected_banks = {bank for bank, _ in BANKS}

    by_key = {}
    rubric_by_indicator = defaultdict(set)

    for row in records:
        bank_code = row["bank_code"].strip().upper()
        indicator = row["indicator_code"].strip().upper()
        key = (bank_code, indicator)

        if bank_code not in expected_banks:
            raise ValueError(
                f"{key}: mã ngân hàng không hợp lệ."
            )

        if indicator not in INDICATORS:
            raise ValueError(
                f"{key}: mã tiêu chí không hợp lệ."
            )

        if key in by_key:
            raise ValueError(
                f"Trùng bản ghi {key}."
            )

        if row["year"].strip() != "2025":
            raise ValueError(
                f"{key}: yêu cầu dữ liệu năm 2025."
            )

        status = row["status"].strip().lower()

        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"{key}: status phải thuộc "
                f"{sorted(ALLOWED_STATUSES)}."
            )

        score = _parse_score(
            row["score_0_3"],
            status,
            key,
        )

        _validate_score_100(
            row["score_100"],
            score,
            key,
        )

        source_url = row.get(
            "source_url",
            "",
        ).strip()

        rubric_rule = row.get(
            "rubric_rule",
            "",
        ).strip()

        score_rationale = row.get(
            "score_rationale",
            "",
        ).strip()

        if status == "verified" and not source_url:
            raise ValueError(
                f"{key}: điểm verified phải có source_url."
            )

        # Nếu đã chấm điểm thì bắt buộc phải giải thích
        # tiêu chuẩn và lý do chấm.
        if score is not None:
            if not rubric_rule:
                raise ValueError(
                    f"{key}: thiếu rubric_rule."
                )

            if not score_rationale:
                raise ValueError(
                    f"{key}: thiếu score_rationale."
                )

            rubric_by_indicator[indicator].add(
                rubric_rule
            )

        by_key[key] = {
            "score": score,
            "status": status,
            "rubric_rule": rubric_rule,
            "score_rationale": score_rationale,
        }

    # -------------------------------------------------
    # Kiểm tra đủ 5 ngân hàng × 3 tiêu chí = 15 bản ghi
    # -------------------------------------------------
    expected_pairs = {
        (bank, indicator)
        for bank in expected_banks
        for indicator in INDICATORS
    }

    actual_pairs = set(by_key)

    if actual_pairs != expected_pairs:
        missing = sorted(
            expected_pairs - actual_pairs
        )

        strange = sorted(
            actual_pairs - expected_pairs
        )

        raise ValueError(
            f"Thiếu bản ghi: {missing}; "
            f"bản ghi lạ: {strange}"
        )

    # -------------------------------------------------
    # Một tiêu chí phải dùng cùng một rubric
    # cho tất cả ngân hàng.
    # -------------------------------------------------
    for indicator in INDICATORS:
        rules = rubric_by_indicator[indicator]

        if len(rules) != 1:
            raise ValueError(
                f"{indicator}: rubric_rule không đồng nhất "
                f"giữa các ngân hàng."
            )

    # -------------------------------------------------
    # Tạo dataset đầu ra
    # -------------------------------------------------
    output = []

    for bank_code, bank_name in BANKS:
        record = {
            "bank_code": bank_code,
            "bank_name": bank_name,
            "year": 2025,
        }

        all_scores = []
        statuses = []

        for indicator in INDICATORS:
            data = by_key[
                (bank_code, indicator)
            ]

            score = data["score"]

            statuses.append(
                data["status"]
            )

            record[
                f"{indicator}_score_0_3"
            ] = (
                score
                if score is not None
                else "NA"
            )

            record[
                f"{indicator}_score_100"
            ] = (
                round(
                    score / 3 * 100,
                    2,
                )
                if score is not None
                else "NA"
            )

            record[
                f"{indicator}_status"
            ] = data["status"]

            # Giữ lại rubric và lý do chấm
            # để downstream/dashboard có thể sử dụng.
            record[
                f"{indicator}_rubric_rule"
            ] = data["rubric_rule"]

            record[
                f"{indicator}_score_rationale"
            ] = data["score_rationale"]

            if score is not None:
                all_scores.append(score)

        complete = (
            len(all_scores)
            == len(INDICATORS)
        )

        record[
            "complete_3_indicators"
        ] = complete

        # Tổng điểm thô D1 + D2 + D3,
        # tối đa 9 điểm.
        record[
            "total_score_0_9"
        ] = (
            sum(all_scores)
            if complete
            else "NA"
        )

        record[
            "weighting_rule"
        ] = "equal_1_3_each"

        # D1 = D2 = D3 = 1/3.
        record[
            "digital_maturity_100"
        ] = (
            round(
                sum(
                    (
                        score / 3
                    )
                    * WEIGHTS[indicator]
                    for indicator, score
                    in zip(
                        INDICATORS,
                        all_scores,
                    )
                )
                * 100,
                2,
            )
            if complete
            else "NA"
        )

        if not complete:
            record[
                "index_status"
            ] = "incomplete"

        elif any(
            status != "verified"
            for status in statuses
        ):
            record[
                "index_status"
            ] = "review"

        else:
            record[
                "index_status"
            ] = "verified"

        # D1, D2, D3 là 3 tiêu chí chính thức
        # trong bộ 15 tiêu chí BCDS.
        record[
            "included_in_BCDS_15"
        ] = True

        output.append(record)

    return output


def run(input_path: Path, output_path: Path):
    """
    Đọc evidence, kiểm tra dữ liệu và xuất dataset D1–D3.
    """
    records = _read_rows(
        input_path
    )

    rows = build_dataset(
        records
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as fh:

        writer = csv.DictWriter(
            fh,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"OK: {len(rows)} ngân hàng, "
        f"D1/D2/D3 đều có trọng số 1/3 "
        f"-> {output_path}"
    )

    for row in rows:
        print(
            f"  {row['bank_code']:3} "
            f"D1={row['D1_score_0_3']} "
            f"D2={row['D2_score_0_3']} "
            f"D3={row['D3_score_0_3']} "
            f"| chỉ số số={row['digital_maturity_100']} "
            f"| {row['index_status']}"
        )

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    here = Path(
        __file__
    ).resolve().parent

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "CSV evidence đầu vào "
            "(mặc định: digital_evidence_2025.csv "
            "cạnh file .py)"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=(
            here
            / "digital_dataset_equal_2025.csv"
        ),
    )

    args = parser.parse_args()

    input_path = (
        args.input
        if args.input is not None
        else here
        / "digital_evidence_2025.csv"
    )

    input_path = _prepare_input_file(
        input_path
    )

    run(
        input_path,
        args.output,
    )