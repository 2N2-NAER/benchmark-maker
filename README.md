# Benchmark Maker · AI 专项评估集合成管线

输入问题文档，让 AI 拆解能力、生成检索词、检索带 caption 的素材库，并合成漫剧/电商 benchmark。**主入口为 MCP 插件或 Python CLI，运行不需要前端。**

AI 负责问题理解、任务规划、素材选择、Prompt 和 checkpoint。程序负责文档解析、素材检索、引用校验、进度保存和导出。保留的 `public/` 与 Node 服务只是旧版可选预览，不参与核心管线。

## 方式一：AI 自身作为合成主体（MCP，推荐）

需要 Python 3.10+，标准库实现，无需 pip install，也无需额外配置模型 Key。由宿主 AI 使用自己的推理能力调用以下工具：

1. `read_problem_document`：读取问题文档。
2. 宿主 AI 根据文档拆解任务，生成覆盖矩阵及中英文检索词。
3. `search_materials`：按任务查询本地带 caption 的素材索引，返回真实素材、来源和缺失用途。
4. 宿主 AI 根据检索结果选择素材，合成不同的用户输入 Prompt、参考绑定和 1～3 条 checkpoint。
5. `export_benchmark`：校验引用、首尾帧分组、数量、重复 Prompt 和参数，输出候选 benchmark。

在支持本地 stdio MCP 的 AI 客户端中添加以下配置。将路径替换为项目克隆后的绝对路径；不依赖客户端工作目录。

```json
{
  "mcpServers": {
    "benchmark-maker": {
      "command": "python3",
      "args": ["/absolute/path/to/benchmark-maker/run_mcp.py"]
    }
  }
}
```

这是可接入 MCP 客户端的工具服务，不代表已经安装成当前 ChatGPT 的云端插件。

配置后可以对 AI 说：

> 使用 benchmark-maker，读取 /data/badcase.md，针对漫剧和电商生成 60 条流体专项候选 benchmark。素材库为 /data/assets.json。覆盖眼泪、口水、海水和精华液，保留首帧、首尾帧、对象参考三种输入方式。根据素材 caption 选择合理组合，不够的部分标记缺失，不虚构素材。输出到 /data/runs/fluid-001。

## 方式二：配置模型 API，全流程命令行运行

```bash
export BM_LLM_ENDPOINT='https://your-gateway.example/v1/chat/completions'
export BM_LLM_MODEL='your-model'
export BM_LLM_API_KEY='your-key'

python3 -m benchmark_maker run examples/problem.md \
  --assets /data/assets.json \
  --out runs/fluid-001 \
  --count 60 --domain 双业务
```

Key 通过环境变量传递，不保存到运行产物。`.env.example` 仅为变量说明，程序不自动加载 `.env`。模型端点接收问题文档、检索到的 caption 与素材元数据；仅配置你认可的服务。

支持 `--domain 漫剧` / `电商` / `双业务`。使用 `--examples /data/user-prompts.md` 加入真实用户输入样例以指导表达方式。运行失败后保留已完成批次：

```bash
python3 -m benchmark_maker run examples/problem.md \
  --assets /data/assets.json --out runs/fluid-001 \
  --count 60 --domain 双业务 --resume
```

恢复要求文档、素材、参数、样例、模型和端点一致。改变输入后应使用新目录。模型无效 JSON 最多修复一次；网络失败不自动重复付费请求。语义/结构不合格的结果保存为候选或报错，不悄悄改成规则模板。

## 分步命令（适合脚本、Agent 和人工接管）

```bash
python3 -m benchmark_maker extract /data/badcase.docx --out runs/source.json
# AI 阅读 source.json 后写 plan.json
python3 -m benchmark_maker search --plan runs/plan.json \
  --assets /data/assets.json --out runs/retrieval.json
# AI 阅读 retrieval.json 后写 cases.json
python3 -m benchmark_maker finalize --plan runs/plan.json \
  --assets /data/assets.json --cases runs/cases.json --out runs/final
```

`finalize` 在有结构阻断或数量不符时退出码为 2，但仍保留报告；正常运行不代表候选已完成人工验收。

文档支持 UTF-8 的 Markdown、TXT、JSON、JSONL、CSV、DOCX；PDF 需要系统安装 Poppler 的 `pdftotext`。扫描 PDF 需先 OCR。单文档限制 50 MiB/16 万字符，超出明确报错，不静默截断。

