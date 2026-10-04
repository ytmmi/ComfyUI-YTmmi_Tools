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
 *
 * 动态图片输入端口（与 Python 端 MAX_IMAGES = 9 一致）：
 * - 新版 ComfyUI 前端（Vue GraphView）中，输入端口总会渲染圆点，无法通过
 *   清空 input.name 隐藏端口，因此改用「删除/添加末尾端口」策略；
 * - 节点创建后默认只保留「图片0」（1 个图片输入口）；
 * - 当末尾图片输入口被连接（如 图片0）时，自动添加下一个图片口（图片1），
 *   依次类推，最多 图片8（共 9 个）；
 * - 断开末尾图片输入口时自动回收该输入口；
 * - 加载含链接的工作流时，会根据已有链接恢复对应图片输入口。
 *
 * 「生成后控制」说明：
 * - 「种子」在 Python 端声明了官方的 control_after_generate 标记，前端会
 *   自动在其旁生成「生成后控制」下拉（固定值/递增值/递减值/随机值）；
 * - 该下拉与种子的联动完全由 ComfyUI 官方前端实现（applyWidgetControl），
 *   生成后由前端本地改写种子控件值，因此本扩展**无需**做任何回填处理。
 */
app.registerExtension({
  name: "YTmmi.CustomLLM",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "CustomLLMNode") return;

    const MAX_IMAGES = 9; // 与 Python 端 MAX_IMAGES 保持一致
    const IMAGE_PREFIX = "图片"; // 图片输入口名称前缀（图片0 ~ 图片8）
    const INPUT_SLOT = 1; // LiteGraph.INPUT

    // 所有图片输入口的当前下标（节点 inputs 中可能还含 STRING 转端口，按名称前缀定位）
    const imagePortIndices = function (node) {
      const idxs = [];
      for (let i = 0; i < node.inputs.length; i++) {
        if (node.inputs[i].name?.startsWith(IMAGE_PREFIX)) idxs.push(i);
      }
      return idxs;
    };

    // 计算当前应显示的图片口数量：
    // 默认 1 个（图片0）；最后一个有链接的图片口后面再保留 1 个空图片口供继续连接
    const computeVisibleImageCount = function (node) {
      let maxLinkedSeq = -1;
      let seq = 0;
      for (let i = 0; i < node.inputs.length; i++) {
        if (node.inputs[i].name?.startsWith(IMAGE_PREFIX)) {
          if (node.inputs[i].link != null) maxLinkedSeq = seq;
          seq++;
        }
      }
      return Math.min(Math.max(1, maxLinkedSeq + 2), MAX_IMAGES);
    };

    // 只增删末尾的图片端口，保证图片口序号与后端参数名（图片0 ~ 图片8）对齐
    const syncInputs = function (node) {
      if (!node.inputs) return;
      const target = computeVisibleImageCount(node);
      const idxs = imagePortIndices(node);
      let imgCount = idxs.length;

      // 删除末尾多余的图片端口（绝不删除有链接的端口，且至少保留 1 个）
      while (imgCount > target) {
        const lastImgIdx = imagePortIndices(node).at(-1);
        if (lastImgIdx == null) break;
        const last = node.inputs[lastImgIdx];
        if (last.link != null) break;
        node.removeInput(lastImgIdx);
        imgCount--;
      }
      // 追加缺失的图片端口（只加到末尾，名称序号 = 当前图片口数量）
      while (imgCount < target) {
        node.addInput(`${IMAGE_PREFIX}${imgCount}`, "IMAGE");
        imgCount++;
      }
      node.setDirtyCanvas?.(true, true);
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

      // 动态图片端口：节点创建/加载后多次刷新，兼容不同前端的输入填充时机
      const sync = () => syncInputs(this);
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      setTimeout(sync, 500);

      return r;
    };

    const originalOnConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (type, slot, change, linkInfo) {
      const r = originalOnConnectionsChange?.apply(this, arguments);
      if (type === INPUT_SLOT) {
        syncInputs(this);
      }
      return r;
    };

    nodeType.prototype.fetchModelList = async function () {
      const selectWidget = this.widgets?.find((w) => w.name === "选择模型");
      if (!selectWidget) return;

      const keyCombo = this.widgets?.find((w) => w.name === "选择密钥");
      const apiKeyWidget = this.widgets?.find((w) => w.name === "API密钥");
      const baseUrlWidget = this.widgets?.find((w) => w.name === "接口地址");

      let body;
      const apiKey = (apiKeyWidget?.value || "").trim();
      const baseUrl = (baseUrlWidget?.value || "").trim();
      const selectedKey = (keyCombo?.value || "").trim();

      if (apiKey && baseUrl) {
        // 手动填写优先（与节点执行时的凭据规则一致：两个都填 → 用手动组合）
        body = { api_key: apiKey, base_url: baseUrl };
      } else if (apiKey || baseUrl) {
        // 只填了一项：与执行规则一致，提示成对填写（避免静默使用密钥库旧值）
        alert("API密钥 与 接口地址 必须成对填写（两个都填，或两个都留空以使用「选择密钥」）");
        return;
      } else if (selectedKey) {
        // 两个输入都为空 → 使用密钥储存器中保存的密钥（后端解密，不受端口连接影响）
        body = { 密钥名称: selectedKey };
      } else {
        alert(
          "请先填写 API密钥 与 接口地址，或在「选择密钥」下拉中选择已保存的密钥；\n" +
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
