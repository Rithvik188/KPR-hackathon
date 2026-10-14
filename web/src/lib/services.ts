// Per-service required documents and the officer chain, read from contract/services.json (contract v1.4).
import data from '@contract/services.json'

import type { Service, Stage, SupportingType } from '@/api/types'

export function supportingTypeFor(service: Service): SupportingType | null {
  const required = (data.services[service]?.required ?? []) as (string | string[])[]
  const found = required.find((slot): slot is string => typeof slot === 'string' && data.supporting_types.includes(slot))
  return (found as SupportingType | undefined) ?? null
}

export function serviceCode(service: Service): string {
  return data.services[service]?.code ?? ''
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
