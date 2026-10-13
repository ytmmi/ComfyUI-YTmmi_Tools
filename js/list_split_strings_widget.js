import { app } from "../../scripts/app.js";

/**
 * 「列表分离字符串」输出端口按需显示扩展。
 *
 * 端口数量在**工作流构建阶段（运行前）**就由连线决定，与本次运行结果无关：
 * - 节点创建后只保留前 MIN_OUTPUTS 个输出端口（字符串0、字符串1）；
 * - 当**末尾端口被连接**时自动追加下一个端口（字符串2、字符串3……），
 *   即「连一个、出一个」，最多 MAX_OUTPUTS（20，与 Python 端一致）；
 * - 断开末尾端口时自动回收该端口；
 * - 加载含链接的工作流时按已有链接恢复端口数量。
 *
 * 新版 ComfyUI 前端（Vue GraphView）中端口圆点总会渲染，无法通过清空 name 隐藏，
 * 因此沿用「视频拼接」「字符串到列表」已验证的「删除/添加末尾端口」策略；
 * 增删只发生在端口数组末尾，保证端口序号与后端 RETURN_NAMES / 返回值始终对齐。
 *
 * 节点高度取最小值：
 * - LiteGraph 的 addOutput() 只会把节点撑高（expandToFitContent），removeOutput()
 *   并不会缩回，因此端口增减后必须显式把高度收敛到「当前端口数所需的最小高度」；
 * - 收敛用**直接赋值 node.size**（与官方 autogrow 同款）而非 setSize()，
 *   这样不会触发 onResize，从而能与「用户手动拖拽高度」区分开；
 * - 用户手动拖大过高度时尊重该高度（会话内拖拽由 onResize 识别，
 *   保存后载入则比较保存高度与当前端口数所需的最小高度）。
 */

const MAX_OUTPUTS = 20; // 与 Python 端 MAX_OUTPUTS 保持一致
const MIN_OUTPUTS = 2;
const OUTPUT_SLOT = 2; // LiteGraph.OUTPUT

app.registerExtension({
  name: "YTmmi.ListSplitStringsOutputs",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "ListSplitStringsNode") return;

    // 该输出端口是否已连线。
    // 优先用非废弃 API（isOutputConnected），避免读取 output.links 触发弃用告警；
    // 图尚未就绪时（创建阶段 graph 为 null）退回序列化字段判断。
    const isLinked = function (node, index) {
      const output = node.outputs?.[index];
      if (!output) return false;
      if (node.graph && typeof node.isOutputConnected === "function") {
        return node.isOutputConnected(index);
      }
      if (Array.isArray(output.links)) return output.links.length > 0;
      return output.link != null;
    };

    // 目标端口数：至少 MIN_OUTPUTS；末尾端口已连接时再多留 1 个空端口供继续连接
    const computeVisibleCount = function (node) {
      let lastLinked = -1;
      const count = node.outputs?.length ?? 0;
      for (let i = 0; i < count; i++) {
        if (isLinked(node, i)) lastLinked = i;
      }
      return Math.min(Math.max(MIN_OUTPUTS, lastLinked + 2), MAX_OUTPUTS);
    };

    // 当前端口数所需的最小高度（LiteGraph computeSize 不传参即得最小尺寸）
    const minimalHeight = function (node) {
      const computed = node.computeSize?.();
      return computed ? Math.max(1, computed[1]) : null;
    };

    // 把节点高度收敛到最小值（用户手动调整过则跳过）
    const applyMinimalHeight = function (node) {
      if (node.__ytmmiUserResized) return;
      const targetHeight = minimalHeight(node);
      if (targetHeight === null) return;
      if (Math.abs((node.size?.[1] ?? 0) - targetHeight) < 0.5) return;
      // 直接赋值而非 setSize()：不触发 onResize，避免被误判为用户手动调整
      node.size = [node.size?.[0] ?? node.computeSize?.()[0] ?? 0, targetHeight];
    };

    // 只增删末尾端口，保证序号对齐。
    // convergeHeight=false 用于「载入工作流」时先摆好端口、再由调用方判定高度。
    const syncOutputs = function (node, convergeHeight = true) {
      if (!node.outputs) return;
      const target = computeVisibleCount(node);

      // addOutput() 内部会 expandToFitContent() → setSize() → onResize()，
      // 用标记表明这是端口同步引起的尺寸变化，不算用户手动调整。
      node.__ytmmiAutoSizing = true;
      try {
        while (node.outputs.length > target) {
          // 绝不删除已连接的端口
          if (isLinked(node, node.outputs.length - 1)) break;
          node.removeOutput(node.outputs.length - 1);
        }
        while (node.outputs.length < target) {
          node.addOutput(`字符串${node.outputs.length}`, "STRING");
        }
      } finally {
        node.__ytmmiAutoSizing = false;
      }

      if (convergeHeight) applyMinimalHeight(node);
      node.setDirtyCanvas?.(true, true);
    };

    // 用户手动拖拽高度后不再自动收敛
    const originalOnResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const r = originalOnResize?.apply(this, arguments);
      if (!this.__ytmmiAutoSizing) this.__ytmmiUserResized = true;
      return r;
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      // 构造期的初始尺寸（按 20 个端口算出）不算用户调整，重置标记
      this.__ytmmiUserResized = false;
      const r = originalOnNodeCreated?.apply(this, arguments);
      const sync = () => syncOutputs(this);
      // 多个时机刷新，兼容不同前端版本的端口填充时机
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      setTimeout(sync, 500);
      return r;
    };

    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = originalOnConfigure?.apply(this, arguments);
      // 先按已有链接摆好端口（暂不收敛高度），再比较「保存高度」与
      // 「当前端口数所需的最小高度」：明显更高说明用户当时手动拖大过，尊重该高度。
      const savedHeight = this.size?.[1] ?? 0;
      this.__ytmmiUserResized = false;
      syncOutputs(this, false);
      const targetHeight = minimalHeight(this);
      if (targetHeight !== null && savedHeight > targetHeight + 1) {
        this.__ytmmiUserResized = true;
      }
      applyMinimalHeight(this);
      // 兼容不同前端版本的端口填充时机，稍后再同步一次
      const sync = () => syncOutputs(this);
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      return r;
    };

    // 整图载入完成后所有连线都已就位，再做一次收敛（保证端口数量与链接一致）
    const originalOnAfterGraphConfigured = nodeType.prototype.onAfterGraphConfigured;
    nodeType.prototype.onAfterGraphConfigured = function () {
      const r = originalOnAfterGraphConfigured?.apply(this, arguments);
      syncOutputs(this);
      return r;
    };

    const originalOnConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (type, slot, change, linkInfo) {
      const r = originalOnConnectionsChange?.apply(this, arguments);
      // 输出端口连线变化即在工作流构建阶段同步端口数量（不依赖运行结果）
      if (type === OUTPUT_SLOT) {
        syncOutputs(this);
      }
      return r;
    };
  },
});
