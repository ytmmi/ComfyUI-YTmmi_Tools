import { app } from "../../scripts/app.js";

/**
 * 批量加载图像节点前端扩展。
 *
 * 「位置」自动递增：
 * - 后端每执行一次就把「位置」按批次递增，并通过 ui 字典回填；
 * - 前端在 onExecuted 里把回填值写回「位置」控件（控件名必须与后端 INPUT_TYPES
 *   的键完全一致），写完调用 setDirtyCanvas 触发重绘。
 *
 * 「生成后控制」（官方 control_after_generate 机制）：
 * - 「种子」在 Python 端声明了官方的 control_after_generate 标记，前端会自动
 *   在「种子」右侧生成「生成后控制」下拉（固定值/递增值/递减值/随机值）；
 * - 该下拉与种子的联动完全由 ComfyUI 官方前端实现（applyWidgetControl），
 *   生成后由前端本地改写种子控件值，因此本扩展**无需**对种子做任何回填。
 *
 * 旧工作流迁移（onConfigure）：
 * - 旧版本把「生成后控制」做成后端 COMBO 控件，控件顺序为
 *   路径 / 顺序 / 位置 / 种子 / 批次 / 生成后控制；
 * - 新版本该下拉改由官方前端生成，控件顺序变为
 *   路径 / 顺序 / 位置 / 种子 / control_after_generate / 批次；
 * - 两者长度都是 6，官方按位置回填时会把「批次」塞进 control_after_generate、
 *   把旧的「生成后控制」塞进「批次」，导致后端报 Value not in list；
 * - 因此在 onConfigure（官方回填控件值之后才调用）里识别旧布局并就地纠正：
 *   「批次」还原为数字，「生成后控制」还原为官方的 fixed/increment/decrement/randomize。
 */
app.registerExtension({
  name: "YTmmi.AutoFillValue",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "BatchLoadImagesNode") return;

    // 旧版后端「生成后控制」COMBO 的取值 → 官方 control_after_generate 的取值
    const LEGACY_CONTROL_MODES = {
      固定: "fixed",
      增量: "increment",
      递减: "decrement",
      随机化: "randomize",
    };
    const LEGACY_BATCH_INDEX = 4; // 旧布局：[路径, 顺序, 位置, 种子, 批次, 生成后控制]
    const LEGACY_CONTROL_INDEX = 5;
    const CONTROL_WIDGET_NAME = "control_after_generate"; // 官方下拉的控件名
    const BATCH_WIDGET_NAME = "批次";
    const POSITION_WIDGET_NAME = "位置";

    // ── 旧工作流控件迁移 ────────────────────────────────────
    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const info = arguments[0];
      const result = originalOnConfigure?.apply(this, arguments);

      const values = info?.widgets_values;
      if (!Array.isArray(values) || values.length !== 6) return result;

      const legacyControl = values[LEGACY_CONTROL_INDEX];
      const legacyBatch = values[LEGACY_BATCH_INDEX];
      // 旧布局特征：第 5 项是旧的中文控制模式，第 4 项是数字批次
      const isLegacy =
        typeof legacyControl === "string" &&
        Object.prototype.hasOwnProperty.call(LEGACY_CONTROL_MODES, legacyControl) &&
        typeof legacyBatch === "number";
      if (!isLegacy) return result;

      const controlWidget = this.widgets?.find(
        (w) => w.name === CONTROL_WIDGET_NAME,
      );
      const batchWidget = this.widgets?.find((w) => w.name === BATCH_WIDGET_NAME);
      if (!controlWidget && !batchWidget) return result;

      const controlValue = LEGACY_CONTROL_MODES[legacyControl];
      if (controlWidget) controlWidget.value = controlValue;
      if (batchWidget) batchWidget.value = legacyBatch;
      // 同步工作流数据，保证内存里的 widgets_values 与控件值一致
      values[LEGACY_BATCH_INDEX] = controlValue;
      values[LEGACY_CONTROL_INDEX] = legacyBatch;
      this.setDirtyCanvas?.(true);

      return result;
    };

    // ── 「位置」回填 ────────────────────────────────────────
    const originalOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function () {
      originalOnExecuted?.apply(this, arguments);
      const execData = arguments[0];
      if (!execData) return;

      const posValue = execData.pos?.[0];
      const posWidget = this.widgets?.find(
        (w) => w.name === POSITION_WIDGET_NAME,
      );
      if (!posWidget || posValue === undefined) return;

      posWidget.value = posValue;
      this.setDirtyCanvas(true);
    };
  },
});
