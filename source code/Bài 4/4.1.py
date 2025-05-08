import pandas as pd
import os
from fuzzywuzzy import fuzz, process
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Đường dẫn file CSV
csv_file = r'D:\python project\report\csv\result.csv'
output_dir = r'D:\python project\report\csv'
output_file = os.path.join(output_dir, 'transfer_fee.csv')


# Hàm rút gọn tên cầu thủ
def shorten_name(name):
    """Rút gọn tên thành 2 từ đầu tiên."""
    parts = name.strip().split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name


# Hàm kiểm tra phí chuyển nhượng hợp lệ
def is_valid_transfer_fee(fee):
    """Kiểm tra nếu phí chuyển nhượng là giá trị tiền tệ hoặc Free."""
    if not fee or fee.lower() in ["n/a", "not found", ""]:
        return False
    return fee.lower() == "free" or any(currency in fee for currency in ["€", "£", "$"])


# Hàm đọc và lọc cầu thủ từ result.csv
def load_players_over_900_minutes(csv_file):
    """Đọc file CSV và lọc cầu thủ có hơn 900 phút thi đấu."""
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig', na_values=["N/A"])
        print(f"Đã đọc file CSV: {csv_file}")
        print(f"Số dòng: {df.shape[0]}, Số cột: {df.shape[1]}")

        # Lọc cầu thủ có hơn 900 phút
        df_filtered = df[df['Minutes'] > 900][['Player', 'Team', 'Minutes']].copy()
        print(f"Số cầu thủ thi đấu > 900 phút: {len(df_filtered)}")

        return df_filtered
    except FileNotFoundError:
        print(f"Không tìm thấy file {csv_file}. Vui lòng kiểm tra đường dẫn.")
        exit()
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        exit()


# Hàm thu thập giá trị chuyển nhượng từ web
def scrape_transfer_values(players):
    """Thu thập giá trị chuyển nhượng từ footballtransfers.com."""
    # Cấu hình trình duyệt headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Khởi tạo ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Tạo danh sách URL từ trang 1 đến 14
    base_url = "https://www.footballtransfers.com/us/transfers/confirmed/2024-2025/uk-premier-league/"
    urls = [f"{base_url}{i}" for i in range(1, 15)]

    # Tạo danh sách tên rút gọn để so khớp
    player_names = [shorten_name(name) for name in players['Player'].str.strip()]

    # Tạo dict để tra cứu thông tin cầu thủ
    player_info = dict(zip(players['Player'].str.strip(), zip(players['Team'], players['Minutes'])))

    transfer_results = []
    not_found = []

    try:
        for url in urls:
            print(f"Đang cào dữ liệu từ: {url}")
            driver.get(url)

            try:
                # Đợi bảng chuyển nhượng xuất hiện
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "transfer-table"))
                )

                # Tìm các hàng trong bảng
                rows = table.find_elements(By.TAG_NAME, "tr")

                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if cols and len(cols) >= 3:
                        # Lấy tên cầu thủ
                        player_name = cols[0].text.strip().split("\n")[0].strip()
                        shortened_player_name = shorten_name(player_name)

                        # Lấy phí chuyển nhượng
                        transfer_fee = cols[-1].text.strip() if cols[-1].text.strip() else "N/A"

                        # Lấy loại chuyển nhượng (giả định cột thứ 2 chứa thông tin loại)
                        transfer_type = cols[1].text.strip() if len(cols) > 1 and cols[1].text.strip() else "Unknown"

                        # So khớp tên cầu thủ
                        best_match = process.extractOne(shortened_player_name, player_names,
                                                        scorer=fuzz.token_sort_ratio)

                        if best_match and best_match[1] >= 85:
                            matched_name = best_match[0]
                            # Tìm tên đầy đủ tương ứng
                            for full_name, short_name in zip(players['Player'].str.strip(), player_names):
                                if short_name == matched_name:
                                    team, minutes = player_info[full_name]
                                    # Chỉ thêm nếu phí chuyển nhượng hợp lệ (tiền tệ hoặc Free)
                                    if is_valid_transfer_fee(transfer_fee):
                                        transfer_results.append({
                                            'Player': full_name,
                                            'Team': team,
                                            'Minutes': minutes,
                                            'Transfer Fee': transfer_fee,
                                            'Transfer Type': transfer_type
                                        })
                                    else:
                                        not_found.append(full_name)
                                    break
            except Exception as e:
                print(f"Lỗi khi xử lý {url}: {str(e)}")

        # Thêm các cầu thủ không tìm thấy trong dữ liệu web
        found_players = {result['Player'] for result in transfer_results}
        for player in players['Player']:
            if player not in found_players and player not in not_found:
                not_found.append(player)

    finally:
        driver.quit()

    return transfer_results, not_found


# Hàm lưu kết quả vào file CSV
def save_results_to_csv(transfer_results, not_found, total_players):
    """Lưu kết quả vào file CSV."""
    os.makedirs(output_dir, exist_ok=True)

    # Chuyển kết quả thành DataFrame
    df_results = pd.DataFrame(transfer_results)

    try:
        if not df_results.empty:
            df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Kết quả đã được lưu vào {output_file} với {len(df_results)} cầu thủ")
        else:
            print(f"Không có cầu thủ nào thỏa mãn điều kiện. Không tạo file {output_file}")
    except Exception as e:
        print(f"Lỗi khi ghi file CSV: {e}")

    # In thống kê ra console
    output_content = "Phân tích giá trị chuyển nhượng cầu thủ Premier League 2024–2025 (Thi đấu > 900 phút và có giá trị chuyển nhượng)\n"
    output_content += "=" * 80 + "\n\n"

    output_content += "Thống kê:\n"
    output_content += f"- Số cầu thủ thi đấu > 900 phút: {total_players}\n"
    output_content += f"- Số cầu thủ tìm thấy giá trị chuyển nhượng (bao gồm Free): {len(transfer_results)}\n"
    output_content += f"- Số cầu thủ không tìm thấy giá trị chuyển nhượng: {len(not_found)}\n"

    print(output_content)


# Hàm chính
def main():
    # Đọc và lọc cầu thủ từ result.csv
    players = load_players_over_900_minutes(csv_file)
    total_players = len(players)

    # Thu thập giá trị chuyển nhượng
    transfer_results, not_found = scrape_transfer_values(players)

    # Lưu kết quả
    save_results_to_csv(transfer_results, not_found, total_players)


if __name__ == "__main__":
    main()