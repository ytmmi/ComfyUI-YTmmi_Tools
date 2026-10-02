import { app } from "../../scripts/app.js";

/**
 * skills管理器节点前端扩展。
 *
 * - 「刷新skills」按钮：调用后端 POST /ytmmi/skills/list 重新扫描
 *   skills/（内置）与 custom_skills/（自定义）目录，并更新「选择skills」下拉选项；
 * - 下拉选项更新使用「原地修改 values 数组」（splice），兼容新前端
 *   Vue 响应式渲染（整体替换 options 对象会断开响应式引用导致不刷新）。
 */
app.registerExtension({
  name: "YTmmi.SkillsManager",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "SkillsManagerNode") return;

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

      // 节点创建后刷新一次，与磁盘上的 skills 目录保持同步
      setTimeout(() => this.refreshSkills(), 300);

      return r;
    };
  },
});
