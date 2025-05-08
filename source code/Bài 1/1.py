import os as operating_system
from io import StringIO as string_input_output
import time as execution_timer
import pandas as data_manipulator  # Đổi tên alias của pandas
from bs4 import BeautifulSoup as html_content_parser  # Đổi tên alias
from selenium import webdriver as browser_automation
from selenium.webdriver.chrome.options import Options as ChromeLaunchOptions
from selenium.webdriver.chrome.service import Service as ChromeBrowserService
from webdriver_manager.chrome import ChromeDriverManager as ChromeBrowserDriverManager


# ---- Các hàm xử lý dữ liệu phụ trợ ----

def transform_age_string_to_numeric(age_text_representation):
    """
    Chuyển đổi chuỗi biểu thị tuổi (ví dụ: "30-150") thành dạng số thập phân.
    Định dạng đầu vào: "NĂM-NGÀY".
    """
    age_not_available_value = "N/A"
    try:
        cleaned_age_text = str(age_text_representation).strip()
        if "-" in cleaned_age_text:
            year_component, day_component = map(int, cleaned_age_text.split("-"))
            numeric_age = year_component + (day_component / 365.0)
            return round(numeric_age, 2)
        return age_not_available_value
    except (ValueError, AttributeError) as err_age_parsing:
        print(f"Thông báo lỗi: Gặp sự cố khi phân tích tuổi '{age_text_representation}': {err_age_parsing}")
        return age_not_available_value


def sanitize_nationality_string(nationality_raw_string):
    """
    Trích xuất mã quốc gia (thường là 3 chữ cái cuối) từ chuỗi quốc tịch.
    """
    nationality_not_available_value = "N/A"
    try:
        string_parts = nationality_raw_string.split()
        if not string_parts:
            return nationality_not_available_value
        return string_parts[-1]
    except (AttributeError, IndexError):
        return nationality_not_available_value


# ---- Khởi tạo và cấu hình Selenium WebDriver ----
def setup_automated_browser_instance():
    """Thiết lập và trả về một instance của Chrome WebDriver."""
    browser_launch_config = ChromeLaunchOptions()
    browser_launch_config.add_argument("--headless=new")
    browser_launch_config.add_argument("--disable-gpu")
    browser_launch_config.add_argument("--no-sandbox")
    browser_launch_config.add_argument("--log-level=3")
    browser_launch_config.add_argument("--disable-dev-shm-usage")

    webdriver_service_object = ChromeBrowserService(ChromeBrowserDriverManager().install())
    active_browser_driver = browser_automation.Chrome(
        service=webdriver_service_object,
        options=browser_launch_config
    )
    return active_browser_driver


# ---- Định nghĩa các nguồn dữ liệu (URL và ID bảng) ----
DATA_SCRAPING_TARGETS = [
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_standard"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_keeper"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/shooting/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_shooting"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/passing/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_passing"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/gca/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_gca"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/defense/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_defense"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/possession/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_possession"},
    {"source_url": "https://fbref.com/en/comps/9/2024-2025/misc/2024-2025-Premier-League-Stats",
     "html_table_id": "stats_misc"},
]

# ---- Định nghĩa các cột dữ liệu cần thiết và ánh xạ đổi tên ----
REQUIRED_DATA_FIELDS = [
    "Player", "Nation", "Team", "Position", "Age", "Matches Played", "Starts", "Minutes",
    "Gls", "Ast", "crdY", "crdR", "xG", "xAG", "PrgC", "PrgP", "PrgR",
    "Gls per 90", "Ast per 90", "xG per 90", "xAG per 90", "GA90", "Save%", "CS%", "PK Save%",
    "SoT%", "SoT per 90", "G per Sh", "Dist", "Cmp", "Cmp%", "TotDist", "ShortCmp%", "MedCmp%", "LongCmp%",
    "KP", "Pass into 1_3", "PPA", "CrsPA", "SCA", "SCA90", "GCA", "GCA90", "Tkl", "TklW",
    "Deff Att", "Lost", "Blocks", "Sh", "Pass", "Int", "Touches", "Def Pen", "Def 3rd", "Mid 3rd",
    "Att 3rd", "Att Pen", "Take-Ons Att", "Succ%", "Tkld%", "Carries", "ProDist",
    "Carries 1_3", "CPA", "Mis", "Dis", "Rec", "Rec PrgR", "Fls", "Fld", "Off", "Crs", "Recov",
    "Aerl Won", "Aerl Lost", "Aerl Won%"
]

