// Fixture-mode responses (VITE_USE_FIXTURES=true). Loaded lazily by client.ts, so the normal build never uses them.
import alerts from '@contract/fixtures/alerts.json'
import applicationDetail from '@contract/fixtures/application_detail.json'
import applicationsList from '@contract/fixtures/applications_list.json'
import issues from '@contract/fixtures/issues.json'
import metricsDetection from '@contract/fixtures/metrics_detection.json'
import metricsOperations from '@contract/fixtures/metrics_operations.json'
import notifications from '@contract/fixtures/notifications.json'
import offices from '@contract/fixtures/offices.json'
import validateAccepted from '@contract/fixtures/validate_accepted.json'
import validateFixable from '@contract/fixtures/validate_fixable.json'
import validateInvalid from '@contract/fixtures/validate_invalid.json'

export const fixtures = {
  alerts,
  applicationDetail,
  applicationsList,
  issues,
  metricsDetection,
  metricsOperations,
  notifications,
  offices,
  validate: { accepted: validateAccepted, fixable: validateFixable, invalid: validateInvalid },
}
