const toStringWithUnit = (unit: string) => (val: number) => `${val} ${unit}`;

export const toKiloWattHours = toStringWithUnit("kWh");
export const toKiloWatts = toStringWithUnit("kW");
export const toDegreesCelcius = toStringWithUnit("°C");
export const toPercentage = toStringWithUnit("%");
