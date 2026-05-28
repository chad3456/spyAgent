import React from 'react'
import { X, Brain, Sparkles, AlertTriangle, GitMerge, Flag, Eye, Cpu, Server } from 'lucide-react'
import clsx from 'clsx'
import { useIntelStatus, useTeamBrief, useDataSources } from '../hooks/useIntel'
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
  const sources = useDataSources()

  if (!open) return null

  const briefing = brief.data?.briefing?.analysis as BriefingAnalysis | null | undefined
  const threats = brief.data?.threats?.analysis as ThreatAnalysis | null | undefined
  const correlations = brief.data?.correlations?.analysis as CorrelationAnalysis | null | undefined
  const regional = brief.data?.regional as
    | Record<string, AnalystEnvelope<RegionalAnalysis>>
    | undefined

  const isLoading = brief.isLoading || (brief.isFetching && !brief.data)
  const activeEngine = (brief.data?.engine ?? status.data?.activeEngine ?? 'local') as string
  const isClaude = activeEngine === 'claude'
  const ollamaActive = brief.data?.ollamaActive ?? status.data?.ollamaAvailable ?? false

  return (
    <div className="fixed inset-0 z-[2000] flex justify-end">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-3xl h-full bg-[#0a0f1e] border-l border-[#1e3a5f] shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#1e3a5f] bg-gradient-to-r from-[#1e3a5f]/60 to-transparent">
          <div
            className={clsx(
              'w-8 h-8 rounded-lg flex items-center justify-center',
              isClaude
                ? 'bg-gradient-to-br from-violet-600 to-blue-500'
                : 'bg-gradient-to-br from-emerald-600 to-cyan-500',
            )}
          >
            {isClaude ? <Brain className="w-4 h-4 text-white" /> : <Cpu className="w-4 h-4 text-white" />}
          </div>
          <div className="flex-1">
            <h2 className="text-[#e8f0fe] font-bold text-sm leading-tight flex items-center gap-2">
              {isClaude ? 'Claude Analyst Team' : 'Local Analyst Team'}
              <Sparkles className={clsx('w-3.5 h-3.5', isClaude ? 'text-violet-300' : 'text-emerald-300')} />
            </h2>
            <p className="text-[#8ba3c0] text-[10px] leading-tight flex items-center gap-1.5 flex-wrap">
              <EngineBadge isClaude={isClaude} />
              <span>·</span>
              <span>
                {status.data?.briefingModel ?? (isClaude ? 'claude-opus-4-7' : 'local-heuristic-v1')}
                {' + '}
                {status.data?.analystModel ?? (isClaude ? 'claude-haiku-4-5' : 'local-heuristic-v1')}
              </span>
              <span>·</span>
              <span>{status.data?.analysts.length ?? 8} analysts</span>
              {ollamaActive && (
                <>
                  <span>·</span>
                  <span className="flex items-center gap-0.5 text-emerald-300">
                    <Server className="w-2.5 h-2.5" /> Ollama polish on
                  </span>
                </>
              )}
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
          {!isClaude && (
            <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-md p-2.5 text-[11px] text-cyan-200/90">
              <strong className="text-cyan-300">Local heuristic engine active.</strong>{' '}
              No API key required — rule-based synthesis runs against the live OSINT swarm.
              {' '}
              {ollamaActive
                ? 'Bottom-line prose is being polished by your local Ollama model.'
                : 'Set ANTHROPIC_API_KEY for Claude-driven synthesis, or run Ollama on localhost:11434 to polish the prose locally.'}
            </div>
          )}

          {isLoading && (
            <div className="flex items-center gap-2 text-[#8ba3c0] text-[12px]">
              <div
                className={clsx(
                  'w-3 h-3 border-2 rounded-full animate-spin border-t-transparent',
                  isClaude ? 'border-violet-400' : 'border-emerald-400',
                )}
              />
              {isClaude
                ? 'Running 8-analyst team against live OSINT swarm… (15-45 s, Opus brief + Haiku analysts in parallel)'
                : 'Running 8-analyst heuristic team against live OSINT swarm… (typically 1-3 s)'}
            </div>
          )}

          {brief.isError && (
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

          {/* Data sources transparency — confirms no-key OSINT mode */}
          {sources.data && (
            <details className="bg-emerald-500/5 border border-emerald-500/20 rounded-md p-3">
              <summary className="text-[11px] uppercase tracking-wider text-emerald-300 cursor-pointer hover:text-emerald-200 flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5" />
                Data sources ({sources.data.summary.keylessSources} keyless ·{' '}
                {sources.data.summary.activeUpgrades}/{sources.data.summary.optionalUpgrades} upgrades active)
              </summary>
              <div className="mt-3">
                <p className="text-[11px] text-emerald-200/90 mb-3 leading-relaxed">
                  {sources.data.headline}
                </p>
                <div className="grid grid-cols-2 gap-1.5">
                  {sources.data.sources.map((s) => (
                    <div
                      key={s.label}
                      className="bg-[#0a0f1e]/60 border border-[#1e3a5f] rounded px-2 py-1.5 flex items-start gap-2"
                    >
                      <span
                        className={clsx(
                          'w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0',
                          s.mode === 'upgraded'
                            ? 'bg-violet-400'
                            : s.mode === 'keyless-public'
                              ? 'bg-emerald-400'
                              : 'bg-cyan-400',
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-[#e8f0fe] truncate">{s.label}</div>
                        <div className="text-[9px] text-[#8ba3c0] truncate">
                          {s.mode === 'upgraded' && s.envKey
                            ? `upgraded (${s.envKey} set)`
                            : s.mode === 'keyless-public'
                              ? 'public · no key needed'
                              : `keyless · ${s.fallback}`}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex items-center gap-3 text-[9px] text-[#8ba3c0] flex-wrap">
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    public, no key
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    keyless with fallback
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                    upgraded (key set)
                  </span>
                </div>
              </div>
            </details>
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

const EngineBadge: React.FC<{ isClaude: boolean }> = ({ isClaude }) => (
  <span
    className={clsx(
      'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider',
      isClaude
        ? 'bg-violet-500/20 text-violet-300 border border-violet-500/40'
        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
    )}
  >
    {isClaude ? <Brain className="w-2.5 h-2.5" /> : <Cpu className="w-2.5 h-2.5" />}
    {isClaude ? 'Claude' : 'Local'}
  </span>
)

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
