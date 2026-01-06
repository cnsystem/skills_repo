---
name: akshare
description: AKShare是一个开源的金融数据接口库，提供超过1000个API接口，涵盖股票、基金、期货、债券、外汇、指数、宏观数据等各类金融数据。该skill提供AKShare API的使用指南和调用方法，支持金融数据查询、分析和可视化。
---

# AKShare 金融数据 API Skill

## 概述

AKShare 是一个开源的金融数据接口库，提供超过1000个API接口，涵盖股票、基金、期货、债券、外汇、指数、宏观数据等各类金融数据。本skill为用户提供AKShare API的使用指南，帮助用户查询和分析金融数据。

## 使用场景

- 查询股票历史行情和实时数据
- 获取基金、期货、债券等金融产品信息
- 分析宏观经济数据
- 获取指数和板块数据
- 金融数据可视化和分析

## API分类和使用方法

### 1. 股票数据 (Stock Data)

#### A股历史行情
- **函数名**: `stock_zh_a_hist`
- **功能**: 获取A股历史行情数据
- **必需参数**: `symbol` (股票代码，如 "600519")
- **可选参数**:
  - `period` (周期: "daily", "weekly", "monthly")
  - `start_date` (开始日期: "YYYYMMDD")
  - `end_date` (结束日期: "YYYYMMDD")
  - `adjust` (复权方式: "", "qfq", "hfq")
- **示例**: `stock_zh_a_hist(symbol="600519", period="daily", start_date="20240101", end_date="20241231")`

#### A股实时行情
- **函数名**: `stock_zh_a_spot_em`
- **功能**: 获取A股实时行情数据
- **参数**: 无
- **示例**: `stock_zh_a_spot_em()`

#### 个股信息
- **函数名**: `stock_individual_info_em`
- **功能**: 获取个股详细信息
- **必需参数**: `symbol` (股票代码)
- **示例**: `stock_individual_info_em(symbol="600519")`

### 2. 指数数据 (Index Data)

#### 指数日线行情
- **函数名**: `stock_zh_index_daily`
- **功能**: 获取指数日线行情
- **必需参数**: `symbol` (指数代码，如 "sh000001")
- **示例**: `stock_zh_index_daily(symbol="sh000001")`

#### 指数历史行情
- **函数名**: `index_zh_a_hist`
- **功能**: 获取指数历史行情数据
- **必需参数**: `symbol` (指数代码)
- **可选参数**: `period`, `start_date`, `end_date`
- **示例**: `index_zh_a_hist(symbol="000001", start_date="20240101")`

### 3. 基金数据 (Fund Data)

#### ETF实时行情
- **函数名**: `fund_etf_spot_em`
- **功能**: 获取ETF基金实时行情
- **参数**: 无
- **示例**: `fund_etf_spot_em()`

#### 开放式基金信息
- **函数名**: `fund_open_fund_info_em`
- **功能**: 获取开放式基金详细信息
- **必需参数**: `fund` (基金代码)
- **示例**: `fund_open_fund_info_em(fund="000001")`

### 4. 期货数据 (Futures Data)

#### 期货主力合约
- **函数名**: `futures_main_sina`
- **功能**: 获取期货主力合约数据
- **参数**: 无
- **示例**: `futures_main_sina()`

#### 期货实时行情
- **函数名**: `futures_zh_spot`
- **功能**: 获取期货实时行情
- **可选参数**: `symbol` (合约代码)
- **示例**: `futures_zh_spot(symbol="M2401")`

### 5. 债券数据 (Bond Data)

#### 国债收益率
- **函数名**: `bond_china_yield`
- **功能**: 获取中国国债收益率数据
- **必需参数**: `start_date`, `end_date`
- **示例**: `bond_china_yield(start_date="20240101", end_date="20240131")`

### 6. 外汇数据 (Forex Data)

#### 人民币汇率
- **函数名**: `fx_cny_spot_sina`
- **功能**: 获取人民币汇率中间价
- **参数**: 无
- **示例**: `fx_cny_spot_sina()`

### 7. 宏观经济数据 (Macroeconomic Data)

#### GDP数据
- **函数名**: `macro_china_gdp_yearly`
- **功能**: 获取中国GDP年度数据
- **参数**: 无
- **示例**: `macro_china_gdp_yearly()`

#### CPI数据
- **函数名**: `macro_china_cpi_yearly`
- **功能**: 获取中国CPI年度数据
- **参数**: 无
- **示例**: `macro_china_cpi_yearly()`

## 重要参数格式说明

1. **日期格式**: "YYYYMMDD" (如 "20240101")
2. **股票代码**: 6位数字 (如 "000001", "600519")
3. **指数代码**: "sh" + 6位数字 (如 "sh000001") 或 "sz" + 6位数字 (如 "sz399001")
4. **基金代码**: 6位数字 (如 "000001")

## API调用示例

当用户需要获取金融数据时，可以使用以下JSON格式进行API调用：

```json
{
  "function_name": "stock_zh_a_hist",
  "params": {
    "symbol": "600519",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20241231"
  }
}
```

## 使用建议

- 对于历史股价查询，使用 `stock_zh_a_hist`
- 对于实时行情概览，使用 `stock_zh_a_spot_em`
- 对于个股基本信息，使用 `stock_individual_info_em`
- 对于指数数据，使用 `stock_zh_index_daily` 或 `index_zh_a_hist`
- 对于基金数据，使用 `fund_etf_spot_em` 或 `fund_open_fund_info_em`
- 对于宏观经济分析，使用 `macro_china_gdp_yearly`, `macro_china_cpi_yearly` 等函数

## 注意事项

- 某些函数可能需要特定的参数才能正常工作
- 部分API可能有访问频率限制
- 历史数据的可用性取决于数据源
- 日期范围不能超过数据源提供的范围
- 部分数据可能有延迟，实时数据仅供参考
