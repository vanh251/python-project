import pandas as pd
import numpy as np
import os
import re
from fuzzywuzzy import process, fuzz
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Đường dẫn thư mục và file
csv_dir = r"D:\python project\report\csv"
result_path = os.path.join(csv_dir, "result.csv")
output_path = os.path.join(csv_dir, "estimate_transfer_fee.csv")

# Các cột đầu ra chuẩn
standard_output_columns = [
    'Player', 'Team', 'Nation', 'Position', 'Actual_Transfer_Value_M', 'Predicted_Transfer_Value_M'
]

# Cấu hình cho các vị trí
positions_config = {
    'GK': {
        'position_filter': 'GK',
        'features': [
            'Save%', 'CS%', 'GA90', 'Minutes', 'Age', 'PK Save%', 'Team', 'Nation'
        ],
        'important_features': ['Save%', 'CS%', 'PK Save%']
    },
    'DF': {
        'position_filter': 'DF',
        'features': [
            'Tkl', 'TklW', 'Int', 'Blocks', 'Recov', 'Minutes', 'Team', 'Age', 'Nation', 'Aerl Won%',
            'Aerl Won', 'Cmp', 'Cmp%', 'PrgP', 'LongCmp%', 'Carries', 'Touches', 'Dis', 'Mis'
        ],
        'important_features': ['Tkl', 'TklW', 'Int', 'Blocks', 'Aerl Won%', 'Aerl Won', 'Recov']
    },
    'MF': {
        'position_filter': 'MF',
        'features': [
            'Cmp%', 'KP', 'PPA', 'PrgP', 'Tkl', 'Ast', 'SCA', 'Touches', 'Minutes', 'Team', 'Age', 'Nation',
            'Pass into 1_3', 'xAG', 'Carries 1_3', 'ProDist', 'Rec', 'Mis', 'Dis'
        ],
        'important_features': ['KP', 'PPA', 'PrgP', 'SCA', 'xAG', 'Pass into 1_3', 'Carries 1_3']
    },
    'FW': {
        'position_filter': 'FW',
        'features': [
            'Gls', 'Ast', 'Gls per 90', 'xG per 90', 'SoT%', 'G per Sh', 'SCA90', 'GCA90',
            'PrgC', 'Carries 1_3', 'Aerl Won%', 'Team', 'Age', 'Minutes'
        ],
        'important_features': ['Gls', 'Ast', 'Gls per 90', 'xG per 90', 'SCA90', 'GCA90']
    }
}

# Hàm rút ngắn tên
def shorten_name(name):
    if name == "Manuel Ugarte Ribeiro": return "Manuel Ugarte"
    elif name == "Igor Júlio": return "Igor"
    elif name == "Igor Thiago": return "Thiago"
    elif name == "Felipe Morato": return "Morato"
    elif name == "Nathan Wood-Gordon": return "Nathan Wood"
    elif name == "Bobby Reid": return "Bobby Cordova-Reid"
    elif name == "J. Philogene": return "Jaden Philogene Bidace"
    parts = name.strip().split(" ")
    return parts[0] + " " + parts[-1] if len(parts) >= 3 else name

# Hàm chuyển đổi giá trị chuyển nhượng
def parse_etv(etv_text):
    if pd.isna(etv_text) or etv_text in ["N/A", ""]:
        return np.nan
    try:
        etv_text = re.sub(r'[€£]', '', etv_text).strip().upper()
        multiplier = 1000000 if 'M' in etv_text else 1000 if 'K' in etv_text else 1
        value = float(re.sub(r'[MK]', '', etv_text)) * multiplier
        return value
    except (ValueError, TypeError):
        return np.nan

# Hàm so khớp tên
def fuzzy_match_name(name, choices, score_threshold=80):
    if not isinstance(name, str):
        return None, None
    shortened_name = shorten_name(name).lower()
    shortened_choices = [shorten_name(c).lower() for c in choices if isinstance(c, str)]
    match = process.extractOne(
        shortened_name,
        shortened_choices,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=score_threshold
    )
    if match is not None:
        matched_idx = shortened_choices.index(match[0])
        return choices[matched_idx], match[1]
    return None, None

