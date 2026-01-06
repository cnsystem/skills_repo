#!/usr/bin/env python3
"""
AKShare API 使用示例脚本
该脚本演示了如何使用AKShare库获取各种金融数据
"""

import akshare as ak


def get_stock_history(symbol="600519", period="daily", start_date="20240101", end_date="20241231"):
    """
    获取A股历史行情数据
    :param symbol: 股票代码
    :param period: 周期
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: DataFrame
    """
    try:
        data = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        return data
    except Exception as e:
        print(f"获取股票历史数据失败: {e}")
        return None


def get_stock_realtime():
    """
    获取A股实时行情数据
    :return: DataFrame
    """
    try:
        data = ak.stock_zh_a_spot_em()
        return data
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return None


def get_fund_etf():
    """
    获取ETF基金实时行情
    :return: DataFrame
    """
    try:
        data = ak.fund_etf_spot_em()
        return data
    except Exception as e:
        print(f"获取ETF数据失败: {e}")
        return None


def get_macro_gdp():
    """
    获取中国GDP年度数据
    :return: DataFrame
    """
    try:
        data = ak.macro_china_gdp_yearly()
        return data
    except Exception as e:
        print(f"获取GDP数据失败: {e}")
        return None


def get_index_history(symbol="000001", start_date="20240101"):
    """
    获取指数历史行情数据
    :param symbol: 指数代码
    :param start_date: 开始日期
    :return: DataFrame
    """
    try:
        data = ak.index_zh_a_hist(
            symbol=symbol,
            start_date=start_date
        )
        return data
    except Exception as e:
        print(f"获取指数历史数据失败: {e}")
        return None


if __name__ == "__main__":
    print("AKShare API 使用示例:")
    
    # 获取贵州茅台历史数据
    print("\n1. 获取贵州茅台(600519)历史行情:")
    stock_data = get_stock_history("600519")
    if stock_data is not None:
        print(stock_data.head())
    
    # 获取ETF基金数据
    print("\n2. 获取ETF基金实时行情:")
    etf_data = get_fund_etf()
    if etf_data is not None:
        print(f"ETF数量: {len(etf_data)}")
        print(etf_data.head())
    
    # 获取GDP数据
    print("\n3. 获取中国GDP年度数据:")
    gdp_data = get_macro_gdp()
    if gdp_data is not None:
        print(gdp_data.tail())
    
    # 获取上证指数历史数据
    print("\n4. 获取上证指数历史行情:")
    index_data = get_index_history("000001")
    if index_data is not None:
        print(index_data.head())