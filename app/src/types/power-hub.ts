export interface Valve {
  position: number;
}

export interface Reservoir {
  temperature: number;
}

export interface Port {
  flow: number;
  temperature: number;
}

export interface Yazaki {
  efficiency: number;
}

export interface PCM {
  stateOfCharge: number;
  temperature: number;
}

export interface AppliancesTree {
  chillerSwitchValve: Valve;
  chillerWasteBypassValve: Valve;
  coldReservoir: Reservoir;
  heatPipesValve: Valve;
  hotReservoir: Reservoir;
  hotReservoirPcmValve: Valve;
  pcm: PCM;
  preheatBypassValve: Valve;
  preheatReservoir: Reservoir;
  wasteSwitchValve: Valve;
  yazaki: Yazaki;
  yazakiWasteBypassValve: Valve;
}

export interface ConnectionsTree {
  chillMix: {
    a: Port;
    b: Port;
  };
  chiller: {
    chilledIn: Port;
    chilledOut: Port;
    coolingIn: Port;
    coolingOut: Port;
  };
  chillerSwitchValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  chillerWasteBypassValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  chillerWasteMix: {
    a: Port;
    ab: Port;
    b: Port;
  };
  coldReservoir: {
    heatExchangeOut: Port;
  };
  freshWaterSource: {
    output: Port;
  };
  heatPipes: {
    out: Port;
  };
  heatPipesMix: {
    a: Port;
    b: Port;
  };
  heatPipesValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  hotMix: {
    a: Port;
    ab: Port;
    b: Port;
  };
  hotReservoir: {
    fillIn: Port;
    heatExchangeIn: Port;
    heatExchangeOut: Port;
  };
  hotReservoirPcmValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  outboard_exchange: {
    aIn: Port;
    bIn: Port;
  };
  outboardSource: {
    output: Port;
  };
  pcm: {
    chargeIn: Port;
    chargeOut: Port;
    dischargeOut: Port;
  };
  preheatBypassValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  preheatMix: {
    a: Port;
    ab: Port;
    b: Port;
  };
  preheatReservoir: {
    fillIn: Port;
    fillOut: Port;
    heatExchangeIn: Port;
    heatExchangeOut: Port;
  };
  wasteMix: {
    a: Port;
    ab: Port;
    b: Port;
  };
  wasteSwitchValve: {
    a: Port;
    b: Port;
  };
  yazaki: {
    chilledIn: Port;
    chilledOut: Port;
    coolingIn: Port;
    coolingOut: Port;
    hotIn: Port;
  };
  yazakiWasteBypassValve: {
    a: Port;
    ab: Port;
    b: Port;
  };
  yazakiWasteMix: {
    a: Port;
    ab: Port;
    b: Port;
  };
}

export interface ComputedTree {
  heatPipes: {
    power: number;
  };
}

export interface Tree {
  connections: ConnectionsTree;
  appliances: AppliancesTree;
  computed: ComputedTree;
}
