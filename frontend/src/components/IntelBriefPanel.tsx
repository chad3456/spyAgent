import React from 'react'
import { X, Brain, Sparkles, AlertTriangle, GitMerge, Flag, Eye } from 'lucide-react'
import clsx from 'clsx'
import { useIntelStatus, useTeamBrief } from '../hooks/useIntel'
import type {
  BriefingAnalysis,
  ThreatAnalysis,
  CorrelationAnalysis,
  RegionalAnalysis,
  AnalystEnvelope,
} from '../types/intel'

interface IntelBriefPanelProps {
  open: boolean
  onClose: () => void
}

const SEVERITY_STYLES: Record<string, { bg: string; fg: string }> = {
  CRITICAL: { bg: '#ff375f22', fg: '#ff375f' },
  HIGH: { bg: '#ff9f0a22', fg: '#ff9f0a' },
  MEDIUM: { bg: '#ffd60a22', fg: '#ffd60a' },
  LOW: { bg: '#32d74b22', fg: '#32d74b' },
  BASELINE: { bg: '#64d2ff22', fg: '#64d2ff' },
}

const SeverityBadge: React.FC<{ value: string }> = ({ value }) => {
  const s = SEVERITY_STYLES[value] ?? SEVERITY_STYLES.MEDIUM
  return (
    <span
      className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider"
      style={{ background: s.bg, color: s.fg }}
    >
      {value}
    </span>
  )
}

