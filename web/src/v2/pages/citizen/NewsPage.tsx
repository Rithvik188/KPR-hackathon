import { Newspaper } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { useLang } from '@/i18n'
import { Breadcrumbs } from '@/v2/components/Breadcrumbs'

// Static, clearly-demo announcements. No live feed — this is a prototype.
const ANNOUNCEMENTS = [
  {
    date: '2026-10-10',
    en: 'e-District simplifies the certificate approval chain: the Deputy Tahsildar stage is removed. Applications now move VAO → Revenue Inspector → Tahsildar.',
    ta: 'இ-மாவட்டம் சான்றிதழ் ஒப்புதல் சங்கிலியை எளிமையாக்குகிறது: உதவி வட்டாட்சியர் நிலை நீக்கப்பட்டது. விண்ணப்பங்கள் இப்போது கிராம நிர்வாக அலுவலர் → வருவாய் ஆய்வாளர் → வட்டாட்சியர் என நகரும்.',
  },
  {
    date: '2026-10-05',
    en: 'Coimbatore e-Sevai centres now verify Aadhaar and PAN documents instantly at the counter using automated checks, reducing repeat visits.',
    ta: 'கோயம்புத்தூர் இ-சேவை மையங்கள் இப்போது தானியங்கு சரிபார்ப்பு மூலம் கவுண்டரிலேயே ஆதார் மற்றும் பான் ஆவணங்களை உடனடியாகச் சரிபார்க்கின்றன, மீண்டும் வருகை தேவையைக் குறைக்கிறது.',
  },
  {
    date: '2026-09-28',
    en: 'Revenue Department sets a 72-hour service-level target for certificate applications once all documents are accepted.',
    ta: 'அனைத்து ஆவணங்களும் ஏற்கப்பட்ட பின் சான்றிதழ் விண்ணப்பங்களுக்கு 72 மணி நேர சேவை இலக்கை வருவாய்த் துறை நிர்ணயித்துள்ளது.',
  },
]

export function NewsPage() {
  const { t } = useLang()

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Breadcrumbs items={[{ label: t('v2.news.title') }]} />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('v2.news.title')}</h1>
        <p className="text-muted-foreground">{t('v2.news.subtitle')}</p>
      </div>
      <div className="space-y-3">
        {ANNOUNCEMENTS.map((item) => (
          <Card key={item.date}>
            <CardContent className="flex gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                <Newspaper className="size-4" aria-hidden />
              </span>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">{item.date}</p>
                <p lang="ta" className="font-tamil text-sm leading-relaxed">
                  {item.ta}
                </p>
                <p className="text-sm leading-relaxed text-muted-foreground">{item.en}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
