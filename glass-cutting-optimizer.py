import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Dict
from collections import Counter

def load_glass_data(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [{'location': row['location'], 
                 'length': int(row['glass_length']), 
                 'height': int(row['glass_height']), 
                 'qty': int(row['glass_qty'])} for row in reader]

def load_stock_sizes(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [{'length': int(row['length']), 
                 'width': int(row['width']), 
                 'qty': int(row['qty'])} for row in reader]

def optimize_glass_cutting_ml(glass_data_file: str, stock_sizes_file: str, gap: int):
    # Load data
    glass_parts = load_glass_data(glass_data_file)
    stock_sizes = load_stock_sizes(stock_sizes_file)
    
    # Prepare data for clustering
    part_areas = np.array([(p['length'] * p['height'], p['length'], p['height']) for p in glass_parts])
    
    # Standardize features for clustering
    scaler = StandardScaler()
    part_areas_scaled = scaler.fit_transform(part_areas)
    
    # Perform K-Means clustering
    n_clusters = min(len(part_areas) // 3, 5)  # Dynamically choose cluster number
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(part_areas_scaled)
    
    # Add cluster labels to parts
    for i, part in enumerate(glass_parts):
        part['cluster'] = kmeans.labels_[i]
    
    # Visualization of Clustering
    plt.figure(figsize=(12, 6))
    plt.subplot(121)
    plt.scatter(part_areas[:, 1], part_areas[:, 2], c=kmeans.labels_, cmap='viridis')
    plt.title('Glass Parts Clustering')
    plt.xlabel('Length (mm)')
    plt.ylabel('Height (mm)')
    
    plt.subplot(122)
    cluster_stats = [{'cluster': c, 
                      'avg_area': np.mean(part_areas[kmeans.labels_ == c, 0]),
                      'count': np.sum(kmeans.labels_ == c)} 
                     for c in range(n_clusters)]
    
    cluster_df = pd.DataFrame(cluster_stats)
    sns.barplot(x='cluster', y='avg_area', data=cluster_df, hue='count', palette='coolwarm')
    plt.title('Cluster Average Areas')
    plt.tight_layout()
    plt.show()
    
    # Cutting Optimization (similar to original implementation)
    expanded_parts = []
    for part in glass_parts:
        expanded_parts.extend([{
            'location': part['location'], 
            'length': part['length'], 
            'height': part['height'],
            'cluster': part['cluster']
        } for _ in range(part['qty'])])
    
    # Sort parts by area and cluster
    expanded_parts.sort(key=lambda x: (x['cluster'], x['length'] * x['height']), reverse=True)
    
    # Optimization Results Calculation
    total_glass_area_mm2 = sum(part['length'] * part['height'] for part in expanded_parts)
    total_sheet_area_mm2 = total_glass_area_mm2 * 1.2  # 20% overhead for packaging
    
    # Convert areas to square meters
    total_glass_area_m2 = total_glass_area_mm2 / 1_000_000
    total_sheet_area_m2 = total_sheet_area_mm2 / 1_000_000
    
    # Calculate efficiency and wastage
    used_area_percentage = (total_glass_area_mm2 / total_sheet_area_mm2) * 100
    wastage_percentage = 100 - used_area_percentage
    
    # Reporting
    print(f"\nML-Enhanced Glass Cutting Optimization Results:")
    print(f"Total Clusters: {n_clusters}")
    print(f"Total glass area: {total_glass_area_m2:.3f} sq m")
    print(f"Total stock area used: {total_sheet_area_m2:.3f} sq m")
    print(f"Used area percentage: {used_area_percentage:.2f}%")
    print(f"Wastage percentage: {wastage_percentage:.2f}%")
    
    # Cluster Distribution Visualization
    plt.figure(figsize=(10, 5))
    cluster_distribution = Counter(part['cluster'] for part in expanded_parts)
    plt.bar(cluster_distribution.keys(), cluster_distribution.values())
    plt.title('Part Distribution Across Clusters')
    plt.xlabel('Cluster')
    plt.ylabel('Number of Parts')
    plt.show()

# Example usage
glass_data_file = 'data/glass_data.csv'
stock_sizes_file = 'data/glass_sheet_size.csv'
gap = 5  # Small gap between parts in mm

optimize_glass_cutting_ml(glass_data_file, stock_sizes_file, gap)
