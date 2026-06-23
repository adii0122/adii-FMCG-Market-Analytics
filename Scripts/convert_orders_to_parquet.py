import pandas as pd
import os
import glob

# Define paths
source_dir = r'd:/data-engineering-project-using-databricks-free-edition_new/project-de-fmcg-atlikon1/project-de-fmcg-atlikon/0_data/2_child_company/incremental_load/orders'
dest_dir = r'd:/data-engineering-project-using-databricks-free-edition_new/project-de-fmcg-atlikon1/project-de-fmcg-atlikon/0_data/2_child_company/incremental_load/orders_parquet'

# Ensure destination directory exists
os.makedirs(dest_dir, exist_ok=True)

# Find all CSV files
csv_files = glob.glob(os.path.join(source_dir, '*.csv'))

print(f"Found {len(csv_files)} CSV files in {source_dir}")

for file_path in csv_files:
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Construct destination path
        file_name = os.path.basename(file_path)
        new_file_name = file_name.replace('.csv', '.parquet')
        dest_path = os.path.join(dest_dir, new_file_name)
        
        # Save as Parquet
        df.to_parquet(dest_path, index=False)
        print(f"Converted {file_name} to {new_file_name}")
        
    except Exception as e:
        print(f"Error converting {file_path}: {e}")

print("Conversion complete.")
