// Report Issue (P2-3): anyone at a centre can flag a problem. Three reports of the same kind for one centre
// within 24 hours raise a USER_REPORTED alert on the admin page.
import { Send } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { createIssueReport, getOffices, listIssueReports } from '@/api/client'
import type { IssueCategory, IssueReport, Office, ReporterRole } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useLang } from '@/i18n'
import { ReportList } from '@/pages/admin/RecentReports'

const CATEGORIES: IssueCategory[] = ['scanner_problem', 'long_wait', 'wrong_rejection', 'other']
const ROLES: ReporterRole[] = ['operator', 'citizen', 'officer']

function savedOffice(): string {
  try {
    return localStorage.getItem('sevaicheck.office') ?? ''
  } catch {
    return ''
  }
}

/** `showRecent` lists recent reports for the centre. That list (GET /issues) is officer-only since v1.8, so the
 * citizen and operator portals turn it off. */
export function ReportPage({ showRecent = true }: { showRecent?: boolean } = {}) {
  const { t } = useLang()
  const [params] = useSearchParams()
  const [offices, setOffices] = useState<Office[]>([])
  const [officeId, setOfficeId] = useState(params.get('office') ?? savedOffice())
  const [category, setCategory] = useState<IssueCategory>('scanner_problem')
  const [role, setRole] = useState<ReporterRole>('operator')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [recent, setRecent] = useState<IssueReport[] | null>(null)

  useEffect(() => {
    getOffices()
      .then((list) => {
        setOffices(list)
        setOfficeId((cur) => (list.some((o) => o.id === cur) ? cur : (list[0]?.id ?? '')))
      })
      .catch(() => {})
  }, [])

  const loadRecent = useCallback(() => {
    if (!showRecent || !officeId) return
    listIssueReports()
      .then((all) => setRecent(all.filter((r) => r.office_id === officeId).slice(0, 8)))
      .catch(() => setRecent([]))
  }, [officeId, showRecent])

  useEffect(loadRecent, [loadRecent])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await createIssueReport({ office_id: officeId, category, reporter_role: role, description })
      toast.success(t('report.sent'))
      setDescription('')
      loadRecent()
    } catch (err) {
      toast.error(t('common.error'), { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('report.title')}</h1>
        <p className="text-muted-foreground">{t('report.subtitle')}</p>
      </div>
      <Card>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="report-office">{t('report.office')}</Label>
              <Select value={officeId} onValueChange={setOfficeId}>
                <SelectTrigger id="report-office" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {offices.map((o) => (
                    <SelectItem key={o.id} value={o.id}>
                      {o.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="report-category">{t('report.category')}</Label>
                <Select value={category} onValueChange={(v) => setCategory(v as IssueCategory)}>
                  <SelectTrigger id="report-category" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => (
                      <SelectItem key={c} value={c}>
                        {t(`category.${c}`)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="report-role">{t('report.role')}</Label>
                <Select value={role} onValueChange={(v) => setRole(v as ReporterRole)}>
                  <SelectTrigger id="report-role" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r}>
                        {t(`role.${r}`)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="report-description">{t('report.description')}</Label>
              <Textarea id="report-description" required maxLength={500} rows={3} value={description}
                        onChange={(e) => setDescription(e.target.value)} />
            </div>
            <Button type="submit" size="lg" disabled={busy || !officeId || !description.trim()}>
              <Send aria-hidden />
              {t('report.submit')}
            </Button>
          </form>
        </CardContent>
      </Card>
      {showRecent && (
        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="text-base">{t('report.recent')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ReportList reports={recent} offices={offices} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
