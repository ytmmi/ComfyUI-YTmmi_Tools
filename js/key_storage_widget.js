import { app } from "../../scripts/app.js";

/**
 * 密钥储存器节点前端扩展。
 *
 * 「选择密钥」为节点定义（INPUT_TYPES）中的正式下拉：
 * - 下拉列出已加密保存的密钥名称，选择后自动回填到「名称」；
 * - 「保存」按钮：将「名称 / 密钥 / 接口地址」POST 到后端加密存储，
 *   保存成功后自动刷新「选择密钥」下拉；
 * - 加载/刷新时若当前值不在下拉选项中，自动补入，避免 "Value not in list"。
 */
app.registerExtension({
  name: "YTmmi.KeyStorage",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "KeyStorageNode") return;

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

    // 将「选择密钥」的当前值补入选项列表（防 Value not in list）
    const ensureValueInOptions = function (node) {
      const combo = node.widgets?.find((w) => w.name === "选择密钥");
      if (!combo || !combo.value) return;
      const vals = combo.options?.values;
      if (!Array.isArray(vals) || vals.includes(combo.value)) return;
      vals.push(combo.value);
      node.setDirtyCanvas?.(true);
    };

    nodeType.prototype.refreshSavedNames = async function () {
      const combo = this.widgets?.find((w) => w.name === "选择密钥");
      if (!combo) return;
      try {
        const resp = await fetch("/ytmmi/keys/list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        const data = await resp.json();
        const names = data.names || [];
        const values = names.includes(combo.value)
          ? names
          : combo.value
            ? [...names, combo.value]
            : names;
        setComboOptions(combo, values);
        this.setDirtyCanvas(true);
      } catch (e) {
        console.error("加载密钥列表失败:", e);
      }
    };

    nodeType.prototype.saveKey = async function () {
      const nameWidget = this.widgets?.find((w) => w.name === "名称");
      const keyWidget = this.widgets?.find((w) => w.name === "密钥");
      const urlWidget = this.widgets?.find((w) => w.name === "接口地址");
      if (!nameWidget || !keyWidget || !urlWidget) return;

      const name = (nameWidget.value || "").trim();
      const key = (keyWidget.value || "").trim();
      const baseUrl = (urlWidget.value || "").trim();
      if (!name) {
        alert("请填写名称");
        return;
      }
      if (!key) {
        alert("请填写密钥");
        return;
      }
      if (!baseUrl) {
        alert("请填写接口地址");
        return;
      }

      try {
        const resp = await fetch("/ytmmi/keys/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 名称: name, 密钥: key, 接口地址: baseUrl }),
        });
        const data = await resp.json();
        if (!resp.ok) {
          alert("保存失败：" + (data.error || resp.status));
          return;
        }
        // 保存成功后刷新「选择密钥」下拉，并回填选中值
        const combo = this.widgets?.find((w) => w.name === "选择密钥");
        if (combo) {
          const names = data.names || [];
          setComboOptions(combo, names);
          combo.value = names.includes(name) ? name : combo.value;
          combo.callback?.(combo.value);
        }
        this.setDirtyCanvas(true);
        alert(`已保存「${name}」`);
      } catch (e) {
        alert("保存失败：" + (e.message || e));
      }
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);

      // 给「选择密钥」正式下拉挂回调：选择后回填「名称」
      const combo = this.widgets?.find((w) => w.name === "选择密钥");
      if (combo) {
        combo.callback = (value) => {
          const nameWidget = this.widgets?.find((w) => w.name === "名称");
          if (nameWidget && value) {
            nameWidget.value = value;
            this.setDirtyCanvas(true);
          }
        };
      }

      // 「保存」按钮
      const btn = this.addWidget("button", "保存", null, () => {
        this.saveKey();
      });
      btn.serialize = false;

      // 多次时机处理：防 Value not in list + 刷新列表
      ensureValueInOptions(this);
      setTimeout(() => ensureValueInOptions(this), 100);
      setTimeout(() => this.refreshSavedNames(), 300);
      setTimeout(() => this.refreshSavedNames(), 1000);
      return r;
    };
  },
});
