import { app } from "../../scripts/app.js";

/**
 * 自定义LLM节点前端扩展。
 *
 * 模型完全由「选择模型」下拉控制：
 * - 「获取模型」按钮：优先使用「选择密钥」（密钥储存器中保存的密钥，
 *   由后端解密），否则使用手动填写的 API密钥/接口地址，调用后端
 *   POST /ytmmi/llm/models 拉取模型列表并填充「选择模型」下拉；
 * - 「选择密钥」下拉：选择后自动调用后端 POST /ytmmi/keys/get 解密，
 *   回填「API密钥」「接口地址」；
 * - 下拉选项更新使用「原地修改 values 数组」（splice），兼容新前端
 *   Vue 响应式渲染（整体替换 options 对象会断开响应式引用导致不刷新）。
 */
app.registerExtension({
  name: "YTmmi.CustomLLM",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "CustomLLMNode") return;

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

    // 将控件的当前值补入选项列表（防 Value not in list）
    const ensureValueInOptions = function (node) {
      for (const name of ["选择模型", "选择密钥"]) {
        const widget = node.widgets?.find((w) => w.name === name);
        if (!widget || !widget.value) continue;
        const vals = widget.options?.values;
        if (!Array.isArray(vals) || vals.includes(widget.value)) continue;
        vals.push(widget.value);
        node.setDirtyCanvas?.(true);
      }
    };

    // 刷新「选择密钥」下拉选项（与密钥储存器同步，无需刷新页面）
    nodeType.prototype.refreshKeyNames = async function () {
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

    // 选择「选择密钥」后回填 API密钥/接口地址
    nodeType.prototype.fillKeyFromVault = async function (name) {
      if (!name) return;
      try {
        const resp = await fetch("/ytmmi/keys/get", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 名称: name }),
        });
        const data = await resp.json();
        if (!resp.ok) {
          alert("读取密钥失败：" + (data.error || resp.status));
          return;
        }
        const apiKeyWidget = this.widgets?.find((w) => w.name === "API密钥");
        const baseUrlWidget = this.widgets?.find((w) => w.name === "接口地址");
        if (apiKeyWidget && data["密钥"]) apiKeyWidget.value = data["密钥"];
        if (baseUrlWidget && data["接口地址"]) baseUrlWidget.value = data["接口地址"];
        this.setDirtyCanvas(true);
      } catch (e) {
        alert("读取密钥失败：" + (e.message || e));
      }
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);

      // 「获取模型」按钮：不参与序列化，避免保存工作流时写入 null
      const btn = this.addWidget("button", "获取模型", null, () => {
        this.fetchModelList();
      });
      btn.serialize = false;

      // 「选择密钥」下拉：选择后自动回填 API密钥/接口地址
      const keyCombo = this.widgets?.find((w) => w.name === "选择密钥");
      if (keyCombo) {
        keyCombo.callback = (value) => {
          if (value) this.fillKeyFromVault(value);
        };
      }

      // 多次时机处理：兼容不同前端的 widget 值恢复时机（configure 前后）
      ensureValueInOptions(this);
      setTimeout(() => ensureValueInOptions(this), 100);
      setTimeout(() => ensureValueInOptions(this), 500);
      setTimeout(() => this.refreshKeyNames(), 300);
      setTimeout(() => this.refreshKeyNames(), 1000);

      return r;
    };

    nodeType.prototype.fetchModelList = async function () {
      const selectWidget = this.widgets?.find((w) => w.name === "选择模型");
      if (!selectWidget) return;

      const keyCombo = this.widgets?.find((w) => w.name === "选择密钥");
      const apiKeyWidget = this.widgets?.find((w) => w.name === "API密钥");
      const baseUrlWidget = this.widgets?.find((w) => w.name === "接口地址");

      let body;
      const selectedKey = (keyCombo?.value || "").trim();
      if (selectedKey) {
        // 优先使用密钥储存器中保存的密钥（后端解密，不受端口连接影响）
        body = { 密钥名称: selectedKey };
      } else if (apiKeyWidget && baseUrlWidget) {
        const apiKey = (apiKeyWidget.value || "").trim();
        const baseUrl = (baseUrlWidget.value || "").trim();
        if (!apiKey) {
          alert("请先填写 API Key，或在「选择密钥」下拉中选择已保存的密钥");
          return;
        }
        if (!baseUrl) {
          alert("请先填写接口地址（base_url）");
          return;
        }
        body = { api_key: apiKey, base_url: baseUrl };
      } else {
        alert(
          "请在「选择密钥」下拉中选择已保存的密钥；\n" +
            "若 API 密钥/接口地址来自连接端口，可先断开连接手动填写一次"
        );
        return;
      }

      try {
        const resp = await fetch("/ytmmi/llm/models", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!resp.ok) {
          alert("获取模型失败：" + (data.error || resp.status));
          return;
        }
        const models = data.models || [];
        if (!models.length) {
          alert("未获取到模型列表");
          return;
        }

        // 更新「选择模型」下拉选项（原地更新 values 数组触发响应式渲染；
        // 保留当前值，若不在列表中则补入）
        const values = models.includes(selectWidget.value)
          ? models
          : selectWidget.value
            ? [...models, selectWidget.value]
            : models;
        setComboOptions(selectWidget, values);
        this.setDirtyCanvas(true);
        alert(`已获取 ${models.length} 个模型，请在「选择模型」下拉中选择`);
      } catch (e) {
        alert("获取模型失败：" + (e.message || e));
      }
    };
  },
});
