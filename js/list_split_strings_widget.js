import { app } from "../../scripts/app.js";

/**
 * 「列表分离字符串」输出端口按需显示扩展。
 *
 * 新版 ComfyUI 前端（Vue GraphView）中端口圆点总会渲染，无法通过清空 name 隐藏，
 * 因此沿用「视频拼接」已验证的「删除/添加末尾端口」策略：
 * - 节点创建后只保留前 2 个输出端口（字符串0、字符串1）；
 * - 执行完成后按实际列表项数显示「项数 + 1」个端口（多出的 1 个作为备用），
 *   最少 2 个、最多 20 个（与 Python 端 MAX_OUTPUTS 一致）；
 * - 已连接的端口绝不删除，删除只发生在端口数组末尾的无链接端口上。
 *
 * 端口名/顺序与 Python 端 RETURN_NAMES 的 字符串0 ~ 字符串19 一一对应，
 * 增删只发生在末尾，保证端口序号与后端返回值始终对齐。
 */

const MAX_OUTPUTS = 20; // 与 Python 端保持一致
const MIN_OUTPUTS = 2;

app.registerExtension({
  name: "YTmmi.ListSplitStringsOutputs",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "ListSplitStringsNode") return;

    const isLinked = function (output) {
      if (!output) return false;
      if (Array.isArray(output.links)) return output.links.length > 0;
      return output.link != null;
    };

    // 目标端口数：至少 MIN_OUTPUTS；执行过则按「项数 + 1」；并保证已连接的端口保留
    const computeVisibleCount = function (node) {
      let lastLinked = -1;
      for (let i = 0; i < node.outputs.length; i++) {
        if (isLinked(node.outputs[i])) lastLinked = i;
      }
      const known = Number(node.__ytmmiListCount);
      const desired = Number.isFinite(known)
        ? Math.max(MIN_OUTPUTS, known + 1)
        : MIN_OUTPUTS;
      return Math.min(Math.max(desired, lastLinked + 1), MAX_OUTPUTS);
    };

    // 只增删末尾端口，保证序号对齐
    const syncOutputs = function (node) {
      if (!node.outputs) return;
      const target = computeVisibleCount(node);

      while (node.outputs.length > target) {
        const last = node.outputs[node.outputs.length - 1];
        if (isLinked(last)) break; // 绝不删除已连接的端口
        node.removeOutput(node.outputs.length - 1);
      }
      while (node.outputs.length < target) {
        node.addOutput(`字符串${node.outputs.length}`, "STRING");
      }
      node.setDirtyCanvas?.(true, true);
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
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
      const sync = () => syncOutputs(this);
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      return r;
    };

    const originalOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function () {
      const r = originalOnExecuted?.apply(this, arguments);
      const execData = arguments[0];
      // Python 端通过 ui 回传实际项数：{"数量": [n]}
      const count = execData?.数量?.[0];
      if (count !== undefined && count !== null) {
        this.__ytmmiListCount = Number(count) || 0;
      }
      syncOutputs(this);
      return r;
    };
  },
});
