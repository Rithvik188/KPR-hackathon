// UI-label dictionary (English default, Tamil toggle). Issue messages arrive bilingual from the API and
// are never translated here. Tamil strings should be checked by a native speaker before the demo.
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

export type Lang = 'en' | 'ta'

const en = {
  'nav.counter': 'Counter',
  'nav.officer': 'Officer',
  'nav.admin': 'Admin',
  'nav.metrics': 'Metrics',
  'nav.report': 'Report Issue',

  'doc.aadhaar_front': 'Aadhaar (front)',
  'doc.aadhaar_back': 'Aadhaar (back)',
  'doc.pan': 'PAN card',
  'doc.voter_id': 'Voter ID',
  'doc.unknown': 'Unknown document',

  'status.accepted': 'Accepted',
  'status.fixable': 'Retake needed',
  'status.invalid': 'Invalid',
  'app.submitted': 'Collecting documents',
  'app.needs_fix': 'Needs fix',
  'app.ready_for_officer': 'Ready for officer',
  'app.approved': 'Approved',
  'app.rejected': 'Rejected',

  'counter.title': 'Document check',
  'counter.subtitle': 'Upload or photograph the card. SevaiCheck checks it in seconds.',
  'counter.docType': 'Document type',
  'counter.choose': 'Take photo or choose file',
  'counter.chooseHint': 'JPG or PNG, up to 10 MB',
  'counter.checking': 'Checking the document…',
  'counter.retake': 'Retake',
  'counter.checkedIn': 'Checked in {s} s',
  'counter.fields': 'Details read from the card',
  'counter.debugFixture': 'Fixture to return',

  'field.id_number_display': 'ID number',
  'field.name': 'Name',
  'field.dob': 'Date of birth',
  'field.gender': 'Gender',
  'field.father_name': "Father's name",
  'field.pin_code': 'PIN code',

  'common.comingSoon': 'This screen is being built.',
  'common.error': 'Something went wrong',
}

type Key = keyof typeof en

const ta: Record<Key, string> = {
  'nav.counter': 'கவுண்டர்',
  'nav.officer': 'அலுவலர்',
  'nav.admin': 'நிர்வாகம்',
  'nav.metrics': 'அளவீடுகள்',
  'nav.report': 'புகார் அளி',

  'doc.aadhaar_front': 'ஆதார் (முன்பக்கம்)',
  'doc.aadhaar_back': 'ஆதார் (பின்பக்கம்)',
  'doc.pan': 'பான் அட்டை',
  'doc.voter_id': 'வாக்காளர் அடையாள அட்டை',
  'doc.unknown': 'அறியப்படாத ஆவணம்',

  'status.accepted': 'ஏற்கப்பட்டது',
  'status.fixable': 'மீண்டும் எடுக்கவும்',
  'status.invalid': 'செல்லாதது',
  'app.submitted': 'ஆவணங்கள் சேகரிப்பில்',
  'app.needs_fix': 'திருத்தம் தேவை',
  'app.ready_for_officer': 'அலுவலர் பரிசீலனைக்குத் தயார்',
  'app.approved': 'ஒப்புதல் அளிக்கப்பட்டது',
  'app.rejected': 'நிராகரிக்கப்பட்டது',

  'counter.title': 'ஆவணச் சரிபார்ப்பு',
  'counter.subtitle': 'அட்டையைப் பதிவேற்றவும் அல்லது படம் எடுக்கவும். சில வினாடிகளில் சரிபார்க்கப்படும்.',
  'counter.docType': 'ஆவண வகை',
  'counter.choose': 'படம் எடு அல்லது கோப்பைத் தேர்ந்தெடு',
  'counter.chooseHint': 'JPG அல்லது PNG, அதிகபட்சம் 10 MB',
  'counter.checking': 'ஆவணம் சரிபார்க்கப்படுகிறது…',
  'counter.retake': 'மீண்டும் எடு',
  'counter.checkedIn': '{s} வினாடிகளில் சரிபார்க்கப்பட்டது',
  'counter.fields': 'அட்டையிலிருந்து படித்த விவரங்கள்',
  'counter.debugFixture': 'Fixture to return',

  'field.id_number_display': 'அடையாள எண்',
  'field.name': 'பெயர்',
  'field.dob': 'பிறந்த தேதி',
  'field.gender': 'பாலினம்',
  'field.father_name': 'தந்தையின் பெயர்',
  'field.pin_code': 'அஞ்சல் குறியீடு',

  'common.comingSoon': 'இந்தத் திரை உருவாக்கத்தில் உள்ளது.',
  'common.error': 'ஏதோ தவறு நடந்தது',
}

const dictionaries: Record<Lang, Record<Key, string>> = { en, ta }
const STORAGE_KEY = 'sevaicheck.lang'

function readStoredLang(): Lang {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'ta' ? 'ta' : 'en'
  } catch {
    return 'en'
  }
}

interface LangContextValue {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: Key, vars?: Record<string, string | number>) => string
}

const LangContext = createContext<LangContextValue | null>(null)

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readStoredLang)

  const setLang = useCallback((next: Lang) => {
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // storage unavailable (private window): keep the choice for this session only
    }
  }, [])

  const t = useCallback(
    (key: Key, vars?: Record<string, string | number>) => {
      let text = dictionaries[lang][key] ?? en[key] ?? key
      for (const [k, v] of Object.entries(vars ?? {})) text = text.replace(`{${k}}`, String(v))
      return text
    },
    [lang],
  )

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

export function useLang(): LangContextValue {
  const ctx = useContext(LangContext)
  if (!ctx) throw new Error('useLang must be used inside <LangProvider>')
  return ctx
}

export type I18nKey = Key
