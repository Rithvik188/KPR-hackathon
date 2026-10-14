// Short English labels for issue codes (officer and admin views). Citizen-facing wording always comes from the
// API's msg_en / msg_ta, which the backend fills from contract/messages.json.

export const ISSUE_LABELS: Record<string, string> = {
  FILE_TOO_LARGE: 'File too large',
  UNSUPPORTED_FILE: 'Unsupported file',
  CARD_NOT_FOUND: 'No card found',
  CROPPED: 'Card cut off',
  BLUR: 'Blurry image',
  GLARE: 'Glare on card',
  TOO_DARK: 'Too dark',
  TOO_BRIGHT: 'Too bright',
  LOW_RESOLUTION: 'Low resolution',
  SKEW_CORRECTED: 'Tilt corrected',
  UNKNOWN_DOC_TYPE: 'Unknown document',
  WRONG_DOC_TYPE: 'Wrong document',
  UNREADABLE: 'Unreadable',
  INVALID_CHECKSUM: 'Invalid Aadhaar number',
  INVALID_FORMAT: 'Invalid number format',
  OCR_AUTOCORRECTED: 'Character auto-corrected',
  DUPLICATE_SUSPECTED: 'Possible duplicate',
  AADHAAR_BACK_MISSING: 'Aadhaar back missing',
  NAME_LIKELY_MATCH: 'Names likely match',
  NAME_MISMATCH: 'Name mismatch',
  DOB_MISMATCH: 'DOB mismatch',
}

export function issueLabel(code: string): string {
  return ISSUE_LABELS[code] ?? code.replaceAll('_', ' ').toLowerCase()
}

/** Reasons an officer can give for "Request fix" or "Reject". Each maps to a bilingual message in the SMS. */
export const REASON_CODES = [
  'BLUR',
  'GLARE',
  'CROPPED',
  'TOO_DARK',
  'LOW_RESOLUTION',
  'UNREADABLE',
  'WRONG_DOC_TYPE',
  'AADHAAR_BACK_MISSING',
  'NAME_MISMATCH',
  'DOB_MISMATCH',
  'INVALID_CHECKSUM',
  'INVALID_FORMAT',
] as const
