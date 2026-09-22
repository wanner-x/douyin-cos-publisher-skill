# douyin-cos-publisher-skill

一个面向 Codex 的抖音 COS 图文发布 Skill。它把素材盘点、角色分组、文案与 Tag 生成、客户端填充、用户确认、发布后验收、合集核验和原图归档串成一条可追踪的工作流。

它重点解决这些容易出错的环节：

- 发布按钮已点击，但作品仍在“审核中”；
- 正文在编辑器里存在，成品却缺失；
- 直接输入的 `#文字` 没有成为真正的话题实体；
- 抖音最多 5 个话题，二次元内容却漏掉 `二次元`；
- 只看到“第 N 集”就误以为合集已经归类；
- 发布结果尚未验收，就提前移动了原图；
- 客户端已经登录，却错误切换到网页要求重新登录。

## 工作流

每个批次必须按状态依次推进：

```text
方案已生成
  → 草稿已填充
  → 用户已确认
  → 已提交
  → 已发布验收通过
  → 合集验收通过
  → 素材已归档
```

1. 只读扫描素材，根据角色、服装和场景做视觉分组。
2. 为全部批次生成图片顺序、标题、正文、5 个 Tag、配乐和目标合集。
3. 在已登录的抖音桌面客户端填写草稿，并检查图片、封面、正文、话题实体、配乐和权限。
4. 冻结最终发布清单；在点击发布的紧邻步骤取得用户确认。
5. 每个批次只点击一次发布。结果未知时去内容管理核对，不直接重试。
6. 作品必须在内容管理中明确显示“已发布”，并核对正文和 5 个话题。
7. 进入合集管理，确认合集数量变化或最新作品匹配，且状态为“通过/已发布”。
8. 只有用户授权归档且两道验收均通过，才能移动该批次的精确原文件。

## 关键约束

- 优先使用已经登录的抖音桌面客户端。
- 公开发布、修改公开作品和上传素材前遵守 Codex 的确认要求。
- 每条作品固定 5 个 Tag；二次元内容必须包含 `二次元`。
- Tag 必须从发布页候选列表中逐个选中；普通 `#文字` 不算生效。
- “正在发布”“审核中”和结果未知都不能触发素材归档。
- 归档时禁止宽泛通配符，必须核对精确文件名和目标目录冲突。
- 发布异常时不自动修改已公开作品，也不重复提交。

## 安装

将 `douyin-cos-publisher` 目录复制到 Codex Skills 目录：

```bash
cp -R douyin-cos-publisher ~/.codex/skills/
```

安装后可这样调用：

```text
使用 $douyin-cos-publisher 处理待发布图片，先生成全部发布方案。
```

使用前请编辑 `douyin-cos-publisher/references/account.md`，配置目标账号、素材目录、归档目录和账号中的真实合集名称。

## 文案协作

如果本机安装了 `cos-douyin-wanxiang`，本 Skill 会优先用它生成或复核文案、Tag 候选和配乐；发布 Skill 仍负责话题实体化、确认、发布和事后验收。没有安装时，也可以直接使用本 Skill 的基础文案规则。

## 素材盘点脚本

```bash
python3 douyin-cos-publisher/scripts/prepare_media.py \
  --source "/absolute/path/to/pending-media" \
  --manifest /tmp/douyin-media.json \
  --contact-sheet /tmp/douyin-contact-sheet.jpg
```

生成联系表需要 Pillow；仅生成清单时不强制依赖 Pillow。

## 仓库结构

```text
douyin-cos-publisher/
├── SKILL.md
├── agents/openai.yaml
├── references/account.md
├── references/publish-ui.md
└── scripts/prepare_media.py
```

## 说明

抖音客户端界面、审核状态和曲库会变化。Skill 要求每次根据当前可见界面重新定位和核验，不复用旧坐标或把历史曲目可用性当作当前事实。它不会绕过登录验证、验证码或平台风控。

## License

MIT