## 数据契约

素材库支持 JSON、JSONL、CSV。JSON 可为数组或 `{"assets": [...]}`。见 `examples/assets.json`，示例中的 URL 是占位符，需替换为真实媒体。

```json
{
  "id": "serum-first-001",
  "role": "首帧",
  "domain": "电商",
  "url": "https://your-media.example/first.jpg",
  "caption": "滴管悬在手背上方，尖端挂着一滴透明精华液。",
  "tags": ["精华液", "serum", "drop"],
  "groupId": "serum-clip-001",
  "source": "数据集名称、原始ID及使用许可",
  "verified": false
}
```

用途：角色图、商品图、场景图、道具图、关键帧、首帧、尾帧、参考视频、参考音频。`groupId` 声明首尾帧属于同一连续片段；同组不等于已验证可过渡。`verified` 只接受 true 或 CSV 的 `true`，默认未核验。

计划格式：

```json
{"summary":"流体连续性问题","tasks":[{
  "id":"T01","name":"精华液从滴管滴落到手背","domain":"电商",
  "ability":"流体连续性与接触","mode":"首尾帧",
  "queries":["精华液 滴落 手背", "serum drop hand"],
  "count":1,"difficulty":"基础"
}]}
```

Case 格式：

```json
{"cases":[{
  "id":"C01","task_id":"T01","domain":"电商","mode":"首尾帧",
  "type":"用户场景","duration":8,"aspect":"16:9",
  "prompt":"以{pic-01}为首帧、{pic-02}为尾帧，固定近景，精华液从滴管滴到手背。",
  "bindings":[
    {"asset_id":"serum-first-001","ref":"pic-01","purpose":"首帧，锁定滴落前状态"},
    {"asset_id":"serum-last-001","ref":"pic-02","purpose":"尾帧，锁定液滴接触手背后的状态"}
  ],
  "checkpoints":["液滴从滴管下落并接触手背","运动过程中液滴没有突然消失"]
}]}
```

AI 只能引用检索返回的素材 ID，URL 由程序解析填入导出表。缺失素材不会被自动造图或伪造 URL。可以传入多个角色、商品、场景、道具、关键帧和声音绑定。

## 输出与可追溯性

完整运行输出：

```text
manifest.json          输入指纹、运行状态及模型
01_document.json       文档提取结果
02_plan.json           AI 覆盖方案
03_retrieval.json      每个任务的素材候选、相关性和缺口
batches/               分任务 AI 合成结果，支持恢复
benchmark.json         候选 Case、素材索引及来源信息
benchmark.csv          一素材一列，保留完整 Prompt 与 checkpoint
validation.json        阻断问题、未核验警告及数量检查
```

所有结果始终标为候选；不会把没有结构性错误的 Case 当作正式通过的评估集。源文档、用户样例和中间产物可能包含业务数据，`runs/` 已默认忽略，勿提交到仓库。

## 当前边界

- 检索已实现本地 caption/tag 的中英文 token 匹配，AI 生成多语言检索词并选择素材；不是向量检索服务，也不是公网数据集爬虫。
- 不自动下载素材、不检查远端 URL、不自动提帧/切片，也不声称读取过媒体像素。首尾帧、关键帧和商品图需预先入库。
- 文档/字幕/caption 都作为数据处理。caption 可能错误，人物身份、商品一致性和首尾帧过渡仍需核验。
- checkpoint 的可观察性、难度、业务分布与流体物理是否合理，需要人工校准；不包含视频生成试跑和评分。

## 测试与 Docker

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
# 旧前端的可选检查
npm run check && npm test

docker build -t benchmark-maker .
# MCP stdio（保持stdin打开）
docker run --rm -i -v /data:/data benchmark-maker mcp
# API 自动运行
# /data目录需对容器app用户可写
docker run --rm --env-file /secure/model.env -v /data:/data benchmark-maker \
  run /data/badcase.md --assets /data/assets.json --out /data/runs/fluid-001
```

Docker 默认主入口为 Python 管线。Node 前端预览仍可通过 `npm start` 启动，但核心合成不依赖它。

## 许可

项目尚未指定开源许可证；公开可读不自动授予再许可。素材数据遵循其各自授权，不随代码分发。
