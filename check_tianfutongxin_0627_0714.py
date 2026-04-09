
import pandas as pd
from backtest_strategy_with_market_filter import calculate_indicators

# Read data
df = pd.read_csv('stock_data.csv')
stock_code = 300394
stock_df = df[df['股票代码'] == stock_code].copy()
stock_df = calculate_indicators(stock_df)

# Check dates 2025-06-20 to 2025-07-20
check_start = pd.to_datetime('2025-06-20')
check_end = pd.to_datetime('2025-07-20')
mask = (stock_df['日期'] >= check_start) & (stock_df['日期'] <= check_end)
check_df = stock_df[mask].copy()

# Also read the trades
trades_df = pd.read_csv('backtest_trades_with_market_filter_and_add_to_position.csv')
stock_trades = trades_df[trades_df['股票代码'] == stock_code]
stock_trades['日期'] = pd.to_datetime(stock_trades['日期'])

print("=== 天孚通信 2025-06-20 至 2025-07-20 信号与交易 ===")
print("\n--- 信号数据 ---")
print(check_df[['日期', '收盘', 'TD', 'TK', '扬帆起航', '避风靠岸']].to_string(index=False))

print("\n--- 同期交易记录 ---")
trades_in_range = stock_trades[(stock_trades['日期'] >= check_start) & (stock_trades['日期'] <= check_end)]
print(trades_in_range[['日期', '阶段', '类型', '价格', '数量', '利润']].to_string(index=False))