# Hàm cào dữ liệu giá trị chuyển nhượng
def scrape_transfer_values():
    df_players = pd.read_csv(result_path)
    player_positions = dict(zip(df_players['Player'].str.strip().apply(shorten_name), df_players['Position']))
    player_original_names = dict(zip(df_players['Player'].str.strip().apply(shorten_name), df_players['Player'].str.strip()))
    player_names = list(player_positions.keys())

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    base_url = "https://www.footballtransfers.com/us/players/uk-premier-league/"
    urls = [f"{base_url}{i}" for i in range(1, 23)]
    all_data = []

    try:
        for url in urls:
            driver.get(url)
            print(f"Scraping: {url}")
            try:
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "similar-players-table"))
                )
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if cols and len(cols) >= 2:
                        player_name = cols[1].text.strip().split("\n")[0].strip()
                        shortened_player_name = shorten_name(player_name)
                        etv = cols[-1].text.strip() if len(cols) >= 3 else "N/A"
                        best_match = process.extractOne(shortened_player_name, player_names, scorer=fuzz.token_sort_ratio)
                        if best_match and best_match[1] >= 80:
                            matched_name = best_match[0]
                            original_name = player_original_names.get(matched_name, matched_name)
                            position = player_positions.get(matched_name, "Unknown")
                            print(f"Match found: {player_name} -> {original_name} (score: {best_match[1]}, Position: {position})")
                            all_data.append([original_name, position, etv])
                        else:
                            print(f"No match for: {player_name} (best match: {best_match[0] if best_match else 'None'}, score: {best_match[1] if best_match else 'N/A'})")
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
    finally:
        driver.quit()

    if all_data:
        df_all = pd.DataFrame(all_data, columns=['Player', 'Position', 'Price'])
        print("Dữ liệu cào được đã sẵn sàng để xử lý.")
        return df_all
    else:
        print("No matching players found.")
        return pd.DataFrame(columns=['Player', 'Position', 'Price'])

