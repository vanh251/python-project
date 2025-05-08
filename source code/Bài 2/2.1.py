import pandas as pd
import numpy as np  # Cần thiết cho np.nan
import os


def analyze_player_statistics():
    """
    Đọc dữ liệu cầu thủ từ result.csv, xác định top 3 và bottom 3 cho mỗi chỉ số,
    và lưu kết quả vào top_3.txt trong thư mục report/txt.
    """
    input_csv_path = r"D:\python project\report\csv\result.csv"
    # ---- THAY ĐỔI ĐƯỜNG DẪN OUTPUT ----
    output_directory = r"D:\python project\report\txt"  # Thư mục mới cho file txt
    output_txt_path = os.path.join(output_directory, "top_3.txt")  # Đường dẫn đầy đủ tới file txt
    # ---- KẾT THÚC THAY ĐỔI ĐƯỜNG DẪN ----

    # Đảm bảo thư mục output tồn tại
    try:
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"Đã tạo thư mục: {output_directory}")
    except OSError as e:
        print(f"Lỗi khi tạo thư mục {output_directory}: {e}")
        return

    # Đọc file CSV, xử lý 'N/A' thành NaN
    try:
        player_data_df = pd.read_csv(input_csv_path, na_values="N/A", encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp {input_csv_path}. Hãy đảm bảo Bài 1 đã chạy thành công.")
        return
    except Exception as e:
        print(f"Lỗi khi đọc tệp CSV: {e}")
        return

    if player_data_df.empty:
        print("Tệp result.csv rỗng. Không có dữ liệu để phân tích.")
        with open(output_txt_path, 'w', encoding='utf-8') as f_out:
            f_out.write("Không có dữ liệu trong result.csv để phân tích.\n")
        return

    player_identifier_column = "Player"

    # Xác định các cột chỉ số
    # (Cách tiếp cận tốt nhất là định nghĩa rõ ràng các cột chỉ số như trong Bài 1)
    # Ví dụ:
    # INTEGER_TYPE_COLUMNS = ["Gls", "Ast", "Minutes", ...] # Sao chép từ Bài 1
    # FLOAT_TYPE_COLUMNS = ["xG", "Save%", "Age", ...]   # Sao chép từ Bài 1
    # ALL_DEFINED_STAT_COLUMNS = INTEGER_TYPE_COLUMNS + FLOAT_TYPE_COLUMNS
    # stat_columns_to_analyze = [
    #     col for col in ALL_DEFINED_STAT_COLUMNS if col in player_data_df.columns
    # ]
    # Nếu không có danh sách trên, sử dụng cách tự động phát hiện:
    stat_columns_to_analyze = [
        col for col in player_data_df.columns
        if col not in [player_identifier_column, "Nation", "Team", "Position"]
           and pd.api.types.is_numeric_dtype(player_data_df[col])
    ]

    if not stat_columns_to_analyze:
        print("Không tìm thấy cột chỉ số dạng số nào để phân tích trong tệp CSV.")
        with open(output_txt_path, 'w', encoding='utf-8') as f_out:
            f_out.write("Không tìm thấy cột chỉ số dạng số nào để phân tích.\n")
        return

    print(f"Các cột chỉ số sẽ được phân tích: {stat_columns_to_analyze}")

    analysis_results_content = []

    for stat_col in stat_columns_to_analyze:
        analysis_results_content.append(f"Chỉ số: {stat_col}\n")

        temp_df_stat = player_data_df[[player_identifier_column, stat_col]].copy()
        temp_df_stat.dropna(subset=[stat_col], inplace=True)

        if temp_df_stat.empty:
            analysis_results_content.append("  Không có cầu thủ nào có dữ liệu hợp lệ cho chỉ số này.\n")
            analysis_results_content.append("-" * 40 + "\n")
            continue

        top_3_players = temp_df_stat.sort_values(by=stat_col, ascending=False).head(3)
        analysis_results_content.append("  Top 3 cầu thủ cao nhất:\n")
        if not top_3_players.empty:
            for index, row_data in top_3_players.iterrows():
                analysis_results_content.append(
                    f"    - {row_data[player_identifier_column]} (Chỉ số: {row_data[stat_col]:.2f})\n")
        else:
            analysis_results_content.append("    Không đủ dữ liệu.\n")

        bottom_3_players = temp_df_stat.sort_values(by=stat_col, ascending=True).head(3)
        analysis_results_content.append("  Top 3 cầu thủ thấp nhất:\n")
        if not bottom_3_players.empty:
            for index, row_data in bottom_3_players.iterrows():
                analysis_results_content.append(
                    f"    - {row_data[player_identifier_column]} (Chỉ số: {row_data[stat_col]:.2f})\n")
        else:
            analysis_results_content.append("    Không đủ dữ liệu.\n")

        analysis_results_content.append("-" * 40 + "\n")

    try:
        with open(output_txt_path, 'w', encoding='utf-8') as f_out:
            f_out.writelines(analysis_results_content)
        print(f"Phân tích hoàn tất. Kết quả đã được lưu vào: {output_txt_path}")
    except Exception as e:
        print(f"Lỗi khi ghi vào tệp {output_txt_path}: {e}")


if __name__ == "__main__":
    analyze_player_statistics()