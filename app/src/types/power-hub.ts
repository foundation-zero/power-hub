export interface Valve {
  position: number;
}

export interface Reservoir {
  temperature: number;
}

export interface PortSensor {
  flow: number;
  temperature: number;
}

export interface Yazaki {
  efficiency: number;
}

export interface PCM {
  state_of_charge: number;
  temperature: number;
}

export interface AppliancesTree {
  chiller_switch_valve: Valve;
  chiller_waste_bypass_valve: Valve;
  cold_reservoir: Reservoir;
  heat_pipes_valve: Valve;
  hot_reservoir: Reservoir;
  hot_reservoir_pcm_valve: Valve;
  pcm: PCM;
  preheat_bypass_valve: Valve;
  preheat_reservoir: Reservoir;
  waste_switch_valve: Valve;
  yazaki: Yazaki;
  yazaki_waste_bypass_valve: Valve;
}

export interface ConnectionsTree {
  chill_mix: {
    A: PortSensor;
    B: PortSensor;
  };
  chiller: {
    CHILLED_IN: PortSensor;
    CHILLED_OUT: PortSensor;
    COOLING_IN: PortSensor;
    COOLING_OUT: PortSensor;
  };
  chiller_switch_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  chiller_waste_bypass_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  chiller_waste_mix: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  cold_reservoir: {
    HEAT_EXCHANGE_OUT: PortSensor;
  };
  fresh_water_source: {
    OUTPUT: PortSensor;
  };
  heat_pipes: {
    OUT: PortSensor;
  };
  heat_pipes_mix: {
    A: PortSensor;
    B: PortSensor;
  };
  heat_pipes_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  hot_mix: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  hot_reservoir: {
    FILL_IN: PortSensor;
    HEAT_EXCHANGE_IN: PortSensor;
    HEAT_EXCHANGE_OUT: PortSensor;
  };
  hot_reservoir_pcm_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  outboard_exchange: {
    A_IN: PortSensor;
    B_IN: PortSensor;
  };
  outboard_source: {
    OUTPUT: PortSensor;
  };
  pcm: {
    CHARGE_IN: PortSensor;
    CHARGE_OUT: PortSensor;
    DISCHARGE_OUT: PortSensor;
  };
  preheat_bypass_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  preheat_mix: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  preheat_reservoir: {
    FILL_IN: PortSensor;
    FILL_OUT: PortSensor;
    HEAT_EXCHANGE_IN: PortSensor;
    HEAT_EXCHANGE_OUT: PortSensor;
  };
  waste_mix: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  waste_switch_valve: {
    A: PortSensor;
    B: PortSensor;
  };
  yazaki: {
    CHILLED_IN: PortSensor;
    CHILLED_OUT: PortSensor;
    COOLING_IN: PortSensor;
    COOLING_OUT: PortSensor;
    HOT_IN: PortSensor;
  };
  yazaki_waste_bypass_valve: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
  yazaki_waste_mix: {
    A: PortSensor;
    AB: PortSensor;
    B: PortSensor;
  };
}

export interface Tree {
  connections: ConnectionsTree;
  appliances: AppliancesTree;
}

export interface Port {
  in: PortSensor;
  out: PortSensor;
}

export interface Chiller {
  chilled: Port;
  cooling: Port;
}

export interface PowerHub {
  chiller: Chiller;
}
