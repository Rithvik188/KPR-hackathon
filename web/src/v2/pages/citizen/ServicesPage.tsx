import { ArrowRight, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useLang } from '@/i18n'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'
import { SCHEMES } from '@/v2/data/schemes'
import { usePortalBase } from '@/v2/portalBase'

/** Schemes directory: ~14 realistic TN schemes with required documents. Only the 4 SevaiCheck supports are
 * clickable into Apply; the rest are informational ("coming soon"). No document upload happens on this page.
 * In the operator portal it is reference only: operators don't apply, so the Apply buttons are hidden. */
export function ServicesPage() {
  const { t, lang } = useLang()
  const canApply = usePortalBase() === '/portal'

  return (
    <div className="space-y-5">
      <Breadcrumbs items={[{ label: t('v2.services.title') }]} />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.services.title')}</h1>
        <p className="text-muted-foreground">{t('v2.services.subtitle')}</p>
        {!canApply && <p className="mt-1 text-sm text-muted-foreground">{t('v2.services.operatorNote')}</p>}
      </div>

      {/* Table view (desktop) */}
      <Card className="hidden py-0 sm:block">
        <CardContent className="overflow-x-auto px-0">
          <Table className="min-w-[860px]">
            <TableHeader>
              <TableRow>
                <TableHead className="w-48">{t('v2.services.table.scheme')}</TableHead>
                <TableHead className="w-44">{t('v2.services.table.department')}</TableHead>
                <TableHead>{t('v2.services.table.documents')}</TableHead>
                <TableHead className="w-28 whitespace-nowrap">{t('v2.services.table.sla')}</TableHead>
                <TableHead className="w-28 whitespace-nowrap">{t('v2.services.table.status')}</TableHead>
                <TableHead className="w-24 text-right" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {SCHEMES.map((scheme) => (
                <TableRow key={scheme.code}>
                  <TableCell>
                    <p className="font-medium">{lang === 'ta' ? scheme.nameTa : scheme.nameEn}</p>
                    <p className="font-mono text-[11px] text-muted-foreground">{scheme.code}</p>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{t(scheme.deptKey)}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {(lang === 'ta' ? scheme.documentsTa : scheme.documentsEn).join(' · ')}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    <span className="inline-flex items-center gap-1 whitespace-nowrap">
                      <Clock className="size-3.5 shrink-0" aria-hidden />
                      {t('v2.services.days', { n: scheme.slaDays })}
                    </span>
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {scheme.service ? (
                      <Badge className="bg-success-soft text-success">{t('v2.services.open')}</Badge>
                    ) : (
                      <Badge className="bg-secondary text-muted-foreground">{t('v2.services.comingSoon')}</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {canApply && scheme.service && (
                      <Button asChild size="sm">
                        <Link to={`/portal/apply/${scheme.service}`}>
                          {t('v2.services.apply')}
                          <ArrowRight aria-hidden />
                        </Link>
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Card view (mobile) */}
      <div className="space-y-3 sm:hidden">
        {SCHEMES.map((scheme) => (
          <Card key={scheme.code}>
            <CardContent className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{lang === 'ta' ? scheme.nameTa : scheme.nameEn}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">{scheme.code}</p>
                </div>
                {scheme.service ? (
                  <Badge className="bg-success-soft text-success">{t('v2.services.open')}</Badge>
                ) : (
                  <Badge className="bg-secondary text-muted-foreground">{t('v2.services.comingSoon')}</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">{t(scheme.deptKey)}</p>
              <p className="text-sm text-muted-foreground">{(lang === 'ta' ? scheme.documentsTa : scheme.documentsEn).join(' · ')}</p>
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="size-3.5" aria-hidden />
                {t('v2.services.days', { n: scheme.slaDays })}
              </p>
              {canApply && scheme.service && (
                <Button asChild size="sm" className="w-full">
                  <Link to={`/portal/apply/${scheme.service}`}>
                    {t('v2.services.apply')}
                    <ArrowRight aria-hidden />
                  </Link>
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
