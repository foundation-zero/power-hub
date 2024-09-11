export type WaterFlowType = "freshWater" | "greyWater" | "blackWater" | "technicalWater";

export const WATER_TANK_THRESHOLDS: Record<WaterFlowType, [number?, number?] | undefined> = {
  freshWater: [100, 900],
  greyWater: [100, 900],
  blackWater: [100, 1800],
  technicalWater: [100, 900],
};

export const WATER_TANK_CAPACITY: Record<WaterFlowType, number> = {
  freshWater: 1000,
  greyWater: 1000,
  blackWater: 2000,
  technicalWater: 1000,
};

export const WATER_MAKER_STATUS: Record<0 | 1 | 2 | 3, string> = {
  0: "Idle",
  1: "Standby",
  2: "Water production",
  3: "Flushing",
};
