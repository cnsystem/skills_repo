# 金融数据分析报告模板

## 数据获取说明

本报告使用AKShare库获取数据，AKShare是一个开源的金融数据接口库，提供超过1000个API接口，涵盖股票、基金、期货、债券、外汇、指数、宏观数据等各类金融数据。

## API调用格式

```json
{
  "function_name": "函数名",
  "params": {
    "参数名": "参数值"
  }
}
```

## 常用函数

- 股票历史数据: `stock_zh_a_hist`
- 实时行情: `stock_zh_a_spot_em`
- 基金数据: `fund_etf_spot_em`
- 指数数据: `index_zh_a_hist`
- 宏观数据: `macro_china_gdp_yearly`