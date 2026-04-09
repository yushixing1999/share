
import pandas as pd

# Read the trades file with add-to-position
trades_df = pd.read_csv('backtest_trades_with_market_filter_and_add_to_position.csv')

# Check 天孚通信 (300394)
stock_code = 300394
stock_trades = trades_df[trades_df['股票代码'] == stock_code]

print(f"股票代码: {stock_code}")
print("交易记录:")
print(stock_trades[['日期', '阶段', '类型', '价格', '数量', '利润', '利润率']])

# Also check how many "加仓" trades there are in total
print("\n--- 全市场加仓统计 ---")
add_trades = trades_df[trades_df['类型'] == '加仓']
print(f"总加仓次数: {len(add_trades)}")
if len(add_trades) > 0:
    print("加仓记录:")
    print(add_trades[['股票代码', '股票名称', '日期', '阶段', '价格', '数量']])
