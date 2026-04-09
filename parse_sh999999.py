
import pandas as pd
import os

# Read the SH#999999.txt file with GBK encoding
sh999999_path = 'SH#999999.txt'
try:
    # Read the file, skipping the first 2 header rows (since they're garbled/headers we don't need)
    df_sh = pd.read_csv(
        sh999999_path,
        sep='\t',
        encoding='gbk',
        skiprows=2,
        names=['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额']
    )
    
    # Add the required columns
    df_sh['股票代码'] = '999999'
    df_sh['文件名'] = 'SH#999999.txt'
    
    # Reorder columns to match stock_data.csv
    df_sh = df_sh[['股票代码', '文件名', '日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额']]
    
    print("SH#999999 data parsed successfully!")
    print(f"Number of rows: {len(df_sh)}")
    print("\nFirst 5 rows:")
    print(df_sh.head())
    
    # Read existing stock_data.csv
    stock_data_csv_path = 'stock_data.csv'
    if os.path.exists(stock_data_csv_path):
        df_existing = pd.read_csv(stock_data_csv_path)
        print(f"\nExisting stock_data.csv has {len(df_existing)} rows")
        
        # Append SH#999999 data
        df_combined = pd.concat([df_existing, df_sh], ignore_index=True)
        print(f"Combined data has {len(df_combined)} rows")
        
        # Save back to stock_data.csv
        df_combined.to_csv(stock_data_csv_path, index=False)
        print(f"Saved to {stock_data_csv_path}")
        
        # Also update stock_data.xlsx
        stock_data_xlsx_path = 'stock_data.xlsx'
        df_combined.to_excel(stock_data_xlsx_path, index=False)
        print(f"Saved to {stock_data_xlsx_path}")
        
    else:
        print(f"\n{stock_data_csv_path} not found, creating new file")
        df_sh.to_csv(stock_data_csv_path, index=False)
        df_sh.to_excel('stock_data.xlsx', index=False)
        
except Exception as e:
    print(f"Error parsing file: {e}")
