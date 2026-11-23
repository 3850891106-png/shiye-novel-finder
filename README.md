# 拾页

用剧情、人物、章节标题和曾用名，找回那本记不清名字的小说。

## 线上架构

- 前端：原生 HTML、CSS、JavaScript，部署到 GitHub Pages。
- 搜索与社区：Supabase PostgREST API。
- 数据库：Supabase PostgreSQL，使用 `pg_trgm` 做中文模糊匹配。
- 数据量：4,679 本穿越小说，33 本可自动识别曾用名或别名。
- 降级策略：Supabase 未配置或临时不可用时，前端自动使用内置示例库。

页面不包含小说正文，也不提供正文、网盘或下载资源。

## 本地预览

可直接打开 `index.html`，或在本目录运行：

```bash
python3 -m http.server 4173
```

访问 `http://127.0.0.1:4173/`。

## Supabase 初始化

1. 在 Supabase 创建项目。
2. 在 SQL Editor 执行 `supabase/schema.sql`。
3. 准备 `SUPABASE_URL` 与 `SUPABASE_SERVICE_ROLE_KEY` 环境变量。
4. 导入 4,679 本小说：

```bash
python3 scripts/import_novels.py
```

导入脚本采用 `source_seq` upsert，重复执行不会产生重复书目。不要在浏览器、GitHub 或聊天中暴露 `SUPABASE_SERVICE_ROLE_KEY`。

## GitHub Pages 部署

仓库的 `.github/workflows/pages.yml` 会在每次推送到 `main` 时构建并部署 `dist/`。

`config.js` 中的 Supabase URL 与 `anon` 密钥可以公开，因为它们只用于访问受行级权限保护的公开数据。也可以在仓库的 `Settings → Secrets and variables → Actions` 添加：

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

`SUPABASE_ANON_KEY` 是公开客户端密钥，但仍通过构建步骤生成，避免把不同环境的配置写死在源码里。数据库安全由 Supabase 行级权限策略保证。

随后在 `Settings → Pages → Build and deployment` 选择 **GitHub Actions**。

## 数据导入

原始数据来自工作区中的香书小说公开页面汇总：

- `香书小说_穿越小说汇总.csv`
- 第 1—6 册 Excel 分册

导入前会规整以下字段：

- 书名、作者、分类、状态、更新时间
- 最新章节、前 100 章章节名
- 角色候选、小说简介、穿越判定依据
- 详情页来源链接
- 从简介中的“原名《…》”“又名《…》”等表述自动抽出的别名

## 数据库权限

- `novels`：匿名用户只读。
- `novel_requests`：匿名用户可以提交并读取已发布寻书帖，不能修改或删除。
- 线索长度限制为 10—600 字，昵称限制为 30 字。
- `service_role` 只用于管理端导入，不进入网页代码。

## 后续增强

1. 增加管理员审核和垃圾信息限制。
2. 把正文向量检索用于剧情相似度，减少单纯关键词匹配。
3. 增加同书不同来源合并、人工别名校验和错误反馈。
4. 接入正版阅读平台搜索入口。
