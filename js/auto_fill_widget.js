import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "YTmmi.AutoFillValue",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "BatchLoadImagesNode") return;

    const originalOnExecuted = nodeType.prototype.onExecuted;

    nodeType.prototype.onExecuted = function () {
      originalOnExecuted?.apply(this, arguments);

      // 从 Python 端返回的 ui 字典中读取值
      // 格式: { seed: [value], pos: [value] }
      const execData = arguments[0];
      if (!execData) return;

      let seedValue = execData.seed?.[0];
      let posValue = execData.pos?.[0];

      const seedWidget = this.widgets?.find((w) => w.name === "种子");
      const posWidget = this.widgets?.find((w) => w.name === "位置");

      let changed = false;
      if (seedWidget && seedValue !== undefined) {
        seedWidget.value = seedValue;
        changed = true;
      }
      if (posWidget && posValue !== undefined) {
        posWidget.value = posValue;
        changed = true;
      }
      if (changed) {
        this.setDirtyCanvas(true);
      }
    };
  },
});
