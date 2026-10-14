// Compile-time drift check: every backend response schema (types.gen.ts, from /openapi.json) must fit the
// hand-written contract types the UI uses. If the backend renames or retypes a field, `npm run build` fails here.
// Regenerate with `npm run gen:types` (backend running). Add a line when a new endpoint lands.
import type { components } from './types.gen'
import type * as T from './types'

type S = components['schemas']
// Pydantic fields with defaults come out optional in OpenAPI but are always present in responses.
type DeepRequired<X> = X extends object ? { [K in keyof X]-?: DeepRequired<X[K]> } : X
type Fits<Generated, Handwritten> = DeepRequired<Generated> extends Handwritten ? true : false

export const contractChecks: [
  Fits<S['OfficeOut'], T.Office>,
  Fits<S['ApplicationSummaryOut'], T.ApplicationSummary>,
  Fits<S['ApplicationDetailOut'], T.ApplicationDetail>,
  Fits<S['ApplicationListOut'], T.ApplicationList>,
  Fits<S['UploadResultOut'], T.UploadResult>,
  Fits<S['ValidationResult'], T.ValidationResult>,
  Fits<S['ConsistencyResult'], T.ConsistencyResult>,
  Fits<S['NotificationOut'], T.Notification>,
  Fits<S['AlertOut'], T.Alert>,
  Fits<S['IssueReportOut'], T.IssueReport>,
  Fits<S['OperationsMetricsOut'], T.OperationsMetrics>,
] = [true, true, true, true, true, true, true, true, true, true, true]