const SectionTitle: React.FC<{ icon: React.ReactNode; children: React.ReactNode }> = ({ icon, children }) => (
  <h3 className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[#64d2ff] font-bold mb-2">
    {icon}
    {children}
  </h3>
)

export const IntelBriefPanel: React.FC<IntelBriefPanelProps> = ({ open, onClose }) => {
  const status = useIntelStatus()
  const brief = useTeamBrief(open)

  if (!open) return null

  const briefing = brief.data?.briefing?.analysis as BriefingAnalysis | null | undefined
  const threats = brief.data?.threats?.analysis as ThreatAnalysis | null | undefined
  const correlations = brief.data?.correlations?.analysis as CorrelationAnalysis | null | undefined
  const regional = brief.data?.regional as
    | Record<string, AnalystEnvelope<RegionalAnalysis>>
    | undefined

  const isDisabled = brief.data?.disabled || status.data?.claudeAvailable === false
  const isLoading = brief.isLoading || (brief.isFetching && !brief.data)

  return (
    <div className="fixed inset-0 z-[2000] flex justify-end">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-3xl h-full bg-[#0a0f1e] border-l border-[#1e3a5f] shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#1e3a5f] bg-gradient-to-r from-[#1e3a5f]/60 to-transparent">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-[#e8f0fe] font-bold text-sm leading-tight flex items-center gap-2">
              Claude Analyst Team
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
            </h2>
            <p className="text-[#8ba3c0] text-[10px] leading-tight">
              {status.data?.briefingModel ?? 'claude-opus-4-7'} + {status.data?.analystModel ?? 'claude-haiku-4-5'} ·{' '}
              {status.data?.analysts.length ?? 8} analysts in parallel
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-[#1e3a5f]/60 text-[#8ba3c0] hover:text-[#e8f0fe]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {isDisabled && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-md p-3 text-[12px] text-amber-200">
              <strong className="text-amber-300">Claude analyst team offline.</strong>{' '}
              {brief.data?.reason ??
                'Set ANTHROPIC_API_KEY in the backend environment to enable real-time intelligence synthesis from the OSINT swarm.'}
            </div>
          )}

          {!isDisabled && isLoading && (
            <div className="flex items-center gap-2 text-[#8ba3c0] text-[12px]">
              <div className="w-3 h-3 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
              Running 8-analyst team against live OSINT swarm output… (15-45s, single Opus brief + 7 Haiku analysts in parallel)
            </div>
          )}

          {!isDisabled && brief.isError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-md p-3 text-[12px] text-red-200">
              <strong className="text-red-300">Team brief failed.</strong>{' '}
              {(brief.error as Error)?.message ?? 'Unknown error'}
            </div>
          )}

          {briefing && (
            <>
              {/* Bottom line */}
              <section>
                <SectionTitle icon={<Sparkles className="w-3.5 h-3.5" />}>Bottom line</SectionTitle>
                <div className="bg-gradient-to-r from-violet-500/10 to-blue-500/10 border border-violet-500/30 rounded-md p-3">
                  <p className="text-[13px] text-[#e8f0fe] leading-relaxed">{briefing.bottomLine}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[9px] uppercase tracking-wider text-[#8ba3c0]">Confidence:</span>
                    <SeverityBadge value={briefing.confidence} />
                    {brief.data?.teamUsage && (
                      <span className="ml-auto text-[9px] text-[#8ba3c0]">
                        {brief.data.teamUsage.totalInputTokens.toLocaleString()} in /{' '}
                        {brief.data.teamUsage.totalOutputTokens.toLocaleString()} out tokens
                        {brief.data.teamUsage.totalCacheReadInputTokens > 0 && (
                          <> · {brief.data.teamUsage.totalCacheReadInputTokens.toLocaleString()} cached</>
                        )}
                      </span>
                    )}
                  </div>
                </div>
              </section>

              {/* Top threats */}
              {briefing.topThreats.length > 0 && (
                <section>
                  <SectionTitle icon={<AlertTriangle className="w-3.5 h-3.5" />}>Top threats</SectionTitle>
                  <div className="space-y-2">
                    {briefing.topThreats.map((t, i) => (
                      <div
                        key={`${t.title}-${i}`}
                        className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded-md p-3"
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <span className="text-[12px] font-semibold text-[#e8f0fe]">{t.title}</span>
                          <SeverityBadge value={t.severity} />
                        </div>
                        <p className="text-[11px] text-[#8ba3c0] leading-relaxed">{t.rationale}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Regional snapshots */}
              {briefing.regionalSnapshots.length > 0 && (
                <section>
                  <SectionTitle icon={<Flag className="w-3.5 h-3.5" />}>Regional snapshots</SectionTitle>
                  <div className="grid grid-cols-1 gap-2">
                    {briefing.regionalSnapshots.map((s) => (
                      <div
                        key={s.country}
                        className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded-md p-3"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[12px] font-bold text-[#e8f0fe]">{s.country}</span>
                          <SeverityBadge value={s.posture} />
                        </div>
                        <p className="text-[11px] text-[#8ba3c0] leading-relaxed">{s.oneLine}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Key correlations */}
              {briefing.keyCorrelations.length > 0 && (
                <section>
                  <SectionTitle icon={<GitMerge className="w-3.5 h-3.5" />}>Cross-feed correlations</SectionTitle>
                  <div className="space-y-2">
                    {briefing.keyCorrelations.map((c, i) => (
                      <div
                        key={`${c.title}-${i}`}
                        className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded-md p-3"
                      >
                        <div className="text-[12px] font-semibold text-[#e8f0fe] mb-1">{c.title}</div>
                        <div className="flex flex-wrap gap-1 mb-1">
                          {c.feeds.map((f) => (
                            <span
                              key={f}
                              className="text-[9px] px-1.5 py-0.5 bg-violet-500/15 text-violet-300 rounded uppercase tracking-wider"
                            >
                              {f}
                            </span>
                          ))}
                        </div>
                        <p className="text-[11px] text-[#8ba3c0] leading-relaxed">{c.implication}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Watch items */}
              {briefing.watchItems.length > 0 && (
                <section>
                  <SectionTitle icon={<Eye className="w-3.5 h-3.5" />}>Watch items (next 12-24h)</SectionTitle>
                  <ul className="space-y-1.5">
                    {briefing.watchItems.map((w, i) => (
                      <li
                        key={i}
                        className="text-[12px] text-[#e8f0fe] bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded px-3 py-2 leading-relaxed"
                      >
                        <span className="text-[#64d2ff] mr-1.5">▸</span>
                        {w}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}

          {/* Drill-down: per-analyst raw output */}
          {(threats || correlations || regional) && (
            <details className="bg-[#0a0f1e]/60 border border-[#1e3a5f] rounded-md p-3">
              <summary className="text-[11px] uppercase tracking-wider text-[#8ba3c0] cursor-pointer hover:text-[#e8f0fe]">
                Drill down — individual analyst output
              </summary>
              <div className="mt-3 space-y-4">
                {threats?.threats && threats.threats.length > 0 && (
                  <div>
                    <h4 className="text-[10px] uppercase tracking-wider text-[#64d2ff] font-bold mb-1.5">
                      ThreatAnalyst — {threats.threats.length} threats · data quality {threats.dataQuality}
                    </h4>
                    <div className="space-y-1.5">
                      {threats.threats.map((t) => (
                        <div key={t.id} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[11px] font-semibold text-[#e8f0fe]">{t.title}</span>
                            <span className="flex items-center gap-1">
                              <SeverityBadge value={t.severity} />
                              <span className="text-[9px] text-[#8ba3c0]">{(t.confidence * 100).toFixed(0)}%</span>
                            </span>
                          </div>
                          <p className="text-[10px] text-[#8ba3c0] mb-1">{t.summary}</p>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[9px] text-[#64d2ff]">{t.region}</span>
                            {t.supportingSignals.map((s) => (
                              <span
                                key={s}
                                className="text-[9px] px-1 py-0.5 bg-[#1e3a5f]/60 text-[#8ba3c0] rounded"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {regional && Object.keys(regional).length > 0 && (
                  <div>
                    <h4 className="text-[10px] uppercase tracking-wider text-[#64d2ff] font-bold mb-1.5">
                      Regional analysts
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {Object.entries(regional).map(([cc, env]) => {
                        const a = env.analysis
                        if (!a) return null
                        return (
                          <div key={cc} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[11px] font-bold text-[#e8f0fe]">{cc}</span>
                              <SeverityBadge value={a.escalationRisk} />
                              <span className="text-[10px] text-[#8ba3c0] truncate">{a.headline}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[10px]">
                              <RegionalList title="Own activity" items={a.ownActivity} />
                              <RegionalList title="Threats against" items={a.threatsAgainst} />
                              <RegionalList title="Internal signals" items={a.internalSignals} />
                              <RegionalList title="Assets observed" items={a.keyAssetsObserved} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {correlations?.correlations && correlations.correlations.length > 0 && (
                  <div>
                    <h4 className="text-[10px] uppercase tracking-wider text-[#64d2ff] font-bold mb-1.5">
                      CorrelationAgent — {correlations.correlations.length} patterns
                    </h4>
                    <div className="space-y-1.5">
                      {correlations.correlations.map((c) => (
                        <div key={c.id} className="bg-[#0a0f1e]/80 border border-[#1e3a5f] rounded p-2">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[11px] font-semibold text-[#e8f0fe]">{c.title}</span>
                            <span className="text-[9px] text-violet-300">strength {(c.strength * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-[10px] text-[#8ba3c0] mb-1">{c.summary}</p>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {c.feeds.map((f) => (
                              <span
                                key={f}
                                className="text-[9px] px-1 py-0.5 bg-violet-500/15 text-violet-300 rounded"
                              >
                                {f}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>

        {/* Footer */}
        {brief.data?.generatedAt && (
          <div className="flex-shrink-0 border-t border-[#1e3a5f] px-4 py-2 flex items-center justify-between text-[10px] text-[#8ba3c0]">
            <span>Generated {new Date(brief.data.generatedAt).toLocaleTimeString()}</span>
            <button
              onClick={() => brief.refetch()}
              disabled={brief.isFetching}
              className={clsx(
                'px-2 py-0.5 rounded border text-[10px] transition-colors',
                brief.isFetching
                  ? 'bg-[#1e3a5f]/20 border-[#1e3a5f]/40 text-[#8ba3c0] cursor-wait'
                  : 'bg-[#1e3a5f]/60 hover:bg-[#1e3a5f] border-[#1e3a5f] text-[#e8f0fe]',
              )}
            >
              {brief.isFetching ? 'Refreshing…' : 'Re-run team'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const RegionalList: React.FC<{ title: string; items: string[] }> = ({ title, items }) => (
  <div>
    <div className="text-[9px] uppercase tracking-wider text-[#64d2ff] mb-0.5">{title}</div>
    {items.length === 0 ? (
      <div className="text-[#8ba3c0] italic">—</div>
    ) : (
      <ul className="space-y-0.5">
        {items.slice(0, 5).map((it, i) => (
          <li key={i} className="text-[#e8f0fe]/90 leading-tight">
            • {it}
          </li>
        ))}
      </ul>
    )}
  </div>
)
