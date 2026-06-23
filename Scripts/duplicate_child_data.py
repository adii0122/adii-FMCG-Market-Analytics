#!/usr/bin/env python3
"""
Duplicate Child Company Data for Big Data Testing

This script scales up the child company dataset by duplicating data
while maintaining referential integrity across tables.

Usage:
    python scripts/duplicate_child_data.py --multiplier 10 [--dry-run]
"""

import pandas as pd
import argparse
import os
from pathlib import Path
import shutil
from datetime import datetime
from tqdm import tqdm


class ChildDataDuplicator:
    """Handles duplication of child company data with referential integrity"""

    def __init__(self, base_dir: Path, multiplier: int, output_format: str = "csv", dry_run: bool = False):
        self.base_dir = base_dir
        self.multiplier = multiplier
        self.output_format = output_format
        self.dry_run = dry_run
        self.full_load_dir = base_dir / "full_load"
        self.incremental_dir = base_dir / "incremental_load"

        # ID offsets for each duplication iteration
        self.customer_id_offset = 100000
        self.product_id_offset = 10000000

    def create_backup(self):
        """Create timestamped backup of original data"""
        if self.dry_run:
            print("DRY RUN: Would create backup")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.base_dir.parent / f"2_child_company_backup_{timestamp}"

        print(f"Creating backup at: {backup_dir}")
        shutil.copytree(self.base_dir, backup_dir)
        print("✓ Backup created successfully")

    def duplicate_customers(self):
        """Duplicate customers.csv with new customer IDs"""
        print("\n📊 Duplicating customers...")

        file_path = self.full_load_dir / "customers" / "customers.csv"
        df_original = pd.read_csv(file_path)
        original_count = len(df_original)

        duplicated_dfs = [df_original]

        for i in range(1, self.multiplier):
            df_dup = df_original.copy()
            df_dup['customer_id'] = df_dup['customer_id'] + (i * self.customer_id_offset)
            duplicated_dfs.append(df_dup)

        df_final = pd.concat(duplicated_dfs, ignore_index=True)

        if not self.dry_run:
            self._save_dataframe(df_final, file_path)

        print(f"  Original rows: {original_count}")
        print(f"  New rows: {len(df_final)}")
        print(f"  ✓ Customers scaled {self.multiplier}x")

        return df_final

    def duplicate_products(self):
        """Duplicate products.csv with new product IDs"""
        print("\n📦 Duplicating products...")

        file_path = self.full_load_dir / "products" / "products.csv"
        df_original = pd.read_csv(file_path)
        original_count = len(df_original)

        duplicated_dfs = [df_original]

        for i in range(1, self.multiplier):
            df_dup = df_original.copy()
            # Convert to int, add offset, convert back to maintain data type
            df_dup['product_id'] = pd.to_numeric(df_dup['product_id'], errors='coerce').fillna(0).astype(int) + (
                        i * self.product_id_offset)
            duplicated_dfs.append(df_dup)

        df_final = pd.concat(duplicated_dfs, ignore_index=True)

        if not self.dry_run:
            self._save_dataframe(df_final, file_path)

        print(f"  Original rows: {original_count}")
        print(f"  New rows: {len(df_final)}")
        print(f"  ✓ Products scaled {self.multiplier}x")

        return df_final

    def duplicate_gross_price(self):
        """Duplicate gross_price.csv with updated product_id references"""
        print("\n💰 Duplicating gross prices...")

        file_path = self.full_load_dir / "gross_price" / "gross_price.csv"
        df_original = pd.read_csv(file_path)
        original_count = len(df_original)

        duplicated_dfs = [df_original]

        for i in range(1, self.multiplier):
            df_dup = df_original.copy()
            # Convert to int, add offset, convert back to maintain data type
            df_dup['product_id'] = pd.to_numeric(df_dup['product_id'], errors='coerce').fillna(0).astype(int) + (
                        i * self.product_id_offset)
            duplicated_dfs.append(df_dup)

        df_final = pd.concat(duplicated_dfs, ignore_index=True)

        if not self.dry_run:
            self._save_dataframe(df_final, file_path)

        print(f"  Original rows: {original_count}")
        print(f"  New rows: {len(df_final)}")
        print(f"  ✓ Gross prices scaled {self.multiplier}x")

    def duplicate_orders_directory(self, orders_dir: Path, dir_type: str):
        """Duplicate all order CSV files in a directory"""
        print(f"\n🛒 Duplicating {dir_type} orders...")

        # Find all CSV files in the landing directory
        if dir_type == "full_load":
            csv_files = list((orders_dir / "landing").glob("*.csv"))
        else:
            csv_files = list(orders_dir.glob("*.csv"))

        print(f"  Found {len(csv_files)} order files")

        total_rows_original = 0
        total_rows_new = 0

        for csv_file in tqdm(csv_files, desc="  Processing files"):
            df_original = pd.read_csv(csv_file)
            original_count = len(df_original)
            total_rows_original += original_count

            duplicated_dfs = [df_original]

            for i in range(1, self.multiplier):
                df_dup = df_original.copy()

                # Update IDs with offsets (handle type conversion)
                df_dup['customer_id'] = pd.to_numeric(df_dup['customer_id'], errors='coerce').fillna(0).astype(int) + (
                            i * self.customer_id_offset)
                df_dup['product_id'] = pd.to_numeric(df_dup['product_id'], errors='coerce').fillna(0).astype(int) + (
                            i * self.product_id_offset)

                # Make order_id unique by appending suffix
                df_dup['order_id'] = df_dup['order_id'].astype(str) + f"_{i}"

                duplicated_dfs.append(df_dup)

            df_final = pd.concat(duplicated_dfs, ignore_index=True)
            total_rows_new += len(df_final)

            if not self.dry_run:
                self._save_dataframe(df_final, csv_file)

        print(f"  Original total rows: {total_rows_original:,}")
        print(f"  New total rows: {total_rows_new:,}")
        print(f"  ✓ Orders scaled {self.multiplier}x")

    def _save_dataframe(self, df: pd.DataFrame, file_path: Path):
        """Save dataframe in specified format (CSV or Parquet)"""
        if self.output_format == "parquet":
            # Convert numeric ID columns to string for Parquet compatibility
            df_copy = df.copy()
            for col in df_copy.columns:
                if 'id' in col.lower():
                    df_copy[col] = df_copy[col].astype(str)

            parquet_path = file_path.with_suffix('.parquet')
            df_copy.to_parquet(parquet_path, compression='snappy', index=False)
        else:
            df.to_csv(file_path, index=False)

    def run(self):
        """Execute the full duplication process"""
        print("=" * 60)
        print(f"Child Company Data Duplication (Multiplier: {self.multiplier}x)")
        print("=" * 60)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files will be modified\n")

        # Create backup
        if not self.dry_run:
            self.create_backup()

        # Duplicate dimension tables
        self.duplicate_customers()
        self.duplicate_products()
        self.duplicate_gross_price()

        # Duplicate fact tables (orders)
        full_orders_dir = self.full_load_dir / "orders"
        self.duplicate_orders_directory(full_orders_dir, "full_load")

        # Duplicate incremental orders if they exist
        incr_orders_dir = self.incremental_dir / "orders"
        if incr_orders_dir.exists():
            self.duplicate_orders_directory(incr_orders_dir, "incremental_load")

        print("\n" + "=" * 60)
        if self.dry_run:
            print("✓ Dry run completed successfully!")
        else:
            print("✓ Data duplication completed successfully!")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate child company data for big data testing"
    )
    parser.add_argument(
        "--multiplier",
        type=int,
        default=10,
        help="How many times to duplicate the data (default: 10)"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "parquet"],
        default="csv",
        help="Output format: csv (default) or parquet (10-20x smaller, faster)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making any changes"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="0_data/2_child_company",
        help="Base directory for child company data"
    )

    args = parser.parse_args()

    # Resolve base directory
    base_dir = Path(args.base_dir)
    if not base_dir.is_absolute():
        # Assume relative to project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        base_dir = project_root / base_dir

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return 1

    # Create duplicator and run
    duplicator = ChildDataDuplicator(
        base_dir=base_dir,
        multiplier=args.multiplier,
        output_format=args.format,
        dry_run=args.dry_run
    )

    duplicator.run()

    return 0


if __name__ == "__main__":
    exit(main())
c