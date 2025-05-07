import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---- Định nghĩa các thông số ----
INPUT_CSV_PATH = r"D:\python project\report\csv\result.csv"
OUTPUT_DIR_ALL_PLAYERS = r"D:\python project\report\histograms\all players"
OUTPUT_DIR_ALL_TEAMS = r"D:\python project\report\histograms\all teams"

# Chỉ số tấn công và phòng thủ
ATTACKING_METRICS = ["Gls", "Ast", "xG"]
DEFENSIVE_METRICS = ["Tkl", "Int", "Blocks"]
ALL_METRICS = ATTACKING_METRICS + DEFENSIVE_METRICS


# ---- Hàm tạo và lưu histogram ----
def plot_histogram(data, metric, title, output_path, bins=20):
    """Vẽ và lưu histogram cho một chỉ số."""
    plt.figure(figsize=(10, 6))
    sns.histplot(data=data, x=metric, bins=bins, kde=True, color='skyblue')
    plt.title(title, fontsize=14)
    plt.xlabel(metric, fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Lưu biểu đồ
    try:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Đã lưu biểu đồ: {output_path}")
    except Exception as e:
        print(f"Lỗi khi lưu biểu đồ {output_path}: {e}")
    plt.close()


# ---- Hàm tạo histogram cho toàn bộ cầu thủ ----
def plot_histograms_all_players(df, output_dir):
    """Vẽ histogram cho toàn bộ cầu thủ."""
    os.makedirs(output_dir, exist_ok=True)

    for metric in ALL_METRICS:
        if metric in df.columns:
            output_path = os.path.join(output_dir, f"{metric}_all_players.png")
            title = f"Phân bố {metric} - Tất cả cầu thủ"
            plot_histogram(df, metric, title, output_path)
        else:
            print(f"Cảnh báo: Cột {metric} không tồn tại trong dữ liệu.")


# ---- Hàm tạo histogram cho từng đội ----
def plot_histograms_per_team(df, output_dir):
    """Vẽ histogram cho từng đội bóng."""
    os.makedirs(output_dir, exist_ok=True)

    # Lấy danh sách các đội
    teams = df['Team'].unique()

    for team in teams:
        team_data = df[df['Team'] == team]
        team_dir = os.path.join(output_dir, team.replace(" ", "_"))
        os.makedirs(team_dir, exist_ok=True)

        for metric in ALL_METRICS:
            if metric in team_data.columns:
                output_path = os.path.join(team_dir, f"{metric}_{team.replace(' ', '_')}.png")
                title = f"Phân bố {metric} - Đội {team}"
                plot_histogram(team_data, metric, title, output_path)
            else:
                print(f"Cảnh báo: Cột {metric} không tồn tại trong dữ liệu của đội {team}.")


# ---- Hàm chính ----
def main():
    # Đọc file CSV
    try:
        df = pd.read_csv(INPUT_CSV_PATH, encoding="utf-8-sig")
        print(f"Đã đọc file CSV: {INPUT_CSV_PATH}")
        print(f"Số dòng: {df.shape[0]}, S nah cột: {df.shape[1]}")
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        return

    # Kiểm tra các cột cần thiết
    missing_columns = [col for col in ALL_METRICS if col not in df.columns]
    if missing_columns:
        print(f"Cảnh báo: Các cột không tồn tại trong dữ liệu: {missing_columns}")

    # Kiểm tra cột 'Team'
    if 'Team' not in df.columns:
        print("Lỗi: Cột 'Team' không tồn tại trong dữ liệu.")
        return

    # Loại bỏ giá trị NaN cho các chỉ số
    df[ALL_METRICS] = df[ALL_METRICS].fillna(0)

    # Vẽ histogram cho toàn bộ cầu thủ
    print("\nĐang tạo histogram cho toàn bộ cầu thủ...")
    plot_histograms_all_players(df, OUTPUT_DIR_ALL_PLAYERS)

    # Vẽ histogram cho từng đội
    print("\nĐang tạo histogram cho từng đội...")
    plot_histograms_per_team(df, OUTPUT_DIR_ALL_TEAMS)

    print("\nHoàn tất! Tất cả biểu đồ đã được lưu.")


# ---- Điểm vào chính ----
if __name__ == "__main__":
    main()