COLUMN_HEADER_MAPPING_RULES = {
    "stats_standard": {
        "Unnamed: 1": "Player", "Unnamed: 2": "Nation", "Unnamed: 3": "Position",
        "Unnamed: 4": "Team", "Unnamed: 5": "Age", "Playing Time": "Matches Played",
        "Playing Time.1": "Starts", "Playing Time.2": "Minutes", "Performance": "Gls",
        "Performance.1": "Ast", "Performance.6": "crdY", "Performance.7": "crdR",
        "Expected": "xG", "Expected.2": "xAG", "Progression": "PrgC",
        "Progression.1": "PrgP", "Progression.2": "PrgR", "Per 90 Minutes": "Gls per 90",
        "Per 90 Minutes.1": "Ast per 90", "Per 90 Minutes.5": "xG per 90", "Per 90 Minutes.6": "xAG per 90"
    },
    "stats_keeper": {
        "Unnamed: 1": "Player", "Performance.1": "GA90", "Performance.4": "Save%",
        "Performance.9": "CS%", "Penalty Kicks.4": "PK Save%"
    },
    "stats_shooting": {
        "Unnamed: 1": "Player", "Standard.3": "SoT%", "Standard.5": "SoT per 90",
        "Standard.6": "G per Sh", "Standard.8": "Dist"
    },
    "stats_passing": {
        "Unnamed: 1": "Player", "Total": "Cmp", "Total.2": "Cmp%", "Total.3": "TotDist",
        "Short.2": "ShortCmp%", "Medium.2": "MedCmp%", "Long.2": "LongCmp%",
        "Unnamed: 26": "KP", "Unnamed: 27": "Pass into 1_3", "Unnamed: 28": "PPA", "Unnamed: 29": "CrsPA",
    },
    "stats_gca": {"Unnamed: 1": "Player", "SCA.1": "SCA90", "GCA.1": "GCA90"},
    "stats_defense": {
        "Unnamed: 1": "Player", "Tackles": "Tkl", "Tackles.1": "TklW",
        "Challenges.1": "Deff Att", "Challenges.3": "Lost", "Blocks": "Blocks",
        "Blocks.1": "Sh", "Blocks.2": "Pass", "Unnamed: 20": "Int",
    },
    "stats_possession": {
        "Unnamed: 1": "Player", "Touches": "Touches", "Touches.1": "Def Pen",
        "Touches.2": "Def 3rd", "Touches.3": "Mid 3rd", "Touches.4": "Att 3rd",
        "Touches.5": "Att Pen", "Touches.6": "Live", "Take-Ons": "Take-Ons Att",
        "Take-Ons.2": "Succ%", "Take-Ons.4": "Tkld%", "Carries": "Carries",
        "Carries.2": "ProDist", "Carries.4": "Carries 1_3", "Carries.5": "CPA",
        "Carries.6": "Mis", "Carries.7": "Dis", "Receiving": "Rec", "Receiving.1": "Rec PrgR",
    },
    "stats_misc": {
        "Unnamed: 1": "Player", "Performance.3": "Fls", "Performance.4": "Fld",
        "Performance.5": "Off", "Performance.6": "Crs", "Performance.12": "Recov",
        "Aerial Duels": "Aerl Won", "Aerial Duels.1": "Aerl Lost", "Aerial Duels.2": "Aerl Won%"
    }
}

# ---- Định nghĩa kiểu dữ liệu cho các cột sau khi xử lý ----
INTEGER_TYPE_COLUMNS = [
    "Matches Played", "Starts", "Minutes", "Gls", "Ast", "crdY", "crdR", "PrgC", "PrgP", "PrgR",
    "Cmp", "KP", "Pass into 1_3", "PPA", "CrsPA", "ProDist", "TotDist", "Tkl", "TklW", "Deff Att", "Lost", "Blocks",
    "Sh", "Pass", "Int",
    "Touches", "Def Pen", "Def 3rd", "Mid 3rd", "Att 3rd", "Att Pen", "Take-Ons Att",
    "Carries", "Carries 1_3", "CPA", "Mis", "Dis", "Rec", "Rec PrgR",
    "Fls", "Fld", "Off", "Crs", "Recov", "Aerl Won", "Aerl Lost"
]
FLOAT_TYPE_COLUMNS = [
    "Age", "xG", "xAG", "Gls per 90", "Ast per 90", "xG per 90", "xAG per 90", "GA90", "Save%", "CS%", "PK Save%",
    "SoT%", "SoT per 90", "G per Sh", "Dist", "Cmp%", "ShortCmp%", "MedCmp%", "LongCmp%", "SCA", "SCA90", "GCA",
    "GCA90", "Succ%", "Tkld%", "Aerl Won%"
]


# ---- Hàm chính thực thi việc cào và xử lý dữ liệu ----

