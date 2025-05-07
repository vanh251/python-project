import pandas as pd
import numpy as np # Cần thiết cho np.nan khi xử lý các cột không phải số

def calculate_stats_from_csv(input_csv_path="D:\\python project\\report\\csv\\result.csv",
                             output_csv_path="D:\\python project\\report\\csv\\results2.csv"):
    """
    Đọc file CSV, tính toán trung vị, trung bình, độ lệch chuẩn cho các chỉ số
    trên toàn bộ cầu thủ và cho từng đội, sau đó lưu kết quả vào file CSV mới.

    Args:
        input_csv_path (str): Đường dẫn đến file result.csv đầu vào.
        output_csv_path (str): Đường dẫn để lưu file results2.csv đầu ra.
    """
    try:
        # Đọc file CSV, chỉ định "N/A" là giá trị NaN
        df = pd.read_csv(input_csv_path, na_values="N/A")
        print(f"Đã đọc thành công file: {input_csv_path}")
        print(f"Số dòng: {df.shape[0]}, Số cột: {df.shape[1]}")
        print("\nXem qua 5 dòng đầu của dữ liệu:")
        print(df.head())
        print("\nThông tin kiểu dữ liệu của các cột:")
        print(df.info())

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{input_csv_path}'. Vui lòng kiểm tra lại đường dẫn.")
        return
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        return

    # Xác định các cột chứa chỉ số (thường là các cột kiểu số)
    # Loại bỏ các cột định danh như 'Player', 'Nation', 'Team', 'Position'
    # và các cột có thể không phải dạng số nếu chưa được chuyển đổi đúng
    identifier_columns = ['Player', 'Nation', 'Team', 'Position']
    # Chỉ chọn các cột số để tính toán thống kê
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    # Nếu không có cột số nào, thông báo và thoát
    if not numeric_cols:
        print("Không tìm thấy cột dữ liệu dạng số nào để tính toán thống kê.")
        return

    print(f"\nCác cột số sẽ được tính toán thống kê: {numeric_cols}")

    # Khởi tạo danh sách để lưu kết quả
    results_list = []

    # ---- 1. Tính toán cho tất cả cầu thủ (all) ----
    all_stats = {'Group': 'all'}
    for col in numeric_cols:
        all_stats[f'Median of {col}'] = df[col].median()
        all_stats[f'Mean of {col}'] = df[col].mean()
        all_stats[f'Std of {col}'] = df[col].std()
    results_list.append(all_stats)

    # ---- 2. Tính toán cho từng đội (Team) ----
    if 'Team' in df.columns:
        unique_teams = df['Team'].dropna().unique()
        print(f"\nCác đội sẽ được tính toán: {unique_teams}")

        for team in unique_teams:
            team_df = df[df['Team'] == team]
            team_stats = {'Group': team}
            for col in numeric_cols:
                team_stats[f'Median of {col}'] = team_df[col].median()
                team_stats[f'Mean of {col}'] = team_df[col].mean()
                team_stats[f'Std of {col}'] = team_df[col].std()
            results_list.append(team_stats)
    else:
        print("Cảnh báo: Không tìm thấy cột 'Team' trong dữ liệu. Sẽ không tính toán thống kê theo đội.")

    # Tạo DataFrame từ danh sách kết quả
    results_df = pd.DataFrame(results_list)

    # Đặt cột 'Group' làm cột đầu tiên nếu nó không phải là cột đầu tiên
    if 'Group' in results_df.columns:
        cols = ['Group'] + [col for col in results_df.columns if col != 'Group']
        results_df = results_df[cols]

    # Lưu DataFrame kết quả vào file CSV
    try:
        # Tạo thư mục nếu chưa tồn tại (lấy từ đường dẫn output)
        import os
        output_directory = os.path.dirname(output_csv_path)
        if output_directory: # Nếu đường dẫn có thư mục
             os.makedirs(output_directory, exist_ok=True)

        results_df.to_csv(output_csv_path, index=False, na_rep="N/A", float_format='%.2f')
        print(f"\nĐã lưu kết quả thành công vào file: {output_csv_path}")
        print(f"Số dòng trong file kết quả: {results_df.shape[0]}, Số cột: {results_df.shape[1]}")
    except Exception as e:
        print(f"Lỗi khi lưu file CSV: {e}")

# Chạy chương trình
if __name__ == "__main__":
    # Sử dụng đường dẫn mặc định như trong chương trình cào dữ liệu gốc
    # Bạn có thể thay đổi đường dẫn này nếu cần
    input_file = r"D:\python project\report\csv\result.csv"
    output_file = r"D:\python project\report\csv\results2.csv"
    calculate_stats_from_csv(input_csv_path=input_file, output_csv_path=output_file)

    print("\n--- Chương trình tính toán thống kê đã hoàn tất ---")