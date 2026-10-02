import { app } from "../../scripts/app.js";

/**
 * skills管理器节点前端扩展。
 *
 * - 「刷新skills」按钮：调用后端 POST /ytmmi/skills/list 重新扫描
 *   skills/（内置）与 custom_skills/（自定义）目录，并更新「选择skills」下拉选项；
 * - 下拉选项更新使用「原地修改 values 数组」（splice），兼容新前端
 *   Vue 响应式渲染（整体替换 options 对象会断开响应式引用导致不刷新）；
 * - 「附加说明」默认填充「仅输出提示词正文」的强调说明（来自 Python 端 default）：
 *   切换到非提示词类 skills 时自动清空，切回时自动恢复；
 *   若用户已改成自定义内容则一律不动，避免覆盖用户输入。
 */
app.registerExtension({
  name: "YTmmi.SkillsManager",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "SkillsManagerNode") return;

    // 提示词书写类 skills 的识别标记（与 Python 端 PROMPT_WRITING_SKILL_MARKERS 一致）
    const PROMPT_WRITING_MARKERS = ["prompt-writing", "prompt_writing"];
    const AUTO_SELECTION = "自动";

    // 「附加说明」的默认强调说明：直接取 Python 端 INPUT_TYPES 的 default，避免硬编码漂移
    const defaultNote =
      nodeData?.input?.optional?.["附加说明"]?.[1]?.default ?? "";

    const isPromptWritingSkill = function (value) {
      const v = String(value || "").trim().toLowerCase();
      if (!v) return false;
      return PROMPT_WRITING_MARKERS.some((m) => v.includes(m));
    };

    /**
     * 同步「附加说明」：
     * - 需要强调（自动 / 提示词书写类）且当前为空 → 填入默认强调说明；
     * - 不需要强调且当前恰好等于默认强调说明（用户未改）→ 清空；
     * - 用户自定义的内容永不覆盖。
     */
    const syncExtraNote = function (node) {
      if (!defaultNote) return;
      const skillsWidget = node.widgets?.find((w) => w.name === "选择skills");
      const noteWidget = node.widgets?.find((w) => w.name === "附加说明");
      if (!noteWidget) return;

      const value = String(noteWidget.value ?? "");
      const wantsNote =
        skillsWidget?.value === AUTO_SELECTION ||
        isPromptWritingSkill(skillsWidget?.value);

      if (wantsNote) {
        if (!value.trim()) {
          noteWidget.value = defaultNote;
          node.setDirtyCanvas?.(true);
        }
        return;
      }
      // 不需要强调：仅当内容就是默认说明（未被用户改写）时才清空
      if (value.trim() === defaultNote.trim()) {
        noteWidget.value = "";
        node.setDirtyCanvas?.(true);
      }
    };

    /**
     * 安全更新 combo 下拉选项（新前端 Vue 响应式渲染）：
     * 1. 若 values 为响应式数组，原地 splice 触发重渲染（官方模式）；
     * 2. 同时替换 options 引用兜底（非响应式路径）。
     */
    const setComboOptions = function (widget, values) {
      if (!widget) return;
      const cur = widget.options?.values;
      if (Array.isArray(cur)) {
        cur.splice(0, cur.length, ...values);
      }
      widget.options = { ...(widget.options || {}), values: [...values] };
    };

    // 保留当前选中值（若已不在新列表中则补入），避免刷新后选项丢失
    const withCurrentValue = function (widget, names) {
      const cur = widget?.value;
      if (cur && !names.includes(cur)) return [...names, cur];
      return names;
    };

    nodeType.prototype.refreshSkills = async function () {
      const combo = this.widgets?.find((w) => w.name === "选择skills");
      if (!combo) return;
      try {
        const resp = await fetch("/ytmmi/skills/list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        const data = await resp.json();
        if (!resp.ok) {
          alert("刷新skills失败：" + (data.error || resp.status));
          return;
        }
        const names = data.names || [];
        if (!names.length) {
          alert(
            "未发现任何 skills。\n" +
              "请在插件的 skills/ 或 custom_skills/ 目录下添加包含 SKILL.md 的子目录后重试。"
          );
        }
        setComboOptions(combo, withCurrentValue(combo, names));
        this.setDirtyCanvas(true);
        if (names.length) {
          alert(`已发现 ${names.length} 个 skills，请在「选择skills」下拉中选择`);
        }
      } catch (e) {
        alert("刷新skills失败：" + (e.message || e));
      }
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);

      // 「刷新skills」按钮：不参与序列化，避免保存工作流时写入 null
      const btn = this.addWidget("button", "刷新skills", null, () => {
        this.refreshSkills();
      });
      btn.serialize = false;

      // 「选择skills」切换时同步「附加说明」
      const skillsCombo = this.widgets?.find((w) => w.name === "选择skills");
      if (skillsCombo) {
        const self = this;
        const originalCallback = skillsCombo.callback;
        // 必须用 function（而非箭头函数）：箭头函数没有自己的 arguments，
        // 会错误地捕获外层 onNodeCreated 的参数，导致原回调收到错误入参。
        skillsCombo.callback = function (...args) {
          const res = originalCallback?.apply(this, args);
          syncExtraNote(self);
          return res;
        };
      }

      // 节点创建后刷新一次，与磁盘上的 skills 目录保持同步
      setTimeout(() => this.refreshSkills(), 300);
      // 多次时机同步「附加说明」，兼容不同前端的控件值恢复时机
      syncExtraNote(this);
      setTimeout(() => syncExtraNote(this), 100);
      setTimeout(() => syncExtraNote(this), 500);

      return r;
    };

    // 加载工作流后控件值按保存内容恢复，需再次同步
    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = originalOnConfigure?.apply(this, arguments);
      setTimeout(() => syncExtraNote(this), 0);
      return r;
    };
  },
});