def extract_table_data_from_webpage(browser, page_url, table_html_id_attribute):
    """Lấy dữ liệu từ một bảng HTML trên trang web và trả về DataFrame."""
    print(f"Đang tiến hành lấy dữ liệu cho bảng '{table_html_id_attribute}' từ: {page_url}")
    browser.get(page_url)
    execution_timer.sleep(3.2)

    web_page_source_code = browser.page_source
    parsed_html_document = html_content_parser(web_page_source_code, "html.parser")
    html_table_object = parsed_html_document.find("table", {"id": table_html_id_attribute})

    if html_table_object is None:
        print(f"Cảnh báo quan trọng: Bảng với ID '{table_html_id_attribute}' không được tìm thấy trên trang.")
        return None

    extracted_dataframe = None
    try:
        list_of_dataframes = data_manipulator.read_html(string_input_output(str(html_table_object)), header=0)
        if list_of_dataframes:
            extracted_dataframe = list_of_dataframes[0]
        else:
            raise ValueError(f"Không có DataFrame nào được trích xuất từ bảng {table_html_id_attribute}")
    except Exception as data_extraction_error:
        print(f"Lỗi nghiêm trọng khi đọc dữ liệu bảng '{table_html_id_attribute}': {data_extraction_error}")
        return None

    rename_rules_for_table = COLUMN_HEADER_MAPPING_RULES.get(table_html_id_attribute, {})
    if rename_rules_for_table:
        extracted_dataframe = extracted_dataframe.rename(columns=rename_rules_for_table)

    extracted_dataframe = extracted_dataframe.loc[:, ~extracted_dataframe.columns.duplicated(keep='first')]

    if "Age" in extracted_dataframe.columns:
        extracted_dataframe["Age"] = extracted_dataframe["Age"].apply(transform_age_string_to_numeric)
    return extracted_dataframe


def merge_multiple_dataframes(dictionary_of_dataframes):
    """Gộp một dictionary các DataFrame thành một DataFrame duy nhất."""
    aggregated_dataframe = None
    required_fields_set = set(REQUIRED_DATA_FIELDS)

    for df_key_name, individual_df_to_merge in dictionary_of_dataframes.items():
        columns_to_include = [col for col in individual_df_to_merge.columns if col in required_fields_set]
        current_filtered_df = individual_df_to_merge[columns_to_include]

        if "Player" in current_filtered_df.columns:
            current_filtered_df = current_filtered_df.drop_duplicates(subset=["Player"], keep="first")
        else:
            print(f"Cảnh báo: Bảng '{df_key_name}' không có cột 'Player' để loại bỏ trùng lặp.")

        if aggregated_dataframe is None:
            aggregated_dataframe = current_filtered_df
        else:
            try:
                if "Player" in current_filtered_df.columns and "Player" in aggregated_dataframe.columns:
                    aggregated_dataframe = data_manipulator.merge(
                        aggregated_dataframe, current_filtered_df,
                        on="Player", how="outer", suffixes=('_original', '_new')
                    )
                    cols_to_remove = [col for col in aggregated_dataframe.columns if col.endswith('_new')]
                    if cols_to_remove:
                        aggregated_dataframe = aggregated_dataframe.drop(columns=cols_to_remove)
                    rename_original_cols = {col: col.replace('_original', '') for col in aggregated_dataframe.columns if
                                            col.endswith('_original')}
                    if rename_original_cols:
                        aggregated_dataframe = aggregated_dataframe.rename(columns=rename_original_cols)
                elif "Player" not in current_filtered_df.columns:
                    print(f"Cảnh báo: Bảng '{df_key_name}' không có cột 'Player' và không thể merge.")
            except Exception as merging_error:
                print(f"Lỗi nghiêm trọng trong quá trình gộp DataFrame cho '{df_key_name}': {merging_error}")
                continue
    return aggregated_dataframe


