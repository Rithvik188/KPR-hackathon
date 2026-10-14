// One function per contract §3 endpoint. In fixture mode, returns contract/fixtures JSON after a 300 ms delay.
import type {
  Alert,
  ApplicationDetail,
  ApplicationList,
  ApplicationSummary,
  AppStatus,
  CreateApplicationInput,
  DeclarableType,
  DetectionMetrics,
  Health,
  IssueReport,
  IssueReportInput,
  Notification,
  Office,
  OfficerActionInput,
  OperationsMetrics,
  Stage,
  UploadResult,
  ValidationResult,
} from './types'

export const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === 'true'

export class ApiError extends Error {
  code: string
  status: number

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

type Query = Record<string, string | number | undefined | null>

function withQuery(path: string, query?: Query): string {
  if (!query) return path
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  }
  const qs = params.toString()
  return qs ? `${path}?${qs}` : path
}

async function request<T>(method: string, path: string, body?: FormData | object, query?: Query): Promise<T> {
  const init: RequestInit = { method }
  if (body instanceof FormData) {
    init.body = body
  } else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { 'Content-Type': 'application/json' }
  }
  let res: Response
  try {
    res = await fetch(withQuery(`/api${path}`, query), init)
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the SevaiCheck server')
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const err = data?.error
    throw new ApiError(res.status, err?.code ?? `HTTP_${res.status}`, err?.message ?? res.statusText)
  }
  return data as T
}

// ---- fixture mode -------------------------------------------------------------------------------

export type ValidateFixture = 'accepted' | 'fixable' | 'invalid'
let validateFixture: ValidateFixture = 'fixable'

/** Debug control (fixture mode only): which validate fixture the next upload returns. */
export function setValidateFixture(v: ValidateFixture) {
  validateFixture = v
}

async function fixture<T>(pick: (f: typeof import('./fixtures').fixtures) => unknown): Promise<T> {
  const { fixtures } = await import('./fixtures')
  await new Promise((r) => setTimeout(r, 300))
  return structuredClone(pick(fixtures)) as T
}

// ---- endpoints ----------------------------------------------------------------------------------

export function getHealth(): Promise<Health> {
  if (USE_FIXTURES) {
    return Promise.resolve({ status: 'ok', ocr_engine: 'fixture', ocr_gpu: false, ocr_ready: true, version: 'fixture' })
  }
  return request('GET', '/health')
}

export function validateDocument(file: File, declaredType?: DeclarableType): Promise<ValidationResult> {
  if (USE_FIXTURES) return fixture((f) => ({ ...f.validate[validateFixture], declared_type: declaredType ?? null }))
  const form = new FormData()
  form.append('file', file)
  if (declaredType) form.append('declared_type', declaredType)
  return request('POST', '/validate', form)
}

export function getDetectionMetrics(): Promise<DetectionMetrics> {
  if (USE_FIXTURES) return fixture((f) => f.metricsDetection)
  return request('GET', '/metrics/detection')
}

export function getOffices(): Promise<Office[]> {
  if (USE_FIXTURES) return fixture((f) => f.offices)
  return request('GET', '/offices')
}

export function createApplication(input: CreateApplicationInput): Promise<ApplicationSummary> {
  if (USE_FIXTURES) return fixture((f) => ({ ...f.applicationsList.items[0], status: 'submitted', doc_count: 0 }))
  return request('POST', '/applications', input)
}

export function listApplications(params: {
  status?: AppStatus
  office_id?: string
  stage?: Stage
  limit?: number
  offset?: number
} = {}): Promise<ApplicationList> {
  if (USE_FIXTURES) return fixture((f) => f.applicationsList)
  return request('GET', '/applications', undefined, params)
}

export function getApplication(id: string): Promise<ApplicationDetail> {
  if (USE_FIXTURES) return fixture((f) => f.applicationDetail)
  return request('GET', `/applications/${encodeURIComponent(id)}`)
}

export function uploadDocument(applicationId: string, file: File, declaredType: DeclarableType): Promise<UploadResult> {
  if (USE_FIXTURES) {
    return fixture((f) => ({
      document_id: 'doc_fixture',
      validation: { ...f.validate[validateFixture], document_id: 'doc_fixture', declared_type: declaredType },
      application: f.applicationsList.items[0],
      consistency: f.applicationDetail.consistency,
    }))
  }
  const form = new FormData()
  form.append('file', file)
  form.append('declared_type', declaredType)
  return request('POST', `/applications/${encodeURIComponent(applicationId)}/documents`, form)
}

export function documentImageUrl(documentId: string): string {
  return `/api/documents/${encodeURIComponent(documentId)}/image`
}

export function actOnApplication(id: string, input: OfficerActionInput): Promise<ApplicationSummary> {
  if (USE_FIXTURES) return fixture((f) => f.applicationsList.items[0])
  return request('PATCH', `/applications/${encodeURIComponent(id)}`, input)
}

export function listAlerts(status?: 'open' | 'acknowledged'): Promise<Alert[]> {
  if (USE_FIXTURES) return fixture((f) => f.alerts)
  return request('GET', '/alerts', undefined, { status })
}

export function ackAlert(id: string): Promise<Alert> {
  if (USE_FIXTURES) return fixture((f) => ({ ...f.alerts[0], status: 'acknowledged' }))
  return request('POST', `/alerts/${encodeURIComponent(id)}/ack`)
}

export function getOperationsMetrics(days = 30): Promise<OperationsMetrics> {
  if (USE_FIXTURES) return fixture((f) => f.metricsOperations)
  return request('GET', '/metrics/operations', undefined, { days })
}

export function listIssueReports(): Promise<IssueReport[]> {
  if (USE_FIXTURES) return fixture((f) => f.issues)
  return request('GET', '/issues')
}

export function createIssueReport(input: IssueReportInput): Promise<IssueReport> {
  if (USE_FIXTURES) return fixture((f) => ({ ...f.issues[0], ...input }))
  return request('POST', '/issues', input)
}

export function listNotifications(applicationId?: string): Promise<Notification[]> {
  if (USE_FIXTURES) return fixture((f) => f.notifications)
  return request('GET', '/notifications', undefined, { application_id: applicationId })
}

export function weeklyReportUrl(officeId?: string): string {
  return withQuery('/api/reports/weekly.pdf', { office_id: officeId })
}
