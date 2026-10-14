import { useLang } from '@/i18n'
import { ReportPage as V1ReportPage } from '@/pages/ReportPage'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'

/** Wraps the existing Report Issue page (same API, same component) with v2 breadcrumbs. */
export function ReportPage() {
  const { t } = useLang()
  return (
    <div>
      <Breadcrumbs items={[{ label: t('v2.home.report') }]} />
      <div className="pt-5">
        <V1ReportPage />
      </div>
    </div>
  )
}
