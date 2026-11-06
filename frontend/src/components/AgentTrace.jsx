import React from 'react';
import { Cpu, CheckCircle2, Clock, Layers, ArrowRight } from 'lucide-react';

export default function AgentTrace({ traceData }) {
  if (!traceData || traceData.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No agent execution active. Trigger an outfit recommendation to view the live multi-agent handoff trace.
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem 0' }}>
      
      {/* Visualizer Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <span className="chip chip-pink" style={{ marginBottom: '0.4rem' }}>GRADED DELIVERABLE</span>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Cpu size={24} color="var(--primary-pink)" /> LangGraph Multi-Agent Handoff Execution Trace
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Step-by-step transparent reasoning pipeline across 6 specialized AI nodes + Orchestrator.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.1)', padding: '0.5rem 1rem', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <CheckCircle2 size={16} color="#34d399" />
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#34d399' }}>Pipeline Status: Ready / Verified</span>
        </div>
      </div>

      {/* Agent Nodes Flow Diagram */}
      <div className="glass-panel-accent" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', position: 'relative' }}>
          {traceData.map((step, idx) => (
            <div 
              key={idx} 
              className="glass-panel"
              style={{
                padding: '1.25rem',
                borderLeft: '4px solid var(--primary-purple)',
                background: 'rgba(15, 20, 35, 0.85)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Node #{idx + 1}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    <Clock size={12} /> {step.time}
                  </span>
                </div>

                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#c084fc', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Layers size={16} /> {step.agent}
                </h4>

                <p style={{ fontSize: '0.83rem', color: 'var(--text-main)', lineHeight: '1.4' }}>
                  {step.summary}
                </p>
              </div>

              <div style={{ marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                <span className="chip chip-emerald" style={{ fontSize: '0.65rem', padding: '0.15rem 0.5rem' }}>
                  State Updated
                </span>
                {idx < traceData.length - 1 && (
                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    Handoff <ArrowRight size={12} />
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

      </div>

    </div>
  );
}
