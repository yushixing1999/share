
import pandas as pd
import numpy as np

def calculate_buy_and_hold(df, stock_code, stock_name):
    """计算一直持有的收益"""
    df = df.copy()
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 定义三个市场阶段
    phases = {
        '牛市': ('2025-05-01', '2025-10-31'),
        '震荡': ('2024-11-01', '2025-04-01'),
        '熊市': ('2024-05-20', '2024-09-12')
    }
    
    results = []
    
    for phase_name, (start_date, end_date) in phases.items():
        phase_start = pd.to_datetime(start_date)
        phase_end = pd.to_datetime(end_date)
        
        mask = (df['日期'] >= phase_start) & (df['日期'] <= phase_end)
        phase_df = df[mask].copy()
        
        if len(phase_df) < 2:
            continue
        
        # Buy at first open, sell at last close
        first_open = phase_df.iloc[0]['开盘']
        last_close = phase_df.iloc[-1]['收盘']
        
        if pd.notna(first_open) and pd.notna(last_close) and first_open > 0 and last_close > 0:
            total_return = (last_close - first_open) / first_open * 100
            
            # Max drawdown
            phase_df['累计最高'] = phase_df['收盘'].cummax()
            phase_df['回撤'] = (phase_df['累计最高'] - phase_df['收盘']) / phase_df['累计最高'] * 100
            max_drawdown = phase_df['回撤'].max()
            
            results.append({
                '股票代码': stock_code,
                '股票名称': stock_name,
                '阶段': phase_name,
                '类型': '一直持有',
                '总收益': round(total_return, 2),
                '最大回撤': round(max_drawdown, 2),
                '买入价格': round(first_open, 2),
                '卖出价格': round(last_close, 2)
            })
    
    return results

def main():
    # Read data
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
    
    all_bh_results = []
    
    stock_groups = df.groupby('股票代码')
    
    for stock_code, group in stock_groups:
        if stock_code == 999999:
            continue
        stock_name = stock_names.get(stock_code, f'股票{stock_code}')
        bh_results = calculate_buy_and_hold(group, stock_code, stock_name)
        all_bh_results.extend(bh_results)
    
    # Save buy-and-hold results
    bh_df = pd.DataFrame(all_bh_results)
    bh_df.to_csv('buy_and_hold_results.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("一直持有回测完成！")
    print("="*80)
    
    # Compare with strategy results
    print("\n" + "="*80)
    print("对比：策略 vs 一直持有")
    print("="*80)
    
    # Read strategy results
    strat_df = pd.read_csv('backtest_results_with_market_filter.csv')
    
    for phase in ['牛市', '震荡', '熊市']:
        print(f"\n【{phase}】")
        strat_phase = strat_df[strat_df['阶段'] == phase]
        bh_phase = bh_df[bh_df['阶段'] == phase]
        
        if len(strat_phase) > 0 and len(bh_phase) > 0:
            print(f"  策略平均总收益: {strat_phase['总收益'].mean():.2f}%")
            print(f"  一直持有平均总收益: {bh_phase['总收益'].mean():.2f}%")
            print(f"  策略平均最大回撤: {strat_phase['最大回撤'].mean():.2f}%")
            print(f"  一直持有平均最大回撤: {bh_phase['最大回撤'].mean():.2f}%")
            print(f"  超额收益: {strat_phase['总收益'].mean()-bh_phase['总收益'].mean():+.2f}%")

if __name__ == '__main__':
    main()
