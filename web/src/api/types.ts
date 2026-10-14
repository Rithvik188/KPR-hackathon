// Contract v1.2 shapes (contract/api.md §1–§2), hand-written until types.gen.ts lands at Sync 1.

export type DocType = 'aadhaar_front' | 'aadhaar_back' | 'pan' | 'voter_id' | 'unknown'
export type DeclarableType = Exclude<DocType, 'unknown'>
export type DocStatus = 'accepted' | 'fixable' | 'invalid'
export type AppStatus = 'submitted' | 'needs_fix' | 'ready_for_officer' | 'approved' | 'rejected'
export type IssueSeverity = 'blocking' | 'warning' | 'info'
export type Audience = 'citizen' | 'officer'
export type NameTier = 'match' | 'likely_match' | 'mismatch' | 'not_enough_data'
export type AlertRule = 'REJECT_SPIKE' | 'SLA_BREACH' | 'BACKLOG_GROWTH' | 'DUPLICATE_CLUSTER' | 'USER_REPORTED'
export type AlertSeverity = 'high' | 'medium' | 'low'
export type AlertStatus = 'open' | 'acknowledged'
export type OfficeType = 'taluk_office' | 'esevai_centre'
export type Service = 'community_certificate' | 'income_certificate' | 'nativity_certificate' | 'ration_card_update'
export type IssueCategory = 'scanner_problem' | 'long_wait' | 'wrong_rejection' | 'other'
export type ReporterRole = 'citizen' | 'operator' | 'officer'
export type OfficerAction = 'approve' | 'reject' | 'request_fix'

export interface Issue {
  code: string
  severity: IssueSeverity
  audience: Audience
  msg_en: string
  msg_ta: string
  evidence: Record<string, unknown>
}

export interface Quality {
  card_found: boolean
  blur_score: number | null
  glare_fraction: number | null
  brightness: number | null
  skew_deg: number | null
  card_width_px: number | null
  passed: boolean
}

/** id_number_display, name, dob, gender, father_name (aadhaar_back: id_number_display, pin_code) */
export type DocFields = Record<string, unknown>

export interface ValidationResult {
  document_id: string | null
  doc_type: DocType
  declared_type: string | null
  status: DocStatus
  issues: Issue[]
  quality: Quality
  fields: DocFields | null
  ocr: { mean_confidence: number; id_number_confidence: number | null } | null
  timings_ms: { quality: number; ocr: number; total: number }
}

export interface ConsistencyResult {
  name_tier: NameTier
  name_score: number | null
  names_compared: string[]
  dob_match: boolean | null
  issues: Issue[]
}

export interface Office {
  id: string
  name: string
  type: OfficeType
  taluk: string
  lat: number
  lng: number
}

export interface ApplicationSummary {
  id: string
  citizen_name: string
  phone_masked: string
  service: Service
  office_id: string
  office_name: string
  status: AppStatus
  created_at: string
  updated_at: string
  sla_due_at: string
  sla_hours_left: number
  flag_codes: string[]
  doc_count: number
  resubmissions: number
}

export interface ApplicationDocument {
  id: string
  doc_type: DocType
  /** contract v1.3: the slot the operator uploaded into (doc_type is "unknown" on a quality early-return) */
  declared_type: string | null
  status: DocStatus
  issues: Issue[]
  fields: DocFields | null
  uploaded_at: string
  image_available: boolean
}

export interface HistoryEvent {
  at: string
  event: string
  actor: string
  note: string | null
}

export interface Decision {
  action: OfficerAction
  reason_code: string | null
  note: string | null
  at: string
}

export interface ApplicationDetail extends ApplicationSummary {
  documents: ApplicationDocument[]
  consistency: ConsistencyResult
  history: HistoryEvent[]
  decision: Decision | null
}

export interface ApplicationList {
  items: ApplicationSummary[]
  total: number
}

export interface UploadResult {
  document_id: string
  validation: ValidationResult
  application: ApplicationSummary
  consistency: ConsistencyResult
}

export interface Alert {
  id: string
  rule: AlertRule
  severity: AlertSeverity
  office_id: string | null
  office_name: string | null
  title_en: string
  detail_en: string
  evidence: Record<string, unknown>
  suggested_action_en: string
  status: AlertStatus
  created_at: string
}

export interface DetectionMetrics {
  generated_at: string
  source: string
  dataset: { tune_n: number; test_n: number; sets_n: number; note_en: string }
  per_code: { code: string; precision: number; recall: number; f1: number; support: number }[]
  doc_type_accuracy: number
  field_accuracy: Record<string, number>
  false_invalid_rate: number
  latency_ms: { quality_p50: number; quality_p95: number; full_p50: number; full_p95: number }
  consistency: { labels: string[]; confusion: number[][] }
}

export interface OperationsMetrics {
  days: number
  source: string
  totals: {
    applications: number
    documents: number
    first_time_right_rate: number
    avg_resubmissions: number
    backlog_now: number
    sla_breaches_now: number
  }
  daily: { date: string; submitted: number; approved: number; rejected: number; backlog: number }[]
  by_office: {
    office_id: string
    office_name: string
    taluk: string
    lat: number
    lng: number
    submissions: number
    reject_rate: number
    backlog: number
    top_issue: string | null
  }[]
  by_issue: { code: string; count: number }[]
  projection: {
    baseline_reject_rate: number
    projected_reject_rate: number
    prevented_rejections: number
    assumptions_en: string
  }
}

export interface IssueReport {
  id: string
  office_id: string
  category: IssueCategory
  description: string
  reporter_role: ReporterRole
  created_at: string
}

export type IssueReportInput = Omit<IssueReport, 'id' | 'created_at'>

export interface Notification {
  id: string
  application_id: string
  channel: string
  to_masked: string
  body_en: string
  body_ta: string
  created_at: string
}

export interface Health {
  status: string
  ocr_engine: string
  ocr_gpu: boolean
  ocr_ready: boolean
  version: string
}

export interface CreateApplicationInput {
  citizen_name: string
  phone: string
  service: Service
  office_id: string
}

export interface OfficerActionInput {
  action: OfficerAction
  reason_code?: string | null
  note?: string | null
}
