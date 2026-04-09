
import pandas as pd
import numpy as np
from optimize_parameters import calculate_indicators, backtest_stock

def main():
    # 读取数据
    df = pd.read_csv('stock_data.csv')
    
    # 股票名称映射
    stock_names = {
        34: '神州数码',
        703: '恒逸石化',
        807: '云铝股份',
        2273: '水晶光电',
        2432: '九安医疗',
        2466: '天齐锂业',
        2607: '中公教育',
        300394: '天孚通信',
        300750: '宁德时代',
        600519: '贵州茅台',
        600522: '中天科技',
        600875: '东方电气',
        601088: '中国神华',
        601288: '农业银行',
        601319: '中国人保',
        601857: '中国石油',
        601872: '招商轮船',
        603816: '中国人保'
    }
    
    # 最佳参数（从优化脚本得到）
    best_params = {
        'kdj_short_n': 9,
        'kdj_short_m1': 3,
        'kdj_short_m2': 3,
        'kdj_long_n': 21,
        'kdj_long_m1': 3,
        'kdj_long_m2': 5,
        'adx_n': 10,
        'adx_smooth': 6
    }
    
    all_results = []
    all_trades = []
    
    # 按股票分组回测
    stock_groups = df.groupby('股票代码')
    
    for stock_code, group in stock_groups:
        if stock_code == 999999:
            continue  # Skip market index itself
        stock_name = stock_names.get(stock_code, f'股票{stock_code}')
        print(f"正在回测: {stock_code} - {stock_name} (最佳参数)")
        
        try:
            results, df_with_indicators = backtest_stock(group, stock_code, stock_name, best_params)
            
            for phase_name, result in results.items():
                all_results.append(result)
                
                # 保存交易明细
                for trade in result.get('交易明细', []):
                    trade['股票代码'] = stock_code
                    trade['股票名称'] = stock_name
                    trade['阶段'] = phase_name
                    all_trades.append(trade)
                    
        except Exception as e:
            print(f"回测 {stock_code} 出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    results_df = pd.DataFrame(all_results)
    results_df.to_csv('backtest_results_best_params.csv', index=False, encoding='utf-8-sig')
    
    trades_df = pd.DataFrame(all_trades)
    trades_df.to_csv('backtest_trades_best_params.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("最佳参数回测完成！")
    print(f"共回测 {len(stock_groups)-1} 只股票")
    print(f"结果已保存到: backtest_results_best_params.csv 和 backtest_trades_best_params.csv")
    print("="*80)
    
    # 打印汇总结果
    print("\n" + "="*80)
    print("最佳参数回测结果汇总")
    print("="*80)
    
    for phase in ['牛市', '震荡', '熊市']:
        print(f"\n【{phase}】")
        phase_results = results_df[results_df['阶段'] == phase]
        
        if len(phase_results) > 0:
            print(f"平均胜率: {phase_results['胜率'].mean():.2f}%")
            print(f"平均总收益: {phase_results['总收益'].mean():.2f}%")
            print(f"平均最大回撤: {phase_results['最大回撤'].mean():.2f}%")
            print(f"平均年化收益: {phase_results['年化收益'].mean():.2f}%")
            
            # 收益最好的3只股票
            top3 = phase_results.nlargest(3, '总收益')
            print("\n收益 TOP 3:")
            for _, row in top3.iterrows():
                print(f"  {row['股票名称']}({row['股票代码']}): {row['总收益']:.2f}%, 胜率{row['胜率']:.2f}%")

if __name__ == '__main__':
    main()
