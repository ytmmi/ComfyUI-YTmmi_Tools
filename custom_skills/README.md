# 自定义 skills

在此目录下为每个 skills 建立独立子目录，并至少放入一个 `SKILL.md`。

- skills 目录在 ComfyUI 加载插件时被扫描，新增或修改 skills 后请重启 ComfyUI，
  或点击「skills管理器」节点上的「刷新skills」按钮重新扫描。
- skills id（目录名，或 `SKILL.md` front matter 中的 `name`）只能包含小写字母、
  数字、点、下划线与连字符，且不能为 `auto`。
- 内置 `skills/` 目录中的 skills 优先；`custom_skills/` 中同 id 的 skills 不会覆盖内置。
- 本目录下的 skills 仅作为模型提示词指导，节点不会执行其中声明的脚本、工具、
  网络调用或审批流程。

## 目录结构示例

```text
custom_skills/
  cinematic-food/
    SKILL.md
    meta.yaml          # 可选
    references/        # 可选，.md / .txt 会被一并读取
      shot-guidelines.md
```

## SKILL.md 示例

```markdown
---
name: cinematic-food
description: 把食材与菜品描述改写为电影感美食短视频提示词。
version: 1.0.0
---

# Cinematic Food

## 工作流

1. 提取菜品主体、材质与光线条件。
2. 按「镜头 → 动作 → 声音」顺序组织描述。
```

`meta.yaml` 可选，用于提供中英文显示名与标签，例如：

```yaml
display-name-zh: 电影感美食
display-name-en: Cinematic Food
version: 1.0.0
tag-cn: 美食
tag-en: Food
summary-cn: 把菜品描述改写为电影感美食短视频提示词。
summary-en: Rewrite dish descriptions into cinematic food short-video prompts.
```

## 使用方式

1. 在 ComfyUI 中添加「skills管理器」节点（分类 `YTmmi/utility`）；
2. 在「选择skills」下拉中选择本目录下的 skills；
3. 将输出的 `skills` 接入「自定义LLM」节点的 `skills` 输入接口。
