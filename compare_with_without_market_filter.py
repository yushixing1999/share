
import pandas as pd

# Read both result files
original = pd.read_csv('backtest_results.csv')
with_filter = pd.read_csv('backtest_results_with_market_filter.csv')

print("="*80)
print("回测结果对比（无大盘过滤 vs 有大盘过滤）")
print("="*80)

for phase in ['牛市', '震荡', '熊市']:
    print(f"\n【{phase}】")
    orig_phase = original[original['阶段'] == phase]
    with_phase = with_filter[with_filter['阶段'] == phase]
    
    print(f"  无过滤 - 平均胜率: {orig_phase['胜率'].mean():.2f}%, 平均总收益: {orig_phase['总收益'].mean():.2f}%, 平均最大回撤: {orig_phase['最大回撤'].mean():.2f}%")
    print(f"  有过滤 - 平均胜率: {with_phase['胜率'].mean():.2f}%, 平均总收益: {with_phase['总收益'].mean():.2f}%, 平均最大回撤: {with_phase['最大回撤'].mean():.2f}%")
    print(f"  变化   - 胜率: {with_phase['胜率'].mean()-orig_phase['胜率'].mean():+.2f}%, 总收益: {with_phase['总收益'].mean()-orig_phase['总收益'].mean():+.2f}%, 回撤: {with_phase['最大回撤'].mean()-orig_phase['最大回撤'].mean():+.2f}%")

print("\n" + "="*80)
