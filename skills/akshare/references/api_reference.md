# AKShare API 详细参考

## 股票数据函数

### A股数据
- `stock_zh_a_hist`: A股历史行情
- `stock_zh_a_spot_em`: A股实时行情
- `stock_individual_info_em`: 个股信息
- `stock_board_industry_name_em`: 行业板块
- `stock_board_concept_name_em`: 概念板块
- `stock_new_a_spot_em`: 新股数据
- `stock_gpzy_profile_em`: 股票质押数据

### 港股数据
- `stock_hk_spot_em`: 港股实时行情
- `stock_hk_hist`: 港股历史行情

### 美股数据
- `stock_us_spot_em`: 美股实时行情
- `stock_us_hist`: 美股历史行情

## 基金数据函数

### 基金基本信息
- `fund_open_fund_info_em`: 开放式基金信息
- `fund_etf_spot_em`: ETF实时行情
- `fund_open_fund_daily_em`: 基金日净值
- `fund_portfolio_hold_em`: 基金持仓

### 基金规模数据
- `fund_scale_open_sina`: 基金规模变动

## 期货数据函数

### 期货行情
- `futures_main_sina`: 期货主力合约
- `futures_zh_spot`: 期货实时行情
- `futures_zh_daily_sina`: 期货历史日线
- `futures_sina_stock_hold_pos`: 期货持仓排名

## 债券数据函数

### 债券行情
- `bond_china_yield`: 国债收益率
- `bond_zh_hs_cov_spot`: 可转债实时行情
- `bond_cb_index_jsl`: 可转债基本信息

## 外汇数据函数

### 外汇行情
- `fx_cny_spot_sina`: 人民币汇率中间价
- `fx_spot_quote`: 外汇实时行情
- `currency_cny_sina`: 人民币汇率

## 宏观经济数据函数

### 中国经济数据
- `macro_china_gdp_yearly`: 中国GDP年度数据
- `macro_china_cpi_yearly`: 中国CPI年度数据
- `macro_china_pmi_yearly`: 中国PMI数据
- `macro_china_money_supply`: 货币供应量数据
- `macro_china_exports_yoy`: 进出口数据
- `macro_china_industrial_production_yoy`: 工业增加值

## 指数数据函数

### 指数行情
- `stock_zh_index_daily`: 指数日线行情
- `index_zh_a_hist`: 指数历史行情
- `index_global_hist_sw`: 全球指数历史数据
- `index_stock_cons`: 指数成分股

## 期权数据函数

### 期权行情
- `option_finance_board`: 期权实时行情
- `option_finance_underlying`: 期权标的资产信息

## 加密货币数据函数

### 数字货币行情
- `crypto_spot`: 数字货币现货行情
- `crypto_hist`: 数字货币历史数据

## 其他数据函数

### 财务数据
- `stock_financial_report_sina`: 股票财务报告
- `stock_hold_num_cninfo`: 股东人数数据
- `stock_institute_hold`: 机构持股数据
- `stock_margin_detail_szse`: 融资融券数据