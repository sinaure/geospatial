const LAYER_COLORS = [
  "#4dabf7",
  "#ff6b6b",
  "#51cf66",
  "#fcc419",
  "#cc5de8",
  "#ff922b",
  "#20c997",
  "#f06595",
  "#a9e34b",
  "#3bc9db",
  "#845ef7",
  "#fd7e14",
];

export const LAYER_DEFINITIONS = [
  {
    id: "enga-province",
    name: "Enga Province",
    file: "enga.geojson",
    group: "Regions",
    visible: true,
  },
  {
    id: "enga-mines",
    name: "Enga Mines",
    file: "enga_mines.geojson",
    group: "Mining Sites",
    visible: true,
  },
  {
    id: "grasberg",
    name: "Grasberg (Indonesia)",
    file: "grasberg.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "bingham",
    name: "Bingham Canyon (USA)",
    file: "bingham.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "carajas",
    name: "Carajás (Brazil)",
    file: "carajas.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "chuquicamata",
    name: "Chuquicamata (Chile)",
    file: "chuquicamata.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "escondida",
    name: "Escondida (Chile)",
    file: "escondida.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "garzweiler",
    name: "Garzweiler (Germany)",
    file: "garzweiler.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "kiruna",
    name: "Kiruna (Sweden)",
    file: "kiruna.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "muruntau",
    name: "Muruntau (Uzbekistan)",
    file: "muruntau.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "north-antelope",
    name: "North Antelope Rochelle (USA)",
    file: "north_antelope.geojson",
    group: "Mining Sites",
    visible: false,
  },
  {
    id: "orapa",
    name: "Orapa (Botswana)",
    file: "orapa.geojson",
    group: "Mining Sites",
    visible: false,
  },
];

export function getLayerColor(index) {
  return LAYER_COLORS[index % LAYER_COLORS.length];
}

export function buildInitialLayers() {
  return LAYER_DEFINITIONS.map((def, i) => ({
    ...def,
    color: getLayerColor(i),
    loaded: false,
    geojson: null,
    geometryType: null,
  }));
}
