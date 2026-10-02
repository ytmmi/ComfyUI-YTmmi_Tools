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

## 默认「附加说明」（extra-note）

「skills管理器」节点会按所选 skills 自动填充一条输出强调（抑制开头说明、结尾建议等
无关元素）。默认规则按 skills id 判断：

- id 含 `prompt`（如 `my-prompt-skill`）→ 填充该强调；
- 其余 → 留空（适用于会输出分镜、制作方案、澄清提问的流程类 skills）。

若你的 skills 需要不同的强调，可在 front matter 或 `meta.yaml` 中自行声明，**优先级高于默认规则**：

```yaml
extra-note: 【输出要求】只输出严格合法的 JSON 对象，不要输出任何说明。
```

用户在节点上改写「附加说明」后不会被自动覆盖；清空则该说明不追加。

## 使用方式

1. 在 ComfyUI 中添加「skills管理器」节点（分类 `YTmmi/utility`）；
2. 在「选择skills」下拉中选择本目录下的 skills（点击「刷新skills」可重新扫描）；
3. 将输出的 `skills` 接入「自定义LLM」节点的 `skills` 输入接口。

> 若「选择skills」选「自动」，节点只输出 skills 清单与 `READ:` 读取协议，
> 由「自定义LLM」与模型多轮按需读取正文（渐进式披露，更省上下文）。
> 此时「模式」还可按任务家族筛选清单（如只列 Qwen-Image 或 H3 家族）。
