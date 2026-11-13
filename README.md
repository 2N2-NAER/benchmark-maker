# Benchmark Foundry

面向漫剧和电商视频生成的 Badcase 专项评估集合成工作台。输入能力问题，编辑覆盖方案，匹配素材，生成 Prompt 与 checkpoint，经审核导出 CSV/JSON。

## 快速启动

需要 Node.js 20 或更新版本，无第三方依赖，无需 npm install。

```bash
npm start
```

打开 http://localhost:4173 。Linux/macOS 可通过 `PORT=8080 npm start` 修改端口；Windows PowerShell 使用 `$env:PORT=8080; npm start`。

```bash
npm run check
npm test
```

## Docker

```bash
docker build -t benchmark-foundry .
docker run --rm -p 4173:4173 benchmark-foundry
```

## 使用流程

1. 在「专项合成」输入 Badcase，选择业务、Case 数、时长、画幅和输入模式。
2. 生成并编辑覆盖方案。规则模式覆盖流体、交互、一致性和镜头；其他问题可手工编辑或连接大模型。
3. 在「素材库」导入 JSON/CSV，或手工添加真实媒体 URL、caption、用途和来源。
4. 回到覆盖方案生成候选集。在「候选评估集」补齐绑定、编辑 Prompt/checkpoint、核验素材后审核。
5. 导出候选 CSV，或仅导出审核通过且无结构性阻断的 CSV。JSON 包含素材索引及 Case 元数据。
6. 使用「备份项目」保存浏览器数据，换浏览器或更换部署地址后用「恢复项目」导入。

## 素材格式

见 [examples/assets.json](examples/assets.json)。其中 URL 为明确占位符，必须替换为真实素材后使用。

- 必填：`role`、`url`、`caption`。
- `role`：角色图、商品图、场景图、道具图、关键帧、首帧、尾帧、参考视频、参考音频。
- `domain`：漫剧、电商、通用。
- `groupId`：首尾帧必须填写同组标识；标识相同只表示声明了关联，仍需人工验证连续性。
- `verified`：默认 false，查看素材并核验内容后再改为 true。
- `source`：记录数据集名称、原始ID和许可。

导入会拒绝非法用途、缺少 caption 或非 HTTP(S) URL 的记录，并报告数量。素材库只保存索引，不上传或托管媒体。

## 大模型接口

在「接口与配置」填写完整的 Chat Completions URL、模型名称和当前会话的 API Key，可执行覆盖方案拆解和单 Case 改写。可填写真实用户 Prompt 样例以指导风格。请求从浏览器直连所填服务，该服务必须允许跨域访问。API Key 不写入 localStorage 或项目备份；刷新页面后需重新输入。

## 素材检索接口

配置自有检索服务 URL，工作台发送：

```json
{"query":"流体效果差", "domain":"双业务", "limit":100}
```

返回素材数组或 `{"assets": [...]}`，素材字段与导入格式一致。当前无内置数据集爬取器、向量检索服务或服务端凭据代理。

## 已实现和边界

已实现：规则覆盖方案、素材索引管理、按 caption 的基础匹配、候选合成、单 Case 编辑与模型改写、素材核验标记、首尾帧组检查、引用检查、审核导出和浏览器备份。

规则模板生成的同类任务可能相似，当前不代表严格采样的真实用户分布。checkpoint 是候选检查点，需要人工校准。匹配 caption 不等于素材内容正确；“无结构性阻断”也不等于已检查媒体可访问性或任务质量。

尚未实现：数据集自动下载、视频切片与提帧、自动音视频理解、跨素材身份验证、向量数据库、生成模型批量试跑、自动评分、多用户云端数据同步。素材链接、许可与实际内容需自行核验。

## 数据与部署

项目是静态前端，加一个零依赖静态文件服务。数据保存在当前浏览器 origin 的 localStorage，不保存到 Node 服务。`/healthz` 用于运行检测。`public/` 可部署到任意静态托管服务。Node 服务仅开放静态文件和健康检查，不包含用户认证；部署到外部网络时需自行按场景添加访问控制。

## 目录

```text
public/           页面、样式、前端与合成规则
server.mjs        独立静态文件服务
examples/         素材字段示例
 tests/           核心逻辑和服务测试
.github/workflows/ GitHub CI
```

## 许可

本项目尚未指定开源许可证。不要将第三方数据集、实际媒体、用户任务、API Key 或个人数据提交到仓库。素材数据的授权与应用代码分别管理。
