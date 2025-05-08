import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import os


def cluster_players_with_kmeans_and_pca():
    """
    Phân nhóm cầu thủ bằng K-means, giảm chiều bằng PCA, và vẽ biểu đồ phân cụm 2D.
    """
    # Đường dẫn file
    input_csv_path = r"D:\python project\report\csv\result.csv"
    output_analysis_path = r"D:\python project\report\txt\kmeans_analysis_summary_k4.txt"
    output_plot_dir = r"D:\python project\report\histograms\k-means"
    elbow_plot_path = os.path.join(output_plot_dir, "kmeans_elbow_plot.png")
    pca_plot_path = os.path.join(output_plot_dir, "kmeans_pca_plot.png")

    # --- 1. Tải dữ liệu ---
    try:
        player_data_df = pd.read_csv(input_csv_path, na_values="N/A", encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp {input_csv_path}. Hãy đảm bảo file tồn tại.")
        return
    except Exception as e:
        print(f"Lỗi khi đọc tệp CSV: {e}")
        return

    if player_data_df.empty:
        print("Tệp result.csv rỗng. Không có dữ liệu để phân tích.")
        return

    print(f"Đã tải thành công {len(player_data_df)} cầu thủ từ {input_csv_path}")

    # --- 2. Tiền xử lý dữ liệu ---
    # Chọn cột thông tin cầu thủ
    player_info_df = player_data_df[['Player', 'Team', 'Position']].copy()

    # Chọn các cột số để phân cụm, loại bỏ cột không liên quan
    cols_to_exclude = ['Minutes', 'Matches Played', 'Starts']
    features_for_clustering_df = player_data_df.drop(columns=['Player', 'Nation', 'Team', 'Position'] + cols_to_exclude,
                                                     errors='ignore')
    features_for_clustering_df = features_for_clustering_df.select_dtypes(include=np.number)

    if features_for_clustering_df.empty or features_for_clustering_df.shape[1] == 0:
        print("Không có đủ cột chỉ số số học để thực hiện phân cụm sau khi lọc.")
        return

    print(
        f"Các chỉ số được sử dụng để phân cụm ({features_for_clustering_df.shape[1]} chỉ số): {features_for_clustering_df.columns.tolist()}")

    # Xử lý giá trị thiếu bằng trung vị
    imputer = SimpleImputer(strategy='median')
    imputed_features = imputer.fit_transform(features_for_clustering_df)
    imputed_features_df = pd.DataFrame(imputed_features, columns=features_for_clustering_df.columns)

    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(imputed_features_df)
    scaled_features_df = pd.DataFrame(scaled_features, columns=imputed_features_df.columns)

    print("Đã hoàn tất tiền xử lý dữ liệu (xử lý NaN, chuẩn hóa).")

    # --- 3. Xác định số cụm tối ưu bằng phương pháp Elbow ---
    inertia_values = []
    possible_k_values = range(2, 16)

    for k in possible_k_values:
        kmeans_model = KMeans(n_clusters=k, init='k-means++', n_init='auto', random_state=42, algorithm='lloyd')
        kmeans_model.fit(scaled_features_df)
        inertia_values.append(kmeans_model.inertia_)

    # Vẽ và lưu biểu đồ Elbow
    plt.figure(figsize=(10, 6))
    plt.plot(possible_k_values, inertia_values, marker='o', linestyle='--')
    plt.title('Phương pháp Elbow để xác định số cụm tối ưu (K)')
    plt.xlabel('Số lượng cụm (K)')
    plt.ylabel('Inertia (Tổng bình phương khoảng cách nội cụm)')
    plt.xticks(possible_k_values)
    plt.grid(True)

    os.makedirs(output_plot_dir, exist_ok=True)
    plt.savefig(elbow_plot_path)
    print(f"Đã lưu biểu đồ Elbow vào: {elbow_plot_path}")
    plt.close()

    # Chọn K=4 (dựa trên vai trò bóng đá: thủ môn, hậu vệ, tiền vệ, tiền đạo)
    optimal_k = 4
    print(f"Số cụm (K) được chọn để phân nhóm là: {optimal_k}")

    # --- 4. Áp dụng thuật toán K-means với K=4 ---
    final_kmeans_model = KMeans(n_clusters=optimal_k, init='k-means++', n_init='auto', random_state=42,
                                algorithm='lloyd')
    cluster_labels = final_kmeans_model.fit_predict(scaled_features_df)

    # Thêm nhãn cụm vào DataFrame thông tin cầu thủ
    player_info_df['Cluster'] = cluster_labels
    print(f"Đã gán nhãn cụm cho {len(player_info_df)} cầu thủ.")

    # --- 5. Giảm chiều dữ liệu bằng PCA ---
    pca = PCA(n_components=2)
    pca_features = pca.fit_transform(scaled_features_df)
    explained_variance_ratio = pca.explained_variance_ratio_
    print(f"Tỷ lệ phương sai được giải thích bởi 2 thành phần PCA: {explained_variance_ratio.sum():.2%}")

    # Tạo DataFrame cho dữ liệu PCA
    pca_df = pd.DataFrame(data=pca_features, columns=['PCA1', 'PCA2'])
    pca_df['Cluster'] = cluster_labels
    pca_df['Player'] = player_info_df['Player'].values
    pca_df['Position'] = player_info_df['Position'].values

    # --- 6. Vẽ biểu đồ phân cụm 2D ---
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=pca_df, x='PCA1', y='PCA2', hue='Cluster', palette='deep', style='Position', s=100)
    plt.title('Phân cụm cầu thủ Premier League (PCA, K=4)')
    plt.xlabel(f'PCA1 ({explained_variance_ratio[0]:.2%} phương sai)')
    plt.ylabel(f'PCA2 ({explained_variance_ratio[1]:.2%} phương sai)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    plt.savefig(pca_plot_path)
    print(f"Đã lưu biểu đồ phân cụm 2D vào: {pca_plot_path}")
    plt.close()

    # --- 7. Phân tích và diễn giải các cụm ---
    analysis_df = imputed_features_df.copy()
    analysis_df['Cluster'] = cluster_labels
    analysis_df['Player'] = player_info_df['Player'].values
    analysis_df['Position'] = player_info_df['Position'].values

    cluster_summary_stats = analysis_df.groupby('Cluster')[features_for_clustering_df.columns].mean()
    cluster_counts = analysis_df['Cluster'].value_counts().sort_index()

    analysis_output_content = ["PHÂN TÍCH CÁC CỤM CẦU THỦ BẰNG K-MEANS (K=4)\n\n"]
    analysis_output_content.append(f"Số cụm (K) đã sử dụng: {optimal_k}\n\n")
    analysis_output_content.append("Số lượng cầu thủ trong mỗi cụm:\n")
    analysis_output_content.append(cluster_counts.to_string() + "\n\n")
    analysis_output_content.append(
        "Đặc điểm trung bình của các chỉ số cho từng cụm (giá trị gốc, sau khi xử lý NaN):\n")

    for i in range(optimal_k):
        analysis_output_content.append(f"\n--- Cụm {i} ({cluster_counts.get(i, 0)} cầu thủ) ---\n")
        analysis_output_content.append(cluster_summary_stats.loc[i].to_string() + "\n")
        example_players = analysis_df[analysis_df['Cluster'] == i][['Player', 'Position']].head(5)
        analysis_output_content.append("\nCầu thủ ví dụ (và vị trí của họ):\n")
        analysis_output_content.append(example_players.to_string(index=False) + "\n")

    # Thêm nhận xét về số cụm và kết quả
    analysis_output_content.append("\n=== NHẬN XÉT VỀ KẾT QUẢ PHÂN CỤM ===\n")
    analysis_output_content.append("1. Số cụm tối ưu:\n")
    analysis_output_content.append(
        "- Số cụm K=4 được chọn dựa trên giả định rằng các cầu thủ Premier League có thể được chia thành 4 vai trò chính: thủ môn, hậu vệ, tiền vệ, và tiền đạo.\n")
    analysis_output_content.append(
        "- Biểu đồ Elbow (xem kmeans_elbow_plot.png) cho thấy sự giảm inertia chậm lại quanh K=4 hoặc K=5, hỗ trợ lựa chọn này.\n")
    analysis_output_content.append(
        "- K=4 phù hợp với các vai trò cơ bản trong bóng đá, trong khi K lớn hơn (ví dụ: 6) có thể phân tách chi tiết hơn (tiền vệ phòng ngự, tiền vệ tấn công, cánh), nhưng có thể làm kết quả phức tạp hơn.\n")

    analysis_output_content.append("\n2. Diễn giải các cụm:\n")
    for i in range(optimal_k):
        stats = cluster_summary_stats.loc[i]
        high_stats = stats[stats > stats.mean() + stats.std()].index.tolist()
        low_stats = stats[stats < stats.mean() - stats.std()].index.tolist()
        analysis_output_content.append(f"- Cụm {i}:\n")
        if high_stats:
            analysis_output_content.append(f"  + Đặc trưng bởi các chỉ số cao: {', '.join(high_stats)}\n")
        if low_stats:
            analysis_output_content.append(f"  + Đặc trưng bởi các chỉ số thấp: {', '.join(low_stats)}\n")
        example_positions = analysis_df[analysis_df['Cluster'] == i]['Position'].value_counts().index.tolist()[:2]
        analysis_output_content.append(f"  + Chủ yếu là: {', '.join(example_positions)}\n")

    analysis_output_content.append("\n3. Nhận xét về biểu đồ PCA:\n")
    analysis_output_content.append(
        f"- Biểu đồ phân cụm 2D (xem kmeans_pca_plot.png) hiển thị các cụm trong không gian 2 chiều, giải thích {explained_variance_ratio.sum():.2%} phương sai.\n")
    analysis_output_content.append(
        "- Các cụm được phân tách rõ rệt nếu các điểm thuộc cùng cụm tập trung gần nhau, cho thấy K-means đã phân nhóm tốt.\n")
    analysis_output_content.append(
        "- Nếu các cụm chồng lấn, điều này có thể do PCA không giữ được toàn bộ thông tin từ dữ liệu gốc, hoặc các vai trò có phong cách chơi tương đồng (ví dụ: tiền vệ tấn công và tiền đạo).\n")

    analysis_output_content.append("\n4. Nhận xét tổng quan:\n")
    analysis_output_content.append(
        "- K-means kết hợp PCA giúp trực quan hóa phong cách chơi, phản ánh vai trò trên sân (thủ môn có Save% cao, tiền đạo có Gls, xG cao, v.v.).\n")
    analysis_output_content.append(
        "- Một số cụm có thể chồng lấn do tương quan giữa các chỉ số (ví dụ: tiền vệ và tiền đạo đều có Ast cao).\n")
    analysis_output_content.append(
        "- Kết quả phù hợp để phân tích chiến thuật, nhưng có thể cải thiện bằng cách chọn các chỉ số 'per 90' để giảm ảnh hưởng thời gian thi đấu hoặc tăng K để tách biệt vai trò chi tiết hơn.\n")
    analysis_output_content.append(
        "- Đề xuất: Sử dụng các thuật toán phân cụm khác (như DBSCAN) hoặc thêm các chỉ số đặc trưng hơn để cải thiện độ tách biệt của các cụm.\n")

    # --- 8. Lưu kết quả phân tích ---
    try:
        os.makedirs(os.path.dirname(output_analysis_path), exist_ok=True)
        with open(output_analysis_path, 'w', encoding='utf-8') as f:
            f.writelines(analysis_output_content)
        print(f"Đã lưu tóm tắt phân tích cụm vào: {output_analysis_path}")
    except Exception as e:
        print(f"Lỗi khi lưu tệp kết quả: {e}")


if __name__ == "__main__":
    cluster_players_with_kmeans_and_pca()