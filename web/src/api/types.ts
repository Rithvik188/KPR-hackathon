// Contract v1.2 shapes (contract/api.md §1–§2), hand-written until types.gen.ts lands at Sync 1.

export type SupportingType = 'parent_community_certificate' | 'birth_certificate' | 'income_proof' | 'address_proof'
export type DocType = 'aadhaar_front' | 'aadhaar_back' | 'pan' | 'voter_id' | SupportingType | 'unknown'
export type DeclarableType = Exclude<DocType, 'unknown'>
export type DocStatus = 'accepted' | 'fixable' | 'invalid'
export type AppStatus = 'submitted' | 'needs_fix' | 'ready_for_officer' | 'approved' | 'rejected'
export type IssueSeverity = 'blocking' | 'warning' | 'info'
export type Audience = 'citizen' | 'officer'
export type NameTier = 'match' | 'likely_match' | 'mismatch' | 'not_enough_data'
export type AlertRule = 'REJECT_SPIKE' | 'SLA_BREACH' | 'BACKLOG_GROWTH' | 'DUPLICATE_CLUSTER' | 'USER_REPORTED'
export type AlertSeverity = 'high' | 'medium' | 'low'
export type AlertStatus = 'open' | 'acknowledged'
export type OfficeType = 'taluk_office' | 'esevai_centre' | 'esevai_centre_private'
export type Service =
  | 'identity_verification' // made-up demo scheme: ID proofs only, no supporting document (contract v1.6)
  | 'community_certificate'
  | 'income_certificate'
  | 'nativity_certificate'
  | 'ration_card_update'
export type IssueCategory = 'scanner_problem' | 'long_wait' | 'wrong_rejection' | 'other'
export type ReporterRole = 'citizen' | 'operator' | 'officer'
export type OfficerAction = 'approve' | 'reject' | 'request_fix' | 'forward'
export type Stage = 'vao' | 'ri' | 'tahsildar'

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
  /** v1.4: operator-typed name/DOB compared with the documents (null when no form was passed) */
  form_check?: Record<string, unknown> | null
}

/** Shape of ConsistencyResult.form_check (contract v1.4); use formCheckOf() to read it safely. */
export interface FormCheck {
  name_on_form: string
  name_on_documents: string | null
  name_tier: NameTier
  dob_on_form: string | null
  dob_match: boolean | null
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
  citizen_dob?: string | null
  /** v1.5: the citizen's CAN when the application was created from one */
  can_id?: string | null
  phone_masked: string
  service: Service
  office_id: string
  office_name: string
  status: AppStatus
  /** v1.4: officer chain position; null unless ready_for_officer */
  stage?: Stage | null
  stage_due_at?: string | null
  stage_sla_hours_left?: number | null
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

/** v1.5: with `can`, name/DOB/phone come from the CAN profile and any typed values are ignored. */
export interface CreateApplicationInput {
  citizen_name?: string | null
  phone?: string | null
  service: Service
  office_id: string
  citizen_dob?: string | null
  can?: string | null
}

/** v1.5 CAN profile: created once per mobile number, never edited. Its name/DOB are printed on the certificate. */
export interface Citizen {
  can: string
  name: string
  dob?: string | null
  phone_masked: string
  address_line?: string | null
  pin_code?: string | null
  created_at: string
}

export interface CitizenInput {
  name: string
  dob?: string | null
  phone: string
  address_line?: string | null
  pin_code?: string | null
}

export interface OfficerActionInput {
  action: OfficerAction
  reason_code?: string | null
  note?: string | null
  /** v1.4: acting officer role; must equal the application's current stage */
  role?: Stage | null
}

export function formCheckOf(c: ConsistencyResult | null | undefined): FormCheck | null {
  const f = c?.form_check
  if (!f || typeof f.name_on_form !== 'string') return null
  return {
    name_on_form: f.name_on_form,
    name_on_documents: typeof f.name_on_documents === 'string' ? f.name_on_documents : null,
    name_tier: (f.name_tier as NameTier) ?? 'not_enough_data',
    dob_on_form: typeof f.dob_on_form === 'string' ? f.dob_on_form : null,
    dob_match: typeof f.dob_match === 'boolean' ? f.dob_match : null,
  }
}
