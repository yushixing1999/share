
import pandas as pd

# Read the trades file
trades_df = pd.read_csv('backtest_trades_with_market_filter_and_add_to_position.csv')

# Filter for 天孚通信 (300394)
stock_code = 300394
stock_trades = trades_df[trades_df['股票代码'] == stock_code]

print("天孚通信 (300394) 交易记录：")
print(stock_trades[['日期', '阶段', '类型', '价格', '数量', '利润', '利润率']].to_string(index=False))
