基于您的需求，我设计了一个名为 **`webapi_crawler_analyzer`** 的技能。这个技能专注于从网页中智能识别可爬取的WebAPI端点，并处理多级页面爬取的深度控制问题。以下是完整设计（包含优化建议和未决问题说明）：

---

### **技能名称**  
`webapi_crawler_analyzer`

### **输入参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | 起始爬取的网页URL |
| `data_description` | string | 是 | 需提取的数据描述（如“商品价格、名称、库存”） |
| `max_depth` | integer | 否 | 最大爬取深度（默认=1，避免无限循环） |
| `confirm_each_depth` | boolean | 否 | 是否每层深度向用户确认（默认=true） |

### **输出结果**
```python
{
  "analyzed_apis": [  # 按优先级排序的候选API列表
    {
      "url": "https://api.example.com/data",  # API端点
      "method": "GET/POST",                   # 请求方法
      "content_type": "application/json",    # 响应类型
      "matched_keywords": ["price", "stock"], # 与data_description匹配的关键词
      "priority_level": 1,                    # 优先级(1=document, 2=XHR, 3=JS, 4=其他)
      "sample_response": "{...}"              # 截取的响应片段（脱敏）
    }
  ],
  "next_depth_links": [  # 当前深度发现的待爬链接（用于下一层）
    "https://example.com/product1",
    "https://example.com/product2"
  ],
  "requires_user_confirmation": true,  # 是否需要用户确认进入下一层
  "analysis_summary": "在XHR请求中找到匹配数据，深度1完成"  # 人类可读摘要
}
```

---

### **核心执行逻辑**
#### **1. 捕获网络请求（Playwright）**
- **技术实现**：
  ```python
  from playwright.sync_api import sync_playwright
  
  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      
      # 拦截所有请求
      requests = []
      page.on("requestfinished", lambda req: requests.append({
          "url": req.url,
          "method": req.method,
          "resource_type": req.resource_type,  # 'document','xhr','fetch','script'等
          "response": req.response().text() if req.response() else None,
          "headers": req.headers
      }))
      
      page.goto(input_url, wait_until="networkidle", timeout=30000)
      page.wait_for_timeout(2000)  # 确保动态内容加载
      browser.close()
  ```
- **优化点**：
  - 仅捕获`response`状态码为200的请求
  - 过滤静态资源（图片/css/字体文件）
  - 自动处理Cookies和Session（保持上下文）

#### **2. API优先级分析（关键步骤）**
按优先级顺序分析请求，**一旦匹配即停止当前优先级的后续分析**：
| 优先级 | 请求类型                | 匹配逻辑                                                                 |
|--------|-------------------------|--------------------------------------------------------------------------|
| 1      | **Document (HTML)**     | 检查初始HTML是否含`<script id="__NEXT_DATA__">`或内联JSON（常见于React/Next.js） |
| 2      | **XHR/Fetch**           | 筛选`content-type: application/json`，检查响应是否含`data_description`关键词 |
| 3      | **JS动态注入**          | 解析JS文件中的字符串化JSON（如`JSON.parse('{"price":100}')`）               |
| 4      | **其他文本类型**        | 处理`text/plain`/`application/text`，用正则提取结构化数据                   |

- **匹配算法**：
  ```python
  keywords = extract_keywords(data_description)  # 用NLP库提取核心词（如nltk）
  for response in priority_group:
      if any(kw in response.text.lower() for kw in keywords):
          return candidate_api  # 返回首个匹配项
  ```

#### **3. 广度优先爬取（防死循环设计）**
- **深度控制**：
  - 初始深度=0（起始页）
  - 每深入一层：`current_depth += 1`
  - 当`current_depth >= max_depth`时停止
- **用户确认机制**：
  ```python
  if confirm_each_depth and next_depth_links:
      output["requires_user_confirmation"] = True
      output["next_depth_links"] = next_depth_links[:10]  # 仅返回前10个示例
      pause_execution()  # 暂停技能，等待用户确认
  ```
- **防重复爬取**：
  - 使用Bloom Filter记录已爬URL
  - 跳过非同源链接（`urllib.parse.urlparse(url).netloc != start_domain`）

#### **4. 安全与性能优化**
- **超时熔断**：单页面分析超时15秒（可配置）
- **流量限制**：每秒最多5个请求（避免被封）
- **敏感数据过滤**：自动脱敏响应中的`password`/`token`字段
- **资源回收**：确保Playwright浏览器进程完全退出

---

### **未决问题与改进建议**
1. **动态内容处理**  
   **问题**：SPA页面（如React/Vue）的数据可能在页面交互后加载。  
   **建议**：增加`interaction_script`输入参数，允许用户注入操作脚本（如`page.click('#load-more')`）。

2. **关键词匹配精度**  
   **问题**：简单关键词匹配可能误判（如“苹果”可能指水果或公司）。  
   **建议**：集成轻量NLP模型（如spaCy）计算语义相似度，但需权衡执行速度。

3. **分页场景优化**  
   **问题**：列表页分页链接（如?page=2）可能被误判为详情页。  
   **建议**：自动识别URL模式（如`/product/\d+`），优先爬取详情页而非分页。

4. **认证支持**  
   **问题**：登录墙页面无法获取API。  
   **建议**：增加`auth_headers`输入参数，支持Bearer Token/Cookies注入。

---

### **使用示例**
**用户输入**：
```json
{
  "url": "https://example-commerce.com/products",
  "data_description": "商品名称、价格、库存状态",
  "max_depth": 2
}
```

**技能执行流程**：
1. 分析起始页 → 发现XHR请求`/api/products`含JSON数据（匹配关键词）
2. 提取页面中的商品详情链接（`/products/123`）
3. 深度=1完成 → **暂停**，返回：
   ```json
   {
     "analyzed_apis": [{"url": "/api/products", "priority_level": 2, ...}],
     "next_depth_links": ["/products/123", "/products/456", ...],
     "requires_user_confirmation": true
   }
   ```
4. 用户确认后 → 自动爬取`next_depth_links`（深度=2）
5. 最终输出所有匹配的API端点

---

### **为什么这样设计？**
1. **平衡自动化与可控性**  
   每层深度确认避免失控爬取，同时提供`max_depth`参数满足批量需求。
   
2. **优先级策略减少误判**  
   从Document→XHR→JS的顺序符合现代Web开发模式（90%+数据通过XHR加载）。

3. **资源安全**  
   通过超时/流量控制/脱敏机制，确保技能在生产环境可用。

4. **扩展性**  
   预留`interaction_script`/`auth_headers`等参数，未来可无缝支持复杂场景。

> **下一步行动**：如果您认可此设计，我可以提供完整Python实现代码（含Playwright+请求分析模块）。或针对未决问题进一步讨论优化方案？
