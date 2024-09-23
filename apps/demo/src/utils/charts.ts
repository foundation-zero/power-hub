import type { DecalObject } from "echarts/types/src/util/types.js";

export const useStripes = (rotation = 4, size = 1.5): DecalObject => ({
  color: "rgba(255, 255, 255, 1)",
  dashArrayX: [1, 0],
  dashArrayY: [1, 2],
  symbolSize: size,
  rotation: Math.PI / rotation,
});
