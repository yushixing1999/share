
import pandas as pd
from backtest_strategy_with_market_filter import calculate_indicators

# Read data
df = pd.read_csv('stock_data.csv')
market_df = df[df['股票代码'] == 999999].copy()
market_df = calculate_indicators(market_df)

# Check dates around 2025-07-14
check_start = pd.to_datetime('2025-07-10')
check_end = pd.to_datetime('2025-07-16')
mask = (market_df['日期'] >= check_start) & (market_df['日期'] <= check_end)
check_df = market_df[mask].copy()

print("=== 上证指数 2025-07-10 至 2025-07-16 信号 ===")
print(check_df[['日期', '收盘', 'TD', 'TK', '扬帆起航', '避风靠岸']].to_string(index=False))