# Hàm xử lý dữ liệu theo vị trí
def process_position(position, config, df_etv):
    try:
        df_result = pd.read_csv(result_path)
    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy tệp result.csv - {e}")
        return None, None

    df_result['Primary_Position'] = df_result['Position'].astype(str).str.split(r'[,/]').str[0].str.strip()
    df_result = df_result[df_result['Primary_Position'].str.upper() == config['position_filter'].upper()].copy()

    player_names = df_etv['Player'].dropna().tolist()
    df_result['Matched_Name'] = None
    df_result['Match_Score'] = None
    df_result['ETV'] = np.nan

    for idx, row in df_result.iterrows():
        matched_name, score = fuzzy_match_name(row['Player'], player_names)
        if matched_name:
            df_result.at[idx, 'Matched_Name'] = matched_name
            df_result.at[idx, 'Match_Score'] = score
            matched_row = df_etv[df_etv['Player'] == matched_name]
            if not matched_row.empty:
                etv_value = parse_etv(matched_row['Price'].iloc[0])
                df_result.at[idx, 'ETV'] = etv_value

    df_filtered = df_result[df_result['Matched_Name'].notna()].copy()
    df_filtered = df_filtered.drop_duplicates(subset='Matched_Name')
    unmatched = df_result[df_result['Matched_Name'].isna()]['Player'].dropna().tolist()
    if unmatched:
        print(f"Cầu thủ {position} không khớp: {len(unmatched)} cầu thủ.")
        print(unmatched)

    features = config['features']
    target = 'ETV'

    for col in features:
        if col in ['Team', 'Nation']:
            df_filtered[col] = df_filtered[col].fillna('Unknown')
        else:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
            median_value = df_filtered[col].median()
            df_filtered[col] = df_filtered[col].fillna(median_value if not pd.isna(median_value) else 0)

    numeric_features = [col for col in features if col not in ['Team', 'Nation']]
    for col in numeric_features:
        df_filtered[col] = np.log1p(df_filtered[col].clip(lower=0))

    for col in config['important_features']:
        if col in df_filtered.columns:
            df_filtered[col] = df_filtered[col] * 2.0
    if 'Minutes' in df_filtered.columns:
        df_filtered['Minutes'] = df_filtered['Minutes'] * 1.5
    if 'Age' in df_filtered.columns:
        df_filtered['Age'] = df_filtered['Age'] * 0.5

    df_ml = df_filtered.dropna(subset=[target]).copy()
    if df_ml.empty:
        print(f"Lỗi: Không có dữ liệu ETV hợp lệ cho {position}.")
        return None, unmatched

    X = df_ml[features]
    y = df_ml[target]

    if len(df_ml) > 5:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    else:
        print(f"Cảnh báo: Không đủ dữ liệu cho {position} để chia tập huấn luyện/kiểm tra.")
        X_train, y_train = X, y
        X_test, y_test = X, y

    categorical_features = [col for col in features if col in ['Team', 'Nation']]
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ])

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    pipeline.fit(X_train, y_train)

    if len(X_test) > 0:
        y_pred = pipeline.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        print(f"Đánh giá mô hình {position} - RMSE: {rmse:.2f}, R²: {r2:.2f}")

    df_filtered['Predicted_Transfer_Value'] = pipeline.predict(df_filtered[features])
    df_filtered['Predicted_Transfer_Value'] = df_filtered['Predicted_Transfer_Value'].clip(lower=100_000, upper=200_000_000)
    df_filtered['Predicted_Transfer_Value_M'] = (df_filtered['Predicted_Transfer_Value'] / 1_000_000).round(2)
    df_filtered['Actual_Transfer_Value_M'] = (df_filtered['ETV'] / 1_000_000).round(2)

    for col in standard_output_columns:
        if col not in df_filtered.columns:
            df_filtered[col] = np.nan if col in ['Actual_Transfer_Value_M', 'Predicted_Transfer_Value_M'] else ''

    df_filtered['Position'] = position
    result = df_filtered[standard_output_columns].copy()

    numeric_features_no_age = [col for col in numeric_features if col != 'Age']
    for col in numeric_features_no_age:
        if col in result.columns:
            result[col] = np.expm1(result[col]).round(2)
    if 'Age' in result.columns:
        result['Age'] = np.expm1(result['Age']).round(0)
        median_age = result['Age'].median()
        result['Age'] = result['Age'].fillna(median_age).astype(int)

    return result, unmatched

# Main execution
print("Bắt đầu cào dữ liệu giá trị chuyển nhượng...")
df_etv = scrape_transfer_values()

all_results = []
all_unmatched = []

for position, config in positions_config.items():
    print(f"\nĐang xử lý {position}...")
    result, unmatched = process_position(position, config, df_etv)
    if result is not None:
        all_results.append(result)
    if unmatched:
        all_unmatched.extend([(position, player) for player in unmatched])

if all_results:
    try:
        combined_results = pd.concat(all_results, ignore_index=True)
        combined_results = combined_results.sort_values(by='Predicted_Transfer_Value_M', ascending=False)
        combined_results.to_csv(output_path, index=False)
        print(f"Kết quả đã được lưu vào '{output_path}'")
    except ValueError as e:
        print(f"Lỗi khi nối: {e}")
        print("Các cột trong mỗi DataFrame kết quả:")
        for i, df in enumerate(all_results):
            print(f"Cột vị trí {list(positions_config.keys())[i]}: {df.columns.tolist()}")

if all_unmatched:
    print("\nDanh sách cầu thủ không khớp:")
    for position, player in all_unmatched:
        print(f"Vị trí: {position}, Cầu thủ: {player}")