import pandas as pd
import os
from collections import Counter

# Đường dẫn file CSV và file kết quả
csv_file = r'D:\python project\report\csv\result.csv'
output_dir = r'D:\python project\report\txt'
output_file = os.path.join(output_dir, 'best_performent.txt')

# Đọc file CSV
try:
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"Đã đọc file CSV: {csv_file}")
    print(f"Số dòng: {df.shape[0]}, Số cột: {df.shape[1]}")
except FileNotFoundError:
    print(f"Không tìm thấy file {csv_file}. Vui lòng kiểm tra đường dẫn.")
    exit()
except Exception as e:
    print(f"Lỗi khi đọc file CSV: {e}")
    exit()

# Danh sách các chỉ số tích cực
positive_metrics = [
    'Gls', 'Ast', 'xG', 'xAG', 'PrgC', 'PrgP', 'PrgR', 'Gls per 90', 'Ast per 90', 'xG per 90', 'xAG per 90',
    'SCA', 'SCA90', 'GCA', 'GCA90', 'SoT%', 'SoT per 90', 'G per Sh', 'Cmp', 'Cmp%', 'TotDist', 'ShortCmp%',
    'MedCmp%', 'LongCmp%', 'KP', 'Pass into 1_3', 'PPA', 'CrsPA', 'Tkl', 'TklW', 'Blocks', 'Int', 'Recov',
    'Aerl Won', 'Aerl Won%', 'Touches', 'Def Pen', 'Def 3rd', 'Mid 3rd', 'Att 3rd', 'Att Pen', 'Take-Ons Att',
    'Succ%', 'Carries', 'ProDist', 'Carries 1_3', 'CPA', 'Rec', 'Rec PrgR', 'Sh', 'Pass', 'Fld', 'Crs',
    'Save%', 'CS%', 'PK Save%'
]


# Tính tổng các chỉ số theo đội
def calculate_team_metrics(df, metrics):
    """Tính tổng các chỉ số cho mỗi đội."""
    # Kiểm tra các cột cần thiết
    missing_columns = [col for col in metrics if col not in df.columns]
    if missing_columns:
        print(f"Cảnh báo: Các cột không tồn tại trong dữ liệu: {missing_columns}")

    if 'Team' not in df.columns:
        raise ValueError("Cột 'Team' không tồn tại trong dữ liệu.")

    # Chuyển đổi các cột chỉ số sang kiểu số, thay thế giá trị không hợp lệ bằng 0
    df_metrics = df[metrics].apply(pd.to_numeric, errors='coerce').fillna(0)
    df_metrics['Team'] = df['Team']

    # Tổng hợp dữ liệu theo đội
    team_metrics = df_metrics.groupby('Team')[metrics].sum().reset_index()
    return team_metrics


# Xác định đội có giá trị cao nhất cho từng chỉ số
def find_top_team_per_metric(team_metrics, metrics):
    """Xác định đội có giá trị cao nhất cho từng chỉ số."""
    top_teams = {}
    for metric in metrics:
        if metric in team_metrics.columns:
            max_value = team_metrics[metric].max()
            top_team = team_metrics[team_metrics[metric] == max_value]['Team'].iloc[0]
            top_teams[metric] = {'team': top_team, 'value': max_value}
    return top_teams


# Lưu kết quả vào file txt
def save_results_to_txt(top_teams, team_leader_count, best_team, best_team_count):
    """Lưu kết quả phân tích vào file txt."""
    os.makedirs(output_dir, exist_ok=True)

    output_content = "Phân tích đội có điểm số cao nhất cho từng chỉ số tích cực - Premier League 2024–2025\n"
    output_content += "=" * 80 + "\n\n"

    # 1. Đội dẫn đầu cho từng chỉ số
    output_content += "1. Đội dẫn đầu cho từng chỉ số tích cực:\n"
    for metric, info in top_teams.items():
        output_content += f"- {metric}: {info['team']} ({info['value']:.2f})\n"

    # 2. Đội thể hiện tốt nhất
    output_content += "\n2. Đội thể hiện tốt nhất:\n"
    output_content += f"Đội {best_team} dẫn đầu trong {best_team_count} chỉ số tích cực, thể hiện phong độ xuất sắc nhất tại Premier League 2024–2025.\n"

    # 3. Danh sách các đội và số chỉ số dẫn đầu
    output_content += "\n3. Danh sách các đội và số chỉ số tích cực dẫn đầu:\n"
    for team, count in sorted(team_leader_count.items(), key=lambda x: x[1], reverse=True):
        output_content += f"- {team}: {count} chỉ số\n"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Kết quả đã được lưu vào {output_file}")
    except Exception as e:
        print(f"Lỗi khi ghi file: {e}")

    # In kết quả ra console để kiểm tra
    print(output_content)


# Hàm chính
def main():
    # Tính tổng các chỉ số theo đội
    try:
        team_metrics = calculate_team_metrics(df, positive_metrics)
    except ValueError as e:
        print(f"Lỗi: {e}")
        return

    # Xác định đội dẫn đầu cho từng chỉ số
    top_teams = find_top_team_per_metric(team_metrics, positive_metrics)

    # Đếm số lần mỗi đội dẫn đầu
    team_leader_count = Counter([info['team'] for info in top_teams.values()])

    # Xác định đội thể hiện tốt nhất
    best_team = max(team_leader_count, key=team_leader_count.get)
    best_team_count = team_leader_count[best_team]

    # Lưu kết quả
    save_results_to_txt(top_teams, team_leader_count, best_team, best_team_count)


# Điểm vào chính
if __name__ == "__main__":
    main()