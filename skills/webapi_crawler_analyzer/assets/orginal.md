# skill.md

## 技能名称
**`webapi_crawler_analyzer`**

## 功能描述
智能识别网页中可爬取的WebAPI端点，支持自然语言交互指令，能处理动态内容、分页场景，并在找不到API时回退到HTML解析。该技能优先分析XHR请求，通过LLM辅助判断最符合用户需求的数据源。

## 输入参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `instructions` | string | 是 | 用户自然语言指令，包含URL和操作描述（如："打开https://example.com，搜索框输入'手机'，点击搜索按钮"） |
| `data_description` | string | 是 | 需提取的数据描述（如"商品名称、价格、库存状态"） |
| `max_depth` | integer | 否 | 最大爬取深度（默认=1，0表示仅当前页面） |
| `confirm_each_depth` | boolean | 否 | 是否每层深度向用户确认（默认=true） |
| `include_pagination` | boolean | 否 | 是否将分页链接视为下一层（默认=false） |

## 处理流程
### 阶段1: 页面加载与交互
1. **URL提取**：从用户指令中提取目标URL
2. **交互操作**：
   - 启动Playwright无头浏览器
   - 将页面截图/HTML摘要和用户指令送入LLM的thinking模式
   - LLM生成具体操作步骤（如：`page.fill('#search-box', 'playwright')`，`page.click('button.execute')`）
   - 执行操作并等待网络请求完成
3. **请求捕获**：
   - 拦截所有网络请求和响应
   - 按类型分类：Document > XHR/Fetch > Script > 其他

### 阶段2: API智能分析
1. **初步过滤**：
   - 优先分析XHR/Fetch类型请求
   - 仅保留成功响应(200-299)且Content-Type为JSON/text的请求
2. **LLM辅助匹配**（两阶段）：
   - **第一阶段**：LLM生成grep-like搜索指令，筛选出N个候选API
     ```markdown
     # LLM思考示例
     grep -i "price\|product\|item" responses/*.json --max-count=5
     ```
   - **第二阶段**：LLM逐条分析候选API，评估与`data_description`的匹配度
     ```markdown
     # 评估标准
     1. 字段名称匹配度（如"price" vs "商品价格"）
     2. 数据结构规范性（JSON > text > HTML）
     3. 数据量充足性（单条记录 vs 列表）
     ```
3. **分页特殊处理**：
   - 检测URL模式：`?page=`, `?p=`, `/page/数字`
   - 识别分页API：包含`pagination`、`total_pages`等字段
   - **默认行为**：不将分页链接加入下一层，而是分析分页API本身

### 阶段3: 数据提取策略
1. **首选方案**：直接使用匹配的WebAPI（提供完整URL和参数）
2. **备选方案**（无API时）：
   - 使用BeautifulSoup解析HTML
   - LLM生成CSS选择器或XPath路径
   - 示例：`soup.select('div.product-list .item')`
3. **深度爬取控制**：
   - 当`max_depth > 0`时，提取页面内链接
   - **排除**：分页链接、外部域名、已访问URL
   - 达到深度限制时暂停，等待用户确认

## 输出格式
```json
{
  "execution_summary": "成功执行2个交互步骤，捕获15个网络请求",
  "recommended_apis": [
    {
      "url": "https://api.example.com/search",
      "method": "POST",
      "priority_score": 0.95,
      "matched_fields": ["name", "price", "stock_status"],
      "sample_data": [{"name": "商品A", "price": 199, ...}],
      "direct_use_example": "curl -X POST https://api.example.com/search -d '{\"query\":\"playwright\"}'"
    }
  ],
  "fallback_html_selectors": {
    "if_no_api": [
      {"element": "商品名称", "selector": ".product-title", "example": "<div class='product-title'>智能手表</div>"},
      {"element": "价格", "selector": ".price-value", "example": "<span class='price-value'>¥299</span>"}
    ]
  },
  "next_actions": {
    "requires_confirmation": true,
    "available_depth_links": [
      {"url": "https://example.com/product/123", "context": "商品详情页"},
      {"url": "https://example.com/product/456", "context": "商品详情页"}
    ],
    "pagination_api_detected": "https://api.example.com/products?page=2"
  }
}
```

