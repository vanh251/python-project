import os
import pandas as pd
from collections import Counter

# ---- Định nghĩa các thông số ----
INPUT_CSV_PATH = r"D:\python project\report\csv\result.csv"
OUTPUT_TXT_PATH = r"D:\python project\report\txt\positive_metrics_analysis.txt"

# Chỉ số tích cực
POSITIVE_METRICS = [
    "Gls", "Ast", "xG", "xAG", "PrgC", "PrgP", "PrgR", "Gls per 90", "Ast per 90", "xG per 90", "xAG per 90",
    "SCA", "SCA90", "GCA", "GCA90", "SoT%", "SoT per 90", "G per Sh", "Cmp", "Cmp%", "TotDist", "ShortCmp%",
    "MedCmp%", "LongCmp%", "KP", "Pass into 1_3", "PPA", "CrsPA", "Tkl", "TklW", "Blocks", "Int", "Recov",
    "Aerl Won", "Aerl Won%", "Touches", "Att 3rd", "Att Pen", "Take-Ons Att", "Succ%", "Carries", "ProDist",
    "Carries 1_3", "CPA", "Rec", "Rec PrgR"
]


# ---- Hàm tính tổng chỉ số theo đội ----
def calculate_team_metrics(df):
    """Tính tổng các chỉ số tích cực cho mỗi đội."""
    # Kiểm tra các cột cần thiết
    missing_columns = [col for col in POSITIVE_METRICS if col not in df.columns]
    if missing_columns:
        print(f"Cảnh báo: Các cột không tồn tại trong dữ liệu: {missing_columns}")

    if 'Team' not in df.columns:
        raise ValueError("Cột 'Team' không tồn tại trong dữ liệu.")

    # Tổng hợp dữ liệu theo đội
    team_metrics = df.groupby('Team')[POSITIVE_METRICS].sum().reset_index()
    return team_metrics


# ---- Hàm tìm đội có chỉ số cao nhất ----
def find_top_team_per_metric(team_metrics):
    """Xác định đội có giá trị cao nhất cho từng chỉ số."""
    top_teams = {}
    for metric in POSITIVE_METRICS:
        if metric in team_metrics.columns:
            max_value = team_metrics[metric].max()
            top_team = team_metrics[team_metrics[metric] == max_value]['Team'].iloc[0]
            top_teams[metric] = {'team': top_team, 'value': max_value}
    return top_teams


# ---- Hàm tính điểm tổng hợp ----
def calculate_composite_score(team_metrics):
    """Tính điểm tổng hợp bằng cách chuẩn hóa và cộng các chỉ số."""
    normalized_metrics = team_metrics.copy()
    for metric in POSITIVE_METRICS:
        if metric in normalized_metrics.columns:
            max_val = normalized_metrics[metric].max()
            if max_val > 0:
                normalized_metrics[metric] = normalized_metrics[metric] / max_val

    # Tính tổng điểm
    normalized_metrics['Composite_Score'] = normalized_metrics[POSITIVE_METRICS].sum(axis=1)
    best_team = normalized_metrics.loc[normalized_metrics['Composite_Score'].idxmax()]
    return best_team['Team'], best_team['Composite_Score']


# ---- Hàm lưu kết quả vào file txt ----
def save_results_to_txt(team_metrics, top_teams, best_team_count, best_team_score, best_team_count_num):
    """Lưu kết quả phân tích vào file txt."""
    os.makedirs(os.path.dirname(OUTPUT_TXT_PATH), exist_ok=True)

    with open(OUTPUT_TXT_PATH, 'w', encoding='utf-8') as f:
        f.write("Phân tích chỉ số tích cực - Premier League 2024-2025\n")
        f.write("=" * 50 + "\n\n")

        # 1. Tổng hợp chỉ số của từng đội
        f.write("1. Tổng hợp chỉ số tích cực của từng đội:\n")
        f.write(team_metrics.to_string(index=False, float_format="%.2f"))
        f.write("\n\n")

        # 2. Đội dẫn đầu cho từng chỉ số
        f.write("2. Đội dẫn đầu cho từng chỉ số:\n")
        for metric, info in top_teams.items():
            f.write(f"- {metric}: {info['team']} ({info['value']:.2f})\n")
        f.write("\n")

        # 3. Đội dẫn đầu nhiều chỉ số nhất
        f.write("3. Đội dẫn đầu nhiều chỉ số nhất:\n")
        f.write(f"Đội {best_team_count} dẫn đầu {best_team_count_num} chỉ số.\n")
        f.write("\n")

        # 4. Đội có điểm tổng hợp cao nhất
        f.write("4. Đội có điểm tổng hợp cao nhất:\n")
        f.write(f"Đội {best_team_score} có điểm tổng hợp cao nhất: {best_team_score:.2f}.\n")
        f.write("Điểm tổng hợp được tính bằng cách chuẩn hóa và cộng tất cả chỉ số tích cực.\n")

    print(f"Đã lưu kết quả vào: {OUTPUT_TXT_PATH}")


# ---- Hàm chính ----
def main():
    # Đọc file CSV
    try:
        df = pd.read_csv(INPUT_CSV_PATH, encoding="utf-8-sig")
        print(f"Đã đọc file CSV: {INPUT_CSV_PATH}")
        print(f"Số dòng: {df.shape[0]}, Số cột: {df.shape[1]}")
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        return

    # Tính tổng các chỉ số theo đội
    try:
        team_metrics = calculate_team_metrics(df)
    except ValueError as e:
        print(f"Lỗi: {e}")
        return

    # Xác định đội dẫn đầu cho từng chỉ số
    top_teams = find_top_team_per_metric(team_metrics)

    # Xác định đội dẫn đầu nhiều chỉ số nhất
    team_counts = Counter([info['team'] for info in top_teams.values()])
    best_team_count = team_counts.most_common(1)[0][0]
    best_team_count_num = team_counts[best_team_count]

    # Tính điểm tổng hợp
    best_team_score, composite_score = calculate_composite_score(team_metrics)

    # Lưu kết quả
    try:
        save_results_to_txt(team_metrics, top_teams, best_team_count, best_team_score, best_team_count_num)
    except Exception as e:
        print(f"Lỗi khi lưu file txt: {e}")


# ---- Điểm vào chính ----
if __name__ == "__main__":
    main()