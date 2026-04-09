
import pandas as pd

# Read the combined data
df = pd.read_csv('stock_data.csv')

# Remove rows where '日期' is not in YYYY/MM/DD format
# Or remove rows where '开盘' is not a number
df['开盘'] = pd.to_numeric(df['开盘'], errors='coerce')
df = df.dropna(subset=['开盘'])

# Convert back to integer for '股票代码'? Maybe not necessary, but let's check
print(f"After cleaning, {len(df)} rows left")

# Save back to CSV and Excel
df.to_csv('stock_data.csv', index=False)
df.to_excel('stock_data.xlsx', index=False)

print("Data cleaned and saved!")
