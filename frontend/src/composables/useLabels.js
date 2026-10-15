// USE LABELS
// Single place that turns backend enum values (B0, enums.py) into Spanish text
// and a colour tone. Components never hard-code status labels or colours:
// they ask useLabels, so changing a text or a colour happens only here.
//
// Usage:
//   const { label, tone, toneClasses } = useLabels()
//   label('AlertState', 'ACKNOWLEDGED')   // 'Reconocida'
//   tone('SensorHealth', 'CRITICAL')      // 'danger'
//   toneClasses('danger').pill            // 'bg-danger-light text-danger-dark'

// Tone -> Tailwind classes. Class names must be written out in full here,
// otherwise Tailwind does not generate them.
const TONE_CLASSES = {
  success: {
    pill: "bg-success-light text-success-dark",
    dot: "bg-success",
    border: "border-success",
  },
  warning: {
    pill: "bg-warning-light text-warning-dark",
    dot: "bg-warning",
    border: "border-warning",
  },
  danger: {
    pill: "bg-danger-light text-danger-dark",
    dot: "bg-danger",
    border: "border-danger",
  },
  info: {
    pill: "bg-info-light text-info-dark",
    dot: "bg-info",
    border: "border-info",
  },
  neutral: {
    pill: "bg-slate-100 text-slate-700",
    dot: "bg-slate-400",
    border: "border-slate-300",
  },
};

// Enum name (as in enums.py) -> value -> { text, tone }.
// Entries without tone are text only (they carry no status colour).
const LABELS = {
  OrganizationStatus: {
    TRIAL: { text: "En prueba", tone: "info" },
    ACTIVE: { text: "Activo", tone: "success" },
    SUSPENDED: { text: "Suspendido", tone: "neutral" },
  },
  SiteStatus: {
    OK: { text: "Correcto", tone: "success" },
    WARNING: { text: "Aviso", tone: "warning" },
    CRITICAL: { text: "Crítico", tone: "danger" },
  },
  // Colour of the sensor dot on the floor plan
  SensorHealth: {
    OK: { text: "Normal", tone: "success" },
    WARNING: { text: "Aviso", tone: "warning" },
    CRITICAL: { text: "Crítico", tone: "danger" },
    OFFLINE: { text: "Sin conexión", tone: "neutral" },
  },
  SensorStatus: {
    ONLINE: { text: "Conectado", tone: "success" },
    OFFLINE: { text: "Sin conexión", tone: "neutral" },
  },
  AlertSeverity: {
    WARNING: { text: "Aviso", tone: "warning" },
    CRITICAL: { text: "Crítica", tone: "danger" },
  },
  AlertState: {
    ACTIVE: { text: "Sin reconocer", tone: "danger" },
    ACKNOWLEDGED: { text: "Reconocida", tone: "info" },
    RESOLVED: { text: "Resuelta", tone: "success" },
  },
  InvitationStatus: {
    PENDING: { text: "Pendiente", tone: "info" },
    ACCEPTED: { text: "Aceptada", tone: "success" },
    REVOKED: { text: "Revocada", tone: "neutral" },
    EXPIRED: { text: "Caducada", tone: "warning" },
  },
  BuildingType: {
    HOTEL: { text: "Hotel" },
    COMMUNITY: { text: "Comunidad de vecinos" },
    OFFICE: { text: "Oficinas" },
    SPORTS: { text: "Instalación deportiva" },
    RESIDENCE: { text: "Residencia" },
    INDUSTRIAL: { text: "Industrial" },
    OTHER: { text: "Otro" },
  },
  // Barcelona districts (D10, ck_sites_district). Official names, in Catalan
  District: {
    CIUTAT_VELLA: { text: "Ciutat Vella" },
    EIXAMPLE: { text: "Eixample" },
    SANTS_MONTJUIC: { text: "Sants-Montjuïc" },
    LES_CORTS: { text: "Les Corts" },
    SARRIA_SANT_GERVASI: { text: "Sarrià-Sant Gervasi" },
    GRACIA: { text: "Gràcia" },
    HORTA_GUINARDO: { text: "Horta-Guinardó" },
    NOU_BARRIS: { text: "Nou Barris" },
    SANT_ANDREU: { text: "Sant Andreu" },
    SANT_MARTI: { text: "Sant Martí" },
  },
  SensorType: {
    PRESSURE: { text: "Presión" },
    FLOW: { text: "Caudal" },
  },
  AlertType: {
    LOW_PRESSURE: { text: "Presión baja" },
    HIGH_PRESSURE: { text: "Presión alta" },
    SENSOR_OFFLINE: { text: "Sensor sin conexión" },
  },
};

// Mock fixtures still send old lowercase sensor keys
// (normal | warning | critical | offline). Map them to SensorHealth so the
// mock data keeps working until the stores use the B0 enums.
const LEGACY_SENSOR_KEYS = {
  normal: "OK",
  warning: "WARNING",
  critical: "CRITICAL",
  offline: "OFFLINE",
};

// Unknown values are shown as they come, so a new enum value never breaks a screen
function label(enumName, value) {
  if (value === null || value === undefined || value === "") return "—";
  return LABELS[enumName]?.[value]?.text || String(value);
}

function tone(enumName, value) {
  return LABELS[enumName]?.[value]?.tone || "neutral";
}

function toneClasses(toneName) {
  return TONE_CLASSES[toneName] || TONE_CLASSES.neutral;
}

function toSensorHealth(key) {
  return LEGACY_SENSOR_KEYS[key] || key || "OFFLINE";
}

export function useLabels() {
  return { label, tone, toneClasses, toSensorHealth };
}
