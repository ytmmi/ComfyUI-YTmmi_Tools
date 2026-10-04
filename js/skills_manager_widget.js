import { app } from "../../scripts/app.js";

/**
 * skills管理器节点前端扩展。
 *
 * - 「刷新skills」按钮：调用后端 POST /ytmmi/skills/list 重新扫描
 *   skills/（内置）与 custom_skills/（自定义）目录，并更新「选择skills」下拉选项；
 * - **不弹窗**：刷新结果（成功/失败）只通过「按钮文字短暂变化 + 控制台日志」反馈，
 *   不使用 alert / confirm / 自绘模态框，避免打断工作流操作；失败时按钮短暂变红提示，
 *   详细信息写在 console.warn 中（F12 可见）；
 * - 下拉选项更新使用「原地修改 values 数组」（splice），兼容新前端
 *   Vue 响应式渲染（整体替换 options 对象会断开响应式引用导致不刷新）；
 * - 「附加说明」按所选 skills 套用对应的默认强调说明（后端按 skills 返回 extra_note）：
 *   产出单一交付物的提示词类 skills（含散文与 JSON）用「只输出最终内容、不要开头说明
 *   与结尾建议」的强调；Anima 家族用「两段式 Positive/Negative」专属强调；
 *   风格类 skills 留空；切换 skills 时自动替换；
 *   若用户已改成自定义内容则一律不动，避免覆盖用户输入；
 * - 「选择skills」与「模式」联动：只有「选择skills」= 自动 时「模式」才生效。
 *   一旦选了具体 skills，自动把「模式」切回 auto（即"无筛选"），因为此时由该
 *   skills 自身决定输出，模式已无意义；切回「自动」时保留用户原来的模式选择。
 */
