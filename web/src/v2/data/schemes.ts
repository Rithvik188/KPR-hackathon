// Realistic TN e-Sevai / e-District scheme directory for the citizen portal's Schemes page.
// The 4 schemes also present in contract/services.json (the ones SevaiCheck validates) are "open" and
// link into the Apply flow; everything else is informational only ("coming soon").
import type { Service } from '@/api/types'

export interface SchemeInfo {
  code: string
  nameEn: string
  nameTa: string
  deptKey: 'v2.services.deptRevenue' | 'v2.services.deptCivilSupplies'
  documentsEn: string[]
  documentsTa: string[]
  slaDays: number
  /** Present only for the 4 schemes SevaiCheck supports; links the row into Apply. */
  service?: Service
}

export const SCHEMES: SchemeInfo[] = [
  {
    code: 'REV-101', nameEn: 'Community Certificate', nameTa: 'சமூகச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', "Parent's / sibling's community certificate"],
    documentsTa: ['ஆதார் அட்டை', 'பெற்றோர் / உடன்பிறந்தோரின் சமூகச் சான்றிதழ்'],
    slaDays: 15, service: 'community_certificate',
  },
  {
    code: 'REV-102', nameEn: 'Nativity Certificate', nameTa: 'பூர்வீகச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Birth certificate'],
    documentsTa: ['ஆதார் அட்டை', 'பிறப்புச் சான்றிதழ்'],
    slaDays: 7, service: 'nativity_certificate',
  },
  {
    code: 'REV-103', nameEn: 'Income Certificate', nameTa: 'வருமானச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Income proof (salary certificate / payslip)'],
    documentsTa: ['ஆதார் அட்டை', 'வருமானச் சான்று (சம்பளச் சான்றிதழ் / ஊதியச் சீட்டு)'],
    slaDays: 15, service: 'income_certificate',
  },
  {
    code: 'CS-RC', nameEn: 'Ration Card Update', nameTa: 'குடும்ப அட்டை திருத்தம்', deptKey: 'v2.services.deptCivilSupplies',
    documentsEn: ['Aadhaar card', 'Address proof (electricity bill / rent agreement)'],
    documentsTa: ['ஆதார் அட்டை', 'முகவரிச் சான்று (மின் கட்டண ரசீது / வாடகை ஒப்பந்தம்)'],
    slaDays: 15, service: 'ration_card_update',
  },
  {
    code: 'REV-104', nameEn: 'Legal Heir Certificate', nameTa: 'வாரிசுச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Death certificate', 'Family card'], documentsTa: ['ஆதார் அட்டை', 'இறப்புச் சான்றிதழ்', 'குடும்ப அட்டை'],
    slaDays: 30,
  },
  {
    code: 'REV-105', nameEn: 'Solvency Certificate', nameTa: 'நிதிநிலைச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Property documents', 'Income proof'], documentsTa: ['ஆதார் அட்டை', 'சொத்து ஆவணங்கள்', 'வருமானச் சான்று'],
    slaDays: 30,
  },
  {
    code: 'REV-106', nameEn: 'No Objection Certificate (land use)', nameTa: 'தடையில்லைச் சான்றிதழ் (நில பயன்பாடு)', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Patta', 'Survey sketch'], documentsTa: ['ஆதார் அட்டை', 'பட்டா', 'சர்வே வரைபடம்'],
    slaDays: 21,
  },
  {
    code: 'REV-107', nameEn: 'Residence Certificate', nameTa: 'குடியிருப்புச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Address proof'], documentsTa: ['ஆதார் அட்டை', 'முகவரிச் சான்று'],
    slaDays: 7,
  },
  {
    code: 'REV-108', nameEn: 'Unemployment Certificate', nameTa: 'வேலையில்லாத் திண்டாட்டச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Educational certificates'], documentsTa: ['ஆதார் அட்டை', 'கல்விச் சான்றிதழ்கள்'],
    slaDays: 15,
  },
  {
    code: 'REV-109', nameEn: 'Agricultural Income Certificate', nameTa: 'விவசாய வருமானச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Patta', 'Adangal extract'], documentsTa: ['ஆதார் அட்டை', 'பட்டா', 'அடங்கல் பிரதி'],
    slaDays: 15,
  },
  {
    code: 'REV-110', nameEn: 'Inter-caste Marriage Certificate', nameTa: 'கலப்புத் திருமணச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar cards (both)', 'Marriage certificate', 'Community certificates'],
    documentsTa: ['ஆதார் அட்டைகள் (இருவரும்)', 'திருமணச் சான்றிதழ்', 'சமூகச் சான்றிதழ்கள்'],
    slaDays: 21,
  },
  {
    code: 'CS-NFC', nameEn: 'New Family Card', nameTa: 'புதிய குடும்ப அட்டை', deptKey: 'v2.services.deptCivilSupplies',
    documentsEn: ['Aadhaar cards (all members)', 'Address proof'], documentsTa: ['ஆதார் அட்டைகள் (அனைத்து உறுப்பினர்கள்)', 'முகவரிச் சான்று'],
    slaDays: 30,
  },
  {
    code: 'REV-111', nameEn: 'First Graduate Certificate', nameTa: 'முதல் பட்டதாரிச் சான்றிதழ்', deptKey: 'v2.services.deptRevenue',
    documentsEn: ['Aadhaar card', 'Parents’ educational records', 'Degree certificate'],
    documentsTa: ['ஆதார் அட்டை', 'பெற்றோரின் கல்வி ஆவணங்கள்', 'பட்டச் சான்றிதழ்'],
    slaDays: 15,
  },
]

export const OPEN_SERVICES = new Set<Service>(SCHEMES.filter((s) => s.service).map((s) => s.service!))
