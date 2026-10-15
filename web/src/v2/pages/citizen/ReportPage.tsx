import { useLang } from '@/i18n'
import { ReportPage as V1ReportPage } from '@/pages/ReportPage'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'

/** Wraps the existing Report Issue page (same API, same component) with v2 breadcrumbs. Citizens and operators
 * can file a report but not list others' reports (officer-only since v1.8). */
export function ReportPage() {
  const { t } = useLang()
  return (
    <div>
      <Breadcrumbs items={[{ label: t('v2.home.report') }]} />
      <div className="pt-5">
        <V1ReportPage showRecent={false} />
      </div>
    </div>
  )
}
