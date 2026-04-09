
import pandas as pd
import matplotlib.pyplot as plt
from backtest_strategy_with_market_filter import calculate_indicators

# Read data
df = pd.read_csv('stock_data.csv')

# Filter for 天孚通信 (300394)
stock_code = 300394
stock_df = df[df['股票代码'] == stock_code].copy()

# Calculate indicators
stock_df = calculate_indicators(stock_df)

# Filter for a period, say 牛市 (2025-05-01 to 2025-10-31)
phase_start = pd.to_datetime('2025-05-01')
phase_end = pd.to_datetime('2025-10-31')
mask = (stock_df['日期'] >= phase_start) & (stock_df['日期'] <= phase_end)
plot_df = stock_df[mask].copy()

# Create plot
plt.figure(figsize=(16, 8))

# Plot closing price
plt.plot(plot_df['日期'], plot_df['收盘'], label='收盘价', color='blue', linewidth=2)

# Plot buy signals (扬帆起航)
buy_signals = plot_df[plot_df['扬帆起航'] == True]
plt.scatter(buy_signals['日期'], buy_signals['收盘'], color='red', marker='^', s=100, label='扬帆起航 (买入)')

# Plot sell signals (避风靠岸)
sell_signals = plot_df[plot_df['避风靠岸'] == True]
plt.scatter(sell_signals['日期'], sell_signals['收盘'], color='green', marker='v', s=100, label='避风靠岸 (卖出)')

# Formatting
plt.title(f'天孚通信 ({stock_code}) - 2025/5/1 - 2025/10/31', fontsize=16)
plt.xlabel('日期', fontsize=12)
plt.ylabel('价格', fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Save plot
plt.savefig('tianfutongxin_chart.png', dpi=300)
print("Plot saved to tianfutongxin_chart.png")