app.registerExtension({
  name: "YTmmi.SkillsManager",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "SkillsManagerNode") return;

    const AUTO_SELECTION = "自动";
    const MODE_AUTO = "auto"; // 与 Python 端 MODE_AUTO 一致

    // 按钮文字反馈的停留时间（毫秒）
    const STATUS_HOLD_MS = 2200;

    // 「附加说明」的兜底默认值：取 Python 端 INPUT_TYPES 的 default（自动模式通用强调）
    const fallbackNote =
      nodeData?.input?.optional?.["附加说明"]?.[1]?.default ?? "";

    // 各 skills 对应的默认强调说明（由后端 /ytmmi/skills/list 填充）。
    // 同时记录所有「已知默认值」，用于判断控件内容是否为默认值（而非用户自定义）。
    let noteBySkill = {};
    let autoNote = fallbackNote;
    const knownDefaults = new Set();
    if (fallbackNote.trim()) knownDefaults.add(fallbackNote.trim());

    const registerDefault = function (note) {
      const v = String(note ?? "").trim();
      if (v) knownDefaults.add(v);
    };

    // 期望的强调说明：自动模式用通用强调，具体 skills 用其后端 extra_note
    const expectedNote = function (skillValue) {
      const v = String(skillValue ?? "").trim();
      if (!v || v === AUTO_SELECTION) return autoNote;
      return noteBySkill[v] ?? "";
    };

    // 内容是否属于「已知默认值」（含空串）——用于区分默认值与用户自定义
    const isKnownDefault = function (value) {
      const v = String(value ?? "").trim();
      return v === "" || knownDefaults.has(v);
    };

    /**
     * 同步「附加说明」：
     * - 当前内容是已知默认值（含空）→ 替换为所选 skills 期望的强调说明；
     * - 用户自定义内容 → 永不覆盖。
     */
    const syncExtraNote = function (node) {
      const skillsWidget = node.widgets?.find((w) => w.name === "选择skills");
      const noteWidget = node.widgets?.find((w) => w.name === "附加说明");
      if (!noteWidget) return;

      const value = String(noteWidget.value ?? "");
      if (!isKnownDefault(value)) return; // 用户自定义内容，不动

      const wanted = expectedNote(skillsWidget?.value);
      if (value.trim() !== String(wanted ?? "").trim()) {
        noteWidget.value = wanted;
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

    /**
     * 按钮文字反馈（替代弹窗）：
     * - 成功：绿色文字「✓ …」，失败：红色文字「✗ …」，约 2.2 秒后恢复原文字；
     * - 同时写控制台日志，详细信息可在 F12 查看，不打断画布操作；
     * - 只改按钮 label/color（LiteGraph 官方按钮控件属性），并在原控件已带
     *   text_color 时才同步文字色——避免给非按钮控件塞未知属性。
     */
    const flashStatus = function (node, text, ok) {
      const btn = node.__ytmmiRefreshBtn;
      if (!btn) return;
      if (btn.__ytmmiRestoreTimer) {
        clearTimeout(btn.__ytmmiRestoreTimer);
        btn.__ytmmiRestoreTimer = null;
      }
      if (!btn.__ytmmiBaseLabel) btn.__ytmmiBaseLabel = btn.label || "刷新skills";
      btn.label = text;
      btn.color = ok ? "#3f9c53" : "#c0392b";
      if ("text_color" in btn) {
        btn.text_color = "#ffffff";
      }
      node.setDirtyCanvas?.(true);
      btn.__ytmmiRestoreTimer = setTimeout(() => {
        btn.label = btn.__ytmmiBaseLabel;
        btn.color = undefined;
        if ("text_color" in btn) btn.text_color = undefined;
        btn.__ytmmiRestoreTimer = null;
        node.setDirtyCanvas?.(true);
      }, STATUS_HOLD_MS);
    };

    const logInfo = function (message, detail) {
      if (detail === undefined) console.info(`[skills管理器] ${message}`);
      else console.info(`[skills管理器] ${message}`, detail);
    };

    const logError = function (message, detail) {
      if (detail === undefined) console.warn(`[skills管理器] ${message}`);
      else console.warn(`[skills管理器] ${message}`, detail);
    };

    /**
     * 「选择skills」与「模式」联动：
     * - 选了具体 skills → 「模式」切回 auto（模式仅在自动下有意义）；
     * - 切回「自动」→ 恢复用户此前选择的模式（未记录过则保持 auto）。
     *
     * 同时维护「模式」控件的可编辑性提示：非自动时模式已失效，但仍保留可点开，
     * 避免用户误以为控件损坏。
     */
    const syncModeLinkage = function (node) {
      const skillsWidget = node.widgets?.find((w) => w.name === "选择skills");
      const modeWidget = node.widgets?.find((w) => w.name === "模式");
      if (!skillsWidget || !modeWidget) return;

      const isAuto = skillsWidget.value === AUTO_SELECTION;
      if (isAuto) {
        // 切回自动：恢复此前的模式选择
        const remembered = node.__ytmmiLastMode;
        const target = remembered || MODE_AUTO;
        if (modeWidget.value !== target) {
          modeWidget.value = target;
          node.setDirtyCanvas?.(true);
        }
        return;
      }

      // 选了具体 skills：记住当前模式（供切回自动时恢复），再把模式切回 auto
      if (modeWidget.value !== MODE_AUTO) {
        node.__ytmmiLastMode = modeWidget.value;
        modeWidget.value = MODE_AUTO;
        node.setDirtyCanvas?.(true);
      }
    };

    // 保留当前选中值（若已不在新列表中则补入），避免刷新后选项丢失
    const withCurrentValue = function (widget, names) {
      const cur = widget?.value;
      if (cur && !names.includes(cur)) return [...names, cur];
      return names;
    };

    /**
     * 重新扫描 skills 目录并更新下拉选项。
     *
     * 全程不弹窗：
     * - 成功：按钮显示「✓ N 个 skills」并写 console.info；
     * - 失败：按钮显示「✗ 刷新失败」并写 console.warn（含具体原因）；
     * - 未发现任何 skills：按钮显示「✗ 未发现 skills」并写 console.warn（含放置说明）。
     */
    nodeType.prototype.refreshSkills = async function (options) {
      const opts = options || {};
      const quiet = Boolean(opts.quiet); // 初始化时的静默刷新不改变按钮文字
      const combo = this.widgets?.find((w) => w.name === "选择skills");
      if (!combo) return;
      try {
        const resp = await fetch("/ytmmi/skills/list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          const reason = data?.error || `HTTP ${resp.status}`;
          logError(`刷新skills失败：${reason}`);
          if (!quiet) flashStatus(this, "✗ 刷新失败", false);
          return;
        }
        const names = data.names || [];

        // 记录每个 skills 的默认强调说明，并登记所有已知默认值
        const nextNoteBySkill = {};
        for (const item of data.skills || []) {
          if (!item?.id) continue;
          const note = String(item.extra_note ?? "");
          nextNoteBySkill[item.id] = note;
          registerDefault(note);
        }
        noteBySkill = nextNoteBySkill;
        if (data.auto_extra_note !== undefined) {
          autoNote = String(data.auto_extra_note ?? "");
          registerDefault(autoNote);
        }

        setComboOptions(combo, withCurrentValue(combo, names));
        // 选项更新后同步「附加说明」，使新选中 skills 的强调说明立即生效
        syncExtraNote(this);
        this.setDirtyCanvas(true);

        if (!names.length) {
          logError(
            "未发现任何 skills。请在插件的 skills/ 或 custom_skills/ 目录下" +
              "添加包含 SKILL.md 的子目录后重试。"
          );
          if (!quiet) flashStatus(this, "✗ 未发现 skills", false);
          return;
        }

        logInfo(`已发现 ${names.length} 个 skills，请在「选择skills」下拉中选择`, names);
        if (!quiet) flashStatus(this, `✓ 已发现 ${names.length} 个`, true);
      } catch (e) {
        const reason = e?.message || e;
        logError(`刷新skills失败：${reason}`, e);
        if (!quiet) flashStatus(this, "✗ 刷新失败", false);
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
      // 供 flashStatus 复用（按钮文字/颜色反馈替代弹窗）
      this.__ytmmiRefreshBtn = btn;

      // 「选择skills」切换时：联动「模式」并同步「附加说明」
      const skillsCombo = this.widgets?.find((w) => w.name === "选择skills");
      if (skillsCombo) {
        const self = this;
        const originalCallback = skillsCombo.callback;
        // 必须用 function（而非箭头函数）：箭头函数没有自己的 arguments，
        // 会错误地捕获外层 onNodeCreated 的参数，导致原回调收到错误入参。
        skillsCombo.callback = function (...args) {
          const res = originalCallback?.apply(this, args);
          syncModeLinkage(self);
          syncExtraNote(self);
          return res;
        };
      }

      // 「模式」切换时记录用户选择（供切回「自动」时恢复）
      const modeCombo = this.widgets?.find((w) => w.name === "模式");
      if (modeCombo) {
        const self = this;
        const originalModeCallback = modeCombo.callback;
        modeCombo.callback = function (...args) {
          const res = originalModeCallback?.apply(this, args);
          if (modeCombo.value && modeCombo.value !== MODE_AUTO) {
            self.__ytmmiLastMode = modeCombo.value;
          }
          return res;
        };
      }

      // 节点创建后刷新一次，与磁盘上的 skills 目录保持同步（静默：不改按钮文字）
      setTimeout(() => this.refreshSkills({ quiet: true }), 300);
      // 多次时机同步「模式」联动与「附加说明」，兼容不同前端的控件值恢复时机
      syncModeLinkage(this);
      syncExtraNote(this);
      setTimeout(() => {
        syncModeLinkage(this);
        syncExtraNote(this);
      }, 100);
      setTimeout(() => {
        syncModeLinkage(this);
        syncExtraNote(this);
      }, 500);

      return r;
    };

    // 加载工作流后控件值按保存内容恢复，需再次同步
    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = originalOnConfigure?.apply(this, arguments);
      setTimeout(() => {
        syncModeLinkage(this);
        syncExtraNote(this);
      }, 0);
      return r;
    };
  },
});
