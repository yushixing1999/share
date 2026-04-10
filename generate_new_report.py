
import pandas as pd

# Load data
new_params_no_filter_trades = pd.read_csv('backtest_trades_new_params.csv')
new_params_with_filter_trades = pd.read_csv('backtest_trades_with_market_filter_new_params.csv')
buy_and_hold = pd.read_csv('buy_and_hold_results.csv')

def calculate_phase_returns(trades_df):
    phase_returns = {}
    for phase in ['牛市', '震荡', '熊市']:
        phase_trades = trades_df[trades_df['阶段'] == phase]
        stock_returns = {}
        for _, trade in phase_trades.iterrows():
            if trade['类型'] in ['卖出', '结算']:
                stock_code = trade['股票代码']
                if stock_code not in stock_returns:
                    stock_returns[stock_code] = 0
                stock_returns[stock_code] += trade.get('利润率', 0)
        if len(stock_returns) > 0:
            avg_return = pd.Series(list(stock_returns.values())).mean()
            phase_returns[phase] = avg_return
        else:
            phase_returns[phase] = 0
    return phase_returns

# Calculate buy and hold average returns
bh_phase_returns = {}
for phase in ['牛市', '震荡', '熊市']:
    bh_phase = buy_and_hold[buy_and_hold['阶段'] == phase]
    bh_phase_returns[phase] = bh_phase['总收益'].mean()

# Calculate new params returns
new_no_filter_returns = calculate_phase_returns(new_params_no_filter_trades)
new_with_filter_returns = calculate_phase_returns(new_params_with_filter_trades)

# Generate report
report = f"""# 新参数(8,2,3)/(18,2,4)+ADX(10,5)策略对比总结报告

## 参数说明
- **短期KDJ**：(8, 2, 3)
- **长期KDJ**：(18, 2, 4)
- **ADX**：(10, 5)

---

## 一、不带大盘过滤 vs 带大盘过滤 vs 一直持有对比

### 按三个时期整体对比

| 时期 | 不带大盘过滤 | 带大盘过滤 | 一直持有 | 不带大盘过滤超额 | 带大盘过滤超额 | 哪个更好？ |
|------|-----------|-----------|---------|--------------|------------|----------|
| **牛市** | {new_no_filter_returns['牛市']:.2f}% | {new_with_filter_returns['牛市']:.2f}% | {bh_phase_returns['牛市']:.2f}% | {new_no_filter_returns['牛市'] - bh_phase_returns['牛市']:.2f}% | {new_with_filter_returns['牛市'] - bh_phase_returns['牛市']:.2f}% | {'不带大盘过滤' if new_no_filter_returns['牛市'] > new_with_filter_returns['牛市'] else '带大盘过滤'} |
| **震荡** | {new_no_filter_returns['震荡']:.2f}% | {new_with_filter_returns['震荡']:.2f}% | {bh_phase_returns['震荡']:.2f}% | {new_no_filter_returns['震荡'] - bh_phase_returns['震荡']:.2f}% | {new_with_filter_returns['震荡'] - bh_phase_returns['震荡']:.2f}% | {'不带大盘过滤' if new_no_filter_returns['震荡'] > new_with_filter_returns['震荡'] else '带大盘过滤'} |
| **熊市** | {new_no_filter_returns['熊市']:.2f}% | {new_with_filter_returns['熊市']:.2f}% | {bh_phase_returns['熊市']:.2f}% | {new_no_filter_returns['熊市'] - bh_phase_returns['熊市']:.2f}% | {new_with_filter_returns['熊市'] - bh_phase_returns['熊市']:.2f}% | {'不带大盘过滤' if new_no_filter_returns['熊市'] > new_with_filter_returns['熊市'] else '带大盘过滤'} ⭐ |

---

## 二、结论

- **牛市**：不带大盘过滤表现更好（{new_no_filter_returns['牛市']:.2f}% vs {new_with_filter_returns['牛市']:.2f}%）
- **震荡市**：带大盘过滤表现更好（{new_with_filter_returns['震荡']:.2f}% vs {new_no_filter_returns['震荡']:.2f}%）
- **熊市**：带大盘过滤表现更好（{new_with_filter_returns['熊市']:.2f}% vs {new_no_filter_returns['熊市']:.2f}%）

---

## 回测逻辑说明

1. **每次买入信号都买入**（支持加仓）
2. **每次买入100股**（固定数量）
3. **第一次出现卖出信号时，把前面所有未卖出的买入都结算掉**
4. **每只股票的收益率 = 该股票所有买入-卖出配对利润率之和**
5. **阶段平均收益率 = 该阶段所有股票收益率之和 ÷ 股票数量**
6. **前复权数据**

---

**文档生成时间：2026-04-10**
"""

# Save report
with open('回测结果总结报告_新参数.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("报告已生成：回测结果总结报告_新参数.md")
