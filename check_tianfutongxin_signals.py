
import pandas as pd
from backtest_strategy_with_market_filter import calculate_indicators

# Read data
df = pd.read_csv('stock_data.csv')
stock_code = 300394
stock_df = df[df['股票代码'] == stock_code].copy()
stock_df = calculate_indicators(stock_df)

# Check dates around 2025-06-27 and 2025-07-14
check_start = pd.to_datetime('2025-06-20')
check_end = pd.to_datetime('2025-07-20')
mask = (stock_df['日期'] >= check_start) & (stock_df['日期'] <= check_end)
check_df = stock_df[mask].copy()

print(check_df[['日期', '收盘', 'TD', 'TK', '扬帆起航', '避风靠岸']].to_string(index=False))
