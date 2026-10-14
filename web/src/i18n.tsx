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
  'counter.newApplication': 'New application',
  'counter.applicant': 'Applicant',
  'counter.office': 'Centre',
  'counter.citizenName': 'Citizen name',
  'counter.phone': 'Mobile number',
  'counter.service': 'Service',
  'counter.create': 'Create application',
  'counter.documents': 'Documents',
  'counter.createFirst': 'Create the application to start checking documents.',
  'counter.attempt': 'Attempt {n}',
  'counter.idProof': 'ID proof',
  'counter.application': 'Application',
  'counter.sentToOfficer': 'Sent to officer',
  'counter.sentToOfficerHint': 'All documents are verified. The officer will review the application.',
  'counter.openInOfficer': 'Open in officer view',
  'counter.reportProblem': 'Report a problem at this centre',
  'counter.phoneTitle': "Citizen's phone (SMS)",
  'counter.noSms': 'No messages yet',
  'counter.appIssues': 'Application issues',

  'service.community_certificate': 'Community certificate',
  'service.income_certificate': 'Income certificate',
  'service.nativity_certificate': 'Nativity certificate',
  'service.ration_card_update': 'Ration card update',

  'consistency.title': 'Name and date-of-birth check',
  'tier.match': 'Names match',
  'tier.likely_match': 'Likely match: officer will confirm',
  'tier.mismatch': 'Names do not match',
  'tier.not_enough_data': 'Waiting for documents',
  'consistency.dobMatch': 'Date of birth matches',
  'consistency.dobMismatch': 'Date of birth differs',

  'officer.title': 'Officer queue',
  'officer.subtitle': 'Applications whose documents passed the counter check come first, most urgent SLA on top.',
  'officer.status': 'Status',
  'officer.office': 'Office',
  'officer.allStatuses': 'All statuses',
  'officer.allOffices': 'All offices',
  'officer.citizen': 'Citizen',
  'officer.service': 'Service',
  'officer.flags': 'Flags',
  'officer.sla': 'SLA',
  'officer.docs': 'Docs',
  'officer.empty': 'No applications match these filters.',
  'officer.refresh': 'Refresh',
  'officer.prev': 'Previous',
  'officer.next': 'Next',
  'officer.showing': '{from}–{to} of {total}',
  'officer.slaOverdue': '{h} h overdue',
  'officer.slaLeft': '{h} h left',
  'officer.documents': 'Documents',
  'officer.history': 'History',
  'officer.decision': 'Decision',
  'officer.actions': 'Officer action',
  'officer.approve': 'Approve',
  'officer.requestFix': 'Request fix',
  'officer.reject': 'Reject',
  'officer.reason': 'Reason',
  'officer.chooseReason': 'Choose a reason',
  'officer.note': 'Note',
  'officer.noteRequired': 'Note (required for rejection)',
  'officer.confirm': 'Confirm',
  'officer.cancel': 'Cancel',
  'officer.imageDeleted': 'Card image deleted after the decision (privacy rule).',
  'officer.imageMissing': 'No card image stored',
  'officer.evidence': 'Evidence',
  'officer.done.approve': 'Application approved. Card images deleted.',
  'officer.done.reject': 'Application rejected. Card images deleted.',
  'officer.done.request_fix': 'Correction requested. The citizen has been notified.',
  'officer.resubmissions': 'Resubmissions',
  'officer.created': 'Created',

  'admin.title': 'District operations',
  'admin.subtitle': 'Where and why documents get sent back across Coimbatore district.',
  'admin.banner': 'Synthetic operational data (seeded) for demonstration.',
  'admin.kpi.applications': 'Applications (30 days)',
  'admin.kpi.ftr': 'First-time-right',
  'admin.kpi.resubmissions': 'Avg resubmissions',
  'admin.kpi.backlog': 'Backlog now',
  'admin.kpi.sla': 'SLA breaches now',
  'admin.map': 'Offices (last 7 days)',
  'admin.mapLegend': 'Colour: reject rate vs district average. Size: backlog.',
  'admin.legend.high': 'Well above district',
  'admin.legend.mid': 'Above district',
  'admin.legend.ok': 'Near or below',
  'admin.alerts': 'Alerts',
  'admin.noAlerts': 'No alerts right now.',
  'admin.ack': 'Acknowledge',
  'admin.acked': 'Acknowledged',
  'admin.action': 'Suggested action',
  'admin.daily': 'Daily flow (30 days)',
  'admin.backlog': 'Open backlog',
  'admin.byIssue': 'Why applications were sent back',
  'admin.offices': 'Offices (30 days)',
  'admin.reports': 'Recent issue reports',
  'admin.showTable': 'Show table',
  'admin.hideTable': 'Hide table',
  'admin.submitted': 'Submitted',
  'admin.approvedSeries': 'Approved',
  'admin.rejectedSeries': 'Rejected',
  'admin.rejectRate': 'Reject rate',
  'admin.submissions': 'Submissions',
  'admin.topIssue': 'Top issue',
  'admin.taluk': 'Taluk',
  'admin.date': 'Date',

  'report.title': 'Report a problem',
  'report.subtitle': 'Tell the district team about a problem at a centre. Repeated reports raise an alert.',
  'report.office': 'Centre',
  'report.category': 'What went wrong',
  'report.role': 'You are',
  'report.description': 'Describe the problem',
  'report.submit': 'Send report',
  'report.sent': 'Report sent. Thank you.',
  'report.recent': 'Recent reports for this centre',
  'report.none': 'No reports yet.',
  'category.scanner_problem': 'Scanner or camera problem',
  'category.long_wait': 'Long waiting time',
  'category.wrong_rejection': 'Wrong rejection',
  'category.other': 'Other',
  'role.citizen': 'Citizen',
  'role.operator': 'Counter operator',
  'role.officer': 'Officer',

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
  'counter.newApplication': 'புதிய விண்ணப்பம்',
  'counter.applicant': 'விண்ணப்பதாரர்',
  'counter.office': 'மையம்',
  'counter.citizenName': 'விண்ணப்பதாரர் பெயர்',
  'counter.phone': 'கைபேசி எண்',
  'counter.service': 'சேவை',
  'counter.create': 'விண்ணப்பத்தை உருவாக்கு',
  'counter.documents': 'ஆவணங்கள்',
  'counter.createFirst': 'ஆவணங்களைச் சரிபார்க்க முதலில் விண்ணப்பத்தை உருவாக்கவும்.',
  'counter.attempt': 'முயற்சி {n}',
  'counter.idProof': 'அடையாளச் சான்று',
  'counter.application': 'விண்ணப்பம்',
  'counter.sentToOfficer': 'அலுவலருக்கு அனுப்பப்பட்டது',
  'counter.sentToOfficerHint': 'அனைத்து ஆவணங்களும் சரிபார்க்கப்பட்டன. அலுவலர் விண்ணப்பத்தைப் பரிசீலிப்பார்.',
  'counter.openInOfficer': 'அலுவலர் பார்வையில் திற',
  'counter.reportProblem': 'இந்த மையத்தின் சிக்கலைப் புகாரளி',
  'counter.phoneTitle': 'குடிமகனின் கைபேசி (SMS)',
  'counter.noSms': 'இன்னும் செய்திகள் இல்லை',
  'counter.appIssues': 'விண்ணப்பச் சிக்கல்கள்',

  'service.community_certificate': 'சமூகச் சான்றிதழ்',
  'service.income_certificate': 'வருமானச் சான்றிதழ்',
  'service.nativity_certificate': 'இருப்பிடச் சான்றிதழ்',
  'service.ration_card_update': 'குடும்ப அட்டை புதுப்பிப்பு',

  'consistency.title': 'பெயர் மற்றும் பிறந்த தேதி சரிபார்ப்பு',
  'tier.match': 'பெயர்கள் பொருந்துகின்றன',
  'tier.likely_match': 'பெயர்கள் ஒத்துள்ளன: அலுவலர் உறுதிப்படுத்துவார்',
  'tier.mismatch': 'பெயர்கள் பொருந்தவில்லை',
  'tier.not_enough_data': 'ஆவணங்களுக்காகக் காத்திருக்கிறது',
  'consistency.dobMatch': 'பிறந்த தேதி பொருந்துகிறது',
  'consistency.dobMismatch': 'பிறந்த தேதி வேறுபடுகிறது',

  'officer.title': 'அலுவலர் வரிசை',
  'officer.subtitle': 'கவுண்டர் சரிபார்ப்பில் தேறிய விண்ணப்பங்கள் முதலில், அவசரமானவை மேலே.',
  'officer.status': 'நிலை',
  'officer.office': 'அலுவலகம்',
  'officer.allStatuses': 'அனைத்து நிலைகளும்',
  'officer.allOffices': 'அனைத்து அலுவலகங்களும்',
  'officer.citizen': 'விண்ணப்பதாரர்',
  'officer.service': 'சேவை',
  'officer.flags': 'குறிப்புகள்',
  'officer.sla': 'காலக்கெடு',
  'officer.docs': 'ஆவணங்கள்',
  'officer.empty': 'இந்த வடிகட்டிகளுக்கு விண்ணப்பங்கள் இல்லை.',
  'officer.refresh': 'புதுப்பி',
  'officer.prev': 'முந்தையது',
  'officer.next': 'அடுத்தது',
  'officer.showing': '{total}-இல் {from}–{to}',
  'officer.slaOverdue': '{h} மணி நேரம் தாமதம்',
  'officer.slaLeft': '{h} மணி நேரம் உள்ளது',
  'officer.documents': 'ஆவணங்கள்',
  'officer.history': 'வரலாறு',
  'officer.decision': 'முடிவு',
  'officer.actions': 'அலுவலர் நடவடிக்கை',
  'officer.approve': 'ஒப்புதல் அளி',
  'officer.requestFix': 'திருத்தம் கோரு',
  'officer.reject': 'நிராகரி',
  'officer.reason': 'காரணம்',
  'officer.chooseReason': 'காரணத்தைத் தேர்ந்தெடுக்கவும்',
  'officer.note': 'குறிப்பு',
  'officer.noteRequired': 'குறிப்பு (நிராகரிப்புக்குக் கட்டாயம்)',
  'officer.confirm': 'உறுதிசெய்',
  'officer.cancel': 'ரத்துசெய்',
  'officer.imageDeleted': 'முடிவுக்குப் பின் அட்டைப் படம் நீக்கப்பட்டது (தனியுரிமை விதி).',
  'officer.imageMissing': 'அட்டைப் படம் சேமிக்கப்படவில்லை',
  'officer.evidence': 'சான்று',
  'officer.done.approve': 'விண்ணப்பம் ஒப்புதல் பெற்றது. அட்டைப் படங்கள் நீக்கப்பட்டன.',
  'officer.done.reject': 'விண்ணப்பம் நிராகரிக்கப்பட்டது. அட்டைப் படங்கள் நீக்கப்பட்டன.',
  'officer.done.request_fix': 'திருத்தம் கோரப்பட்டது. விண்ணப்பதாரருக்குத் தெரிவிக்கப்பட்டது.',
  'officer.resubmissions': 'மறு சமர்ப்பிப்புகள்',
  'officer.created': 'உருவாக்கப்பட்டது',

  'admin.title': 'மாவட்டச் செயல்பாடுகள்',
  'admin.subtitle': 'கோயம்புத்தூர் மாவட்டத்தில் ஆவணங்கள் எங்கே, ஏன் திருப்பி அனுப்பப்படுகின்றன.',
  'admin.banner': 'செயற்கை செயல்பாட்டுத் தரவு (மாதிரி) விளக்கத்திற்காக மட்டும்.',
  'admin.kpi.applications': 'விண்ணப்பங்கள் (30 நாட்கள்)',
  'admin.kpi.ftr': 'முதல் முறையிலேயே சரி',
  'admin.kpi.resubmissions': 'சராசரி மறு சமர்ப்பிப்பு',
  'admin.kpi.backlog': 'நிலுவையில் உள்ளவை',
  'admin.kpi.sla': 'காலக்கெடு மீறல்கள்',
  'admin.map': 'அலுவலகங்கள் (கடந்த 7 நாட்கள்)',
  'admin.mapLegend': 'நிறம்: மாவட்ட சராசரியுடன் நிராகரிப்பு விகிதம். அளவு: நிலுவை.',
  'admin.legend.high': 'மாவட்டத்தை விட மிக அதிகம்',
  'admin.legend.mid': 'மாவட்டத்தை விட அதிகம்',
  'admin.legend.ok': 'சராசரி அல்லது குறைவு',
  'admin.alerts': 'எச்சரிக்கைகள்',
  'admin.noAlerts': 'தற்போது எச்சரிக்கைகள் இல்லை.',
  'admin.ack': 'ஏற்றுக்கொள்',
  'admin.acked': 'ஏற்றுக்கொள்ளப்பட்டது',
  'admin.action': 'பரிந்துரைக்கப்பட்ட நடவடிக்கை',
  'admin.daily': 'தினசரி ஓட்டம் (30 நாட்கள்)',
  'admin.backlog': 'நிலுவை',
  'admin.byIssue': 'விண்ணப்பங்கள் திருப்பி அனுப்பப்பட்ட காரணங்கள்',
  'admin.offices': 'அலுவலகங்கள் (30 நாட்கள்)',
  'admin.reports': 'சமீபத்திய புகார்கள்',
  'admin.showTable': 'அட்டவணையைக் காட்டு',
  'admin.hideTable': 'அட்டவணையை மறை',
  'admin.submitted': 'சமர்ப்பிக்கப்பட்டவை',
  'admin.approvedSeries': 'ஒப்புதல்',
  'admin.rejectedSeries': 'நிராகரிப்பு',
  'admin.rejectRate': 'நிராகரிப்பு விகிதம்',
  'admin.submissions': 'சமர்ப்பிப்புகள்',
  'admin.topIssue': 'முதன்மைச் சிக்கல்',
  'admin.taluk': 'வட்டம்',
  'admin.date': 'தேதி',

  'report.title': 'சிக்கலைப் புகாரளி',
  'report.subtitle': 'ஒரு மையத்தில் உள்ள சிக்கலை மாவட்டக் குழுவுக்குத் தெரிவிக்கவும். தொடர் புகார்கள் எச்சரிக்கையை எழுப்பும்.',
  'report.office': 'மையம்',
  'report.category': 'என்ன தவறு நடந்தது',
  'report.role': 'நீங்கள்',
  'report.description': 'சிக்கலை விவரிக்கவும்',
  'report.submit': 'புகாரை அனுப்பு',
  'report.sent': 'புகார் அனுப்பப்பட்டது. நன்றி.',
  'report.recent': 'இந்த மையத்தின் சமீபத்திய புகார்கள்',
  'report.none': 'இன்னும் புகார்கள் இல்லை.',
  'category.scanner_problem': 'ஸ்கேனர் அல்லது கேமரா சிக்கல்',
  'category.long_wait': 'நீண்ட காத்திருப்பு',
  'category.wrong_rejection': 'தவறான நிராகரிப்பு',
  'category.other': 'மற்றவை',
  'role.citizen': 'குடிமகன்',
  'role.operator': 'கவுண்டர் இயக்குநர்',
  'role.officer': 'அலுவலர்',

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