def perform_final_data_cleanup_and_formatting(master_player_dataframe):
    """Thực hiện các bước làm sạch và định dạng cuối cùng trên DataFrame tổng hợp."""
    if master_player_dataframe is None or master_player_dataframe.empty:
        print("Thông báo: DataFrame tổng hợp rỗng, không có dữ liệu để hoàn thiện.")
        return master_player_dataframe

    final_selected_columns = [col for col in REQUIRED_DATA_FIELDS if col in master_player_dataframe.columns]
    cleaned_dataframe = master_player_dataframe[final_selected_columns].copy()

    for column_header_name in cleaned_dataframe.columns:
        if column_header_name in INTEGER_TYPE_COLUMNS:
            cleaned_dataframe[column_header_name] = data_manipulator.to_numeric(cleaned_dataframe[column_header_name],
                                                                                errors="coerce").astype("Int64")
        elif column_header_name in FLOAT_TYPE_COLUMNS:
            cleaned_dataframe[column_header_name] = data_manipulator.to_numeric(cleaned_dataframe[column_header_name],
                                                                                errors="coerce")
            if cleaned_dataframe[column_header_name].notna().any():
                cleaned_dataframe[column_header_name] = cleaned_dataframe[column_header_name].round(2)

    minutes_played_column = "Minutes"
    if minutes_played_column in cleaned_dataframe.columns and cleaned_dataframe[
        minutes_played_column].dtype != 'object':
        cleaned_dataframe = cleaned_dataframe[cleaned_dataframe[minutes_played_column].fillna(0) > 90]
    elif minutes_played_column in cleaned_dataframe.columns:
        print(f"Cảnh báo: Cột '{minutes_played_column}' không phải kiểu số, không thể lọc theo phút thi đấu.")

    nation_column_name = "Nation"
    if nation_column_name in cleaned_dataframe.columns:
        cleaned_dataframe[nation_column_name] = cleaned_dataframe[nation_column_name].apply(
            lambda nat_val: sanitize_nationality_string(nat_val) if data_manipulator.notna(nat_val) else "N/A"
        )
    return cleaned_dataframe


def export_dataframe_to_predetermined_csv_file(dataframe_to_save):  # Thay đổi tên hàm và tham số
    """Lưu DataFrame kết quả vào một file CSV tại đường dẫn cố định D:\python project\report\csv\result.csv."""
    if dataframe_to_save is None or dataframe_to_save.empty:
        print("Thông báo: Không có dữ liệu để xuất ra file CSV.")
        return

    # Đường dẫn cố định
    fixed_directory_path = r"D:\python project\report\csv"
    fixed_output_filename = "result.csv"
    full_output_file_path = operating_system.path.join(fixed_directory_path, fixed_output_filename)

    try:
        # Tạo thư mục nếu chưa tồn tại
        operating_system.makedirs(fixed_directory_path, exist_ok=True)

        # Lưu file với na_rep="N/A"
        dataframe_to_save.to_csv(full_output_file_path, index=False, encoding="utf-8-sig", na_rep="N/A")  # Đổi na_rep
        print(f"Thông báo thành công: Dữ liệu đã được lưu vào file: {full_output_file_path}")
        print(f"Số liệu DataFrame đã lưu: {dataframe_to_save.shape[0]} dòng và {dataframe_to_save.shape[1]} cột.")
    except Exception as file_saving_error:
        # Xử lý lỗi nếu không thể tạo thư mục hoặc ghi file (ví dụ: do quyền hạn)
        print(f"Lỗi nghiêm trọng khi tạo thư mục hoặc lưu file CSV tại '{full_output_file_path}': {file_saving_error}")
        print("Vui lòng kiểm tra quyền ghi và đường dẫn có hợp lệ không.")


# ---- Điểm vào chính của chương trình ----
if __name__ == "__main__":
    web_browser_instance = setup_automated_browser_instance()
    collected_dataframes_storage = {}
    target_counter = 0

    for target_config in DATA_SCRAPING_TARGETS:
        target_counter += 1
        current_url = target_config["source_url"]
        current_table_id = target_config["html_table_id"]

        print(f"\nĐang xử lý target {target_counter}/{len(DATA_SCRAPING_TARGETS)}: ID bảng '{current_table_id}'")
        single_table_df = extract_table_data_from_webpage(web_browser_instance, current_url, current_table_id)

        if single_table_df is not None and not single_table_df.empty:
            collected_dataframes_storage[current_table_id] = single_table_df
        else:
            print(f"Cảnh báo: Không có dữ liệu nào được lấy từ bảng '{current_table_id}'. Bảng này sẽ được bỏ qua.")

    consolidated_player_dataframe = data_manipulator.DataFrame()
    if collected_dataframes_storage:
        consolidated_player_dataframe = merge_multiple_dataframes(collected_dataframes_storage)
    else:
        print("Cảnh báo lớn: Không có dữ liệu nào được cào từ tất cả các nguồn. File output sẽ rỗng.")

    fully_prepared_dataframe = perform_final_data_cleanup_and_formatting(consolidated_player_dataframe)

    # Xuất DataFrame cuối cùng ra file CSV với đường dẫn và na_rep đã được chỉ định
    export_dataframe_to_predetermined_csv_file(fully_prepared_dataframe)  # Gọi hàm đã sửa đổi

    if web_browser_instance is not None:
        web_browser_instance.quit()

    print(
        f"\n--- Chương trình đã hoàn tất quá trình xử lý dữ liệu lúc {execution_timer.strftime('%Y-%m-%d %H:%M:%S')} ---")
    status_message = "Quá trình cào và xử lý dữ liệu đã kết thúc."
    print(status_message)