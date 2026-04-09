
import pandas as pd

# Read both versions
v1 = pd.read_csv('sh999999_backtest_results_v1.csv')
v2 = pd.read_csv('sh999999_backtest_results_v2.csv')

print("="*80)
print("上证指数回测参数对比")
print("="*80)
print("  v1: 短期 KDJ (9,3,3), 中期 KDJ (21,3,5)")
print("  v2: 短期 KDJ (7,3,3), 中期 KDJ (38,5,10)")
print("="*80)

for phase in ['牛市', '震荡', '熊市']:
    print(f"\n【{phase}】")
    v1_phase = v1[v1['阶段'] == phase].iloc[0]
    v2_phase = v2[v2['阶段'] == phase].iloc[0]
    
    print(f"  总收益: v1={v1_phase['总收益']}%, v2={v2_phase['总收益']}%, 变化={v2_phase['总收益']-v1_phase['总收益']:.2f}%")
    print(f"  胜率: v1={v1_phase['胜率']}%, v2={v2_phase['胜率']}%, 变化={v2_phase['胜率']-v1_phase['胜率']:.2f}%")
    print(f"  最大回撤: v1={v1_phase['最大回撤']}%, v2={v2_phase['最大回撤']}%, 变化={v2_phase['最大回撤']-v1_phase['最大回撤']:.2f}%")
    print(f"  年化收益: v1={v1_phase['年化收益']}%, v2={v2_phase['年化收益']}%, 变化={v2_phase['年化收益']-v1_phase['年化收益']:.2f}%")
    print(f"  交易次数: v1={v1_phase['交易次数']}, v2={v2_phase['交易次数']}, 变化={v2_phase['交易次数']-v1_phase['交易次数']}")

print("\n" + "="*80)