## 工作原理
### 智能请求分析
- **优先级队列**：Document > XHR > Script > 其他，打破常规爬虫从HTML开始的模式
- **语义匹配**：不依赖简单关键词，而是理解数据结构和上下文
- **分页优化**：将分页视为同一数据源的不同请求，而非新页面

### 交互操作机制
1. LLM将自然语言指令转换为Playwright操作序列：
   ```markdown
   用户指令："在搜索框中输入playwright，点击excute按钮"
   ↓
   LLM生成操作：
   1. page.wait_for_selector('#search-box')
   2. page.fill('#search-box', 'playwright')
   3. page.click('button:has-text("execute")')
   4. page.wait_for_load_state('networkidle')
   ```

### 无API回退策略
当没有找到合适API时：
1. LLM分析HTML结构，识别数据容器
2. 生成针对性CSS选择器
3. 提供示例代码：
   ```python
   from bs4 import BeautifulSoup
   soup = BeautifulSoup(html_content, 'html.parser')
   items = soup.select('div.skill-item')
   for item in items:
       name = item.select_one('.skill-name').text.strip()
       # ... 其他字段提取
   ```

## 使用示例
### 示例1：带交互的API发现
**用户输入**：
```
instructions: "打开https://skillsmp.com/zh/search，搜索框输入'playwright'，点击execute按钮"
data_description: "技能名称、作者、下载次数"
max_depth: 0
```

**执行过程**：
1. 加载页面，执行搜索操作
2. 捕获到XHR请求：`https://api.skillsmp.com/search?q=playwright`
3. LLM分析响应，确认包含所需字段
4. 跳过深度爬取(max_depth=0)

**输出摘要**：
```json
{
  "recommended_apis": [{
    "url": "https://api.skillsmp.com/search",
    "matched_fields": ["skill_name", "author", "downloads"],
    "direct_use_example": "curl 'https://api.skillsmp.com/search?q=playwright'"
  }]
}
```

### 示例2：分页场景处理
**用户输入**：
```
instructions: "访问https://example-commerce.com/products"
data_description: "所有商品的名称和价格"
max_depth: 1,
include_pagination: false
```

**执行过程**：
1. 分析XHR请求，发现`/api/products?page=1`包含商品数据
2. 检测到分页参数，自动分析总页数
3. **不分页链接加入下一层**，而是提供完整爬取方案：
   ```markdown
   for page in range(1, total_pages+1):
       response = requests.get(f"/api/products?page={page}")
   ```

### 示例3：无API时的HTML解析
**用户输入**：
```
instructions: "打开https://legacy-website.com/listings"
data_description: "联系人电话和地址"
```

**执行过程**：
1. 未找到匹配的XHR/API请求
2. LLM分析HTML结构，生成CSS选择器
3. 提取关键元素位置

**输出摘要**：
```json
{
  "fallback_html_selectors": {
    "if_no_api": [
      {"element": "电话", "selector": ".contact-info .phone"},
      {"element": "地址", "selector": ".contact-info .address"}
    ]
  },
  "extraction_code_template": "soup.select('.listing-item') → 遍历提取"
}
```

## 限制与注意事项
1. **动态内容限制**：高度依赖JavaScript渲染的页面可能需要定制交互脚本
2. **反爬机制**：不处理验证码、IP封禁等反爬措施
3. **数据量控制**：单次分析最多处理50个候选API，避免LLM过载
4. **隐私合规**：自动跳过包含`/auth/`、`/login/`等敏感路径的请求
5. **性能边界**：单页面分析超时时间=30秒，深度爬取建议分批次进行

> **提示**：对于复杂网站，可先用`max_depth=0`分析当前页API，再决定是否深入爬取。分页场景建议直接使用检测到的分页API，而非逐页点击。
