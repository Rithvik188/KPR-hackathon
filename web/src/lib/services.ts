// Per-service required documents and the officer chain, read from contract/services.json (contract v1.4).
import data from '@contract/services.json'

import type { Service, Stage, SupportingType } from '@/api/types'

type ServiceDef = { code: string; required: (string | string[])[] }
// Indexed loosely so a service the contract file doesn't list yet degrades to "ID proofs only, no code".
const SERVICES = data.services as Record<string, ServiceDef | undefined>

export function supportingTypeFor(service: Service): SupportingType | null {
  const required = SERVICES[service]?.required ?? []
  const found = required.find((slot): slot is string => typeof slot === 'string' && data.supporting_types.includes(slot))
  return (found as SupportingType | undefined) ?? null
}

export function serviceCode(service: Service): string {
  return SERVICES[service]?.code ?? ''
}

export const STAGE_ORDER = data.stages.order as Stage[]

export function stageName(stage: Stage, lang: 'en' | 'ta'): string {
  return data.stages[stage][lang === 'ta' ? 'name_ta' : 'name_en']
}

export function stageSlaHours(stage: Stage): number {
  return data.stages[stage].sla_hours
}

export function nextStage(stage: Stage | null | undefined): Stage | null {
  if (!stage) return null
  const i = STAGE_ORDER.indexOf(stage)
  return i >= 0 && i + 1 < STAGE_ORDER.length ? STAGE_ORDER[i + 1] : null
}

export function supportingLabel(type: SupportingType, lang: 'en' | 'ta'): string {
  return data.supporting_labels[type][lang]
}
