
import pandas as pd
from backtest_strategy_with_market_filter import calculate_indicators

# Read data
df = pd.read_csv('stock_data.csv')
stock_code = 300394
stock_df = df[df['股票代码'] == stock_code].copy()
stock_df = calculate_indicators(stock_df)

# Find the 2025-07-14 row
target_date = pd.to_datetime('2025-07-14')
target_row = stock_df[stock_df['日期'] == target_date].iloc[0]

print("=== 2025-07-14 天孚通信指标详情 ===")
print(f"日期: {target_row['日期']}")
print(f"收盘: {target_row['收盘']}")
print(f"TD: {target_row['TD']}, TK: {target_row['TK']}")
print(f"TD_prev: {target_row['TD_prev']}, TK_prev: {target_row['TK_prev']}")
print(f"扬帆起航: {target_row['扬帆起航']}, 避风靠岸: {target_row['避风靠岸']}")
print(f"\n指标值:")
print(f"DXD: {target_row['DXD']:.2f}, DXK: {target_row['DXK']:.2f}")
print(f"ZXD: {target_row['ZXD']:.2f}, ZXK: {target_row['ZXK']:.2f}")
print(f"ADX: {target_row['ADX']:.2f}")
