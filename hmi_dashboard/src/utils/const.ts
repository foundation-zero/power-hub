export type WaterFlowType = "freshWater" | "greyWater" | "blackWater" | "technicalWater";

export const waterTankThresholds: Record<WaterFlowType, [number?, number?] | undefined> = {
  freshWater: [100, 900],
  greyWater: [100, 900],
  blackWater: [100, 1800],
  technicalWater: [100, 900],
};

export const waterTankCapacity: Record<WaterFlowType, number> = {
  freshWater: 1000,
  greyWater: 1000,
  blackWater: 2000,
  technicalWater: 1000,
};
