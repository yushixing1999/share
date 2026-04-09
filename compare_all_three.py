
import pandas as pd

# Read all three result files
original = pd.read_csv('backtest_results.csv')
with_filter = pd.read_csv('backtest_results_with_market_filter.csv')
buy_and_hold = pd.read_csv('buy_and_hold_results.csv')

print("="*100)
print("三者对比：无大盘过滤 vs 有大盘过滤 vs 一直持有")
print("="*100)

for phase in ['牛市', '震荡', '熊市']:
    print(f"\n【{phase}】")
    orig_phase = original[original['阶段'] == phase]
    with_phase = with_filter[with_filter['阶段'] == phase]
    bh_phase = buy_and_hold[buy_and_hold['阶段'] == phase]
    
    print(f"  无过滤    - 胜率: {orig_phase['胜率'].mean():.2f}%, 总收益: {orig_phase['总收益'].mean():.2f}%, 最大回撤: {orig_phase['最大回撤'].mean():.2f}%")
    print(f"  有过滤    - 胜率: {with_phase['胜率'].mean():.2f}%, 总收益: {with_phase['总收益'].mean():.2f}%, 最大回撤: {with_phase['最大回撤'].mean():.2f}%")
    print(f"  一直持有  - 胜率: N/A, 总收益: {bh_phase['总收益'].mean():.2f}%, 最大回撤: {bh_phase['最大回撤'].mean():.2f}%")
    
    print(f"\n  有过滤 vs 无过滤 - 胜率: {with_phase['胜率'].mean()-orig_phase['胜率'].mean():+.2f}%, 总收益: {with_phase['总收益'].mean()-orig_phase['总收益'].mean():+.2f}%, 回撤: {with_phase['最大回撤'].mean()-orig_phase['最大回撤'].mean():+.2f}%")
    print(f"  有过滤 vs 一直持有 - 总收益: {with_phase['总收益'].mean()-bh_phase['总收益'].mean():+.2f}%, 回撤: {with_phase['最大回撤'].mean()-bh_phase['最大回撤'].mean():+.2f}%")

print("\n" + "="*100)
