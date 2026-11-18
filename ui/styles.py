"""Scoped Axial-inspired editorial CSS for MIND / MACHINE (THE DECISION STUDIO)."""

from __future__ import annotations

import streamlit as st


def inject_editorial_styles() -> None:
    """Inject the complete Axial-inspired design system stylesheet into Streamlit."""
    st.markdown(
        """
<style>
:root {
  --bg-main: #F5F4F0;
  --surface-primary: #FFFFFF;
  --surface-secondary: #ECEAE4;
  --text-primary: #141414;
  --text-secondary: #676B69;
  --border-hairline: #D8D8D2;
  --stage-dark: #151719;
  --surface-dark-elevated: #232629;
  --border-dark-hairline: #2F3337;
  --text-dark-primary: #F5F4F0;
  --text-dark-secondary: #9EA3A0;
  --accent: #C9E76B;
  --verified: #2D7452;
  --failed: #B63E3D;
  --warning: #9B680B;
  --font-display: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Arial", system-ui, sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", system-ui, sans-serif;
  --font-mono: "SFMono-Regular", "Cascadia Code", "Consolas", "Liberation Mono", monospace;
  --ease-editorial: cubic-bezier(0.22, 1, 0.36, 1);
}

/* Global Canvas & Reset */
html, body, .stApp {
  background-color: var(--bg-main) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden !important;
}

/* Hide default Streamlit chrome clutter while preserving accessible sidebar toggle */
#MainMenu, footer {
  visibility: hidden;
}
header[data-testid="stHeader"] {
  background: rgba(245, 244, 240, 0.88) !important;
  backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--border-hairline);
}

/* Main container layout */
.block-container {
  max-width: 1520px !important;
  padding-top: 2.25rem !important;
  padding-bottom: 4.5rem !important;
  padding-left: 2.75rem !important;
  padding-right: 2.75rem !important;
}

/* Sidebar — Editorial Studio Index */
section[data-testid="stSidebar"] {
  background-color: var(--stage-dark) !important;
  border-right: 1px solid var(--border-dark-hairline) !important;
}
section[data-testid="stSidebar"] * {
  color: var(--text-dark-primary);
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] small {
  color: var(--text-dark-secondary) !important;
}

/* Sidebar Radio Navigation Overrides */
section[data-testid="stSidebar"] div[role="radiogroup"] {
  gap: 0.25rem !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
  background: transparent !important;
  border-left: 2px solid transparent !important;
  border-radius: 0 !important;
  padding: 0.62rem 0.75rem !important;
  margin: 0 !important;
  transition: border-color 180ms var(--ease-editorial), background-color 180ms var(--ease-editorial);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
  background: var(--surface-dark-elevated) !important;
  border-left-color: rgba(201, 231, 107, 0.45) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: var(--surface-dark-elevated) !important;
  border-left: 2px solid var(--accent) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
  font-family: var(--font-mono) !important;
  font-size: 11.5px !important;
  font-weight: 600 !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--text-dark-primary) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
  display: none !important;
}

/* Native Streamlit Button Styling — Editorial Precision */
.stButton > button, .stDownloadButton > button {
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  border-radius: 2px !important;
  padding: 0.68rem 1.15rem !important;
  border: 1px solid var(--text-primary) !important;
  background-color: var(--surface-primary) !important;
  color: var(--text-primary) !important;
  box-shadow: none !important;
  transition: background-color 180ms var(--ease-editorial), color 180ms var(--ease-editorial), border-color 180ms var(--ease-editorial);
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background-color: var(--text-primary) !important;
  color: var(--bg-main) !important;
  border-color: var(--text-primary) !important;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background-color: var(--stage-dark) !important;
  color: var(--accent) !important;
  border: 1px solid var(--stage-dark) !important;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
  background-color: var(--accent) !important;
  color: var(--text-primary) !important;
  border-color: var(--text-primary) !important;
}
section[data-testid="stSidebar"] .stButton > button {
  background-color: var(--surface-dark-elevated) !important;
  color: var(--text-dark-primary) !important;
  border: 1px solid var(--border-dark-hairline) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* Accessible Focus States */
button:focus-visible, a:focus-visible, input:focus-visible, summary:focus-visible {
  outline: 2px solid var(--text-primary) !important;
  outline-offset: 2px !important;
}

/* Editorial Top Instrument Strip */
.mm-top-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.65rem 0;
  border-top: 2px solid var(--text-primary);
  border-bottom: 1px solid var(--border-hairline);
  margin-bottom: 2rem;
}
.mm-top-strip-left, .mm-top-strip-right {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

/* Metadata & Monospace Overlines */
.mm-overline {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.mm-mono {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
}

/* Editorial Hero Section */
.mm-hero-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 2.5rem;
  align-items: end;
  padding-bottom: 2.25rem;
  border-bottom: 1px solid var(--border-hairline);
  margin-bottom: 1.75rem;
  animation: mmEditorialReveal 200ms var(--ease-editorial) both;
}
.mm-display-headline {
  font-family: var(--font-display);
  font-size: clamp(48px, 6.4vw, 96px);
  font-weight: 800;
  line-height: 0.91;
  letter-spacing: -0.05em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0.45rem 0 1.15rem 0;
  white-space: pre-line;
}
.mm-hero-subtitle {
  font-family: var(--font-body);
  font-size: 16.5px;
  line-height: 1.55;
  color: var(--text-secondary);
  max-width: 58ch;
  margin: 0;
}
.mm-hero-monument {
  background: var(--surface-primary);
  border: 1px solid var(--border-hairline);
  border-top: 3px solid var(--text-primary);
  padding: 1.5rem 1.65rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1rem;
}

/* Section Headings (42-64px desktop) */
.mm-section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 1rem;
  padding-bottom: 1.1rem;
  border-bottom: 1px solid var(--border-hairline);
  margin-bottom: 1.5rem;
}
.mm-section-title {
  font-family: var(--font-display);
  font-size: clamp(34px, 3.8vw, 56px);
  font-weight: 800;
  line-height: 0.96;
  letter-spacing: -0.04em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0;
}

/* Minimalist Metric Rail (Prominent data values: 40-76px) */
.mm-metric-rail {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: var(--surface-primary);
  border: 1px solid var(--border-hairline);
  margin-bottom: 2.75rem;
}
.mm-metric-cell {
  padding: 1.5rem 1.6rem;
  border-right: 1px solid var(--border-hairline);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 156px;
  transition: background-color 180ms var(--ease-editorial);
}
.mm-metric-cell:last-child {
  border-right: none;
}
.mm-metric-cell:hover {
  background-color: var(--surface-secondary);
}
.mm-metric-value {
  font-family: var(--font-display);
  font-size: clamp(34px, 3.8vw, 60px);
  font-weight: 800;
  line-height: 0.95;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  margin: 0.55rem 0 0.45rem 0;
  word-break: break-word;
}
.mm-metric-value-compact {
  font-family: var(--font-display);
  font-size: clamp(22px, 2.3vw, 34px);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  margin: 0.65rem 0 0.45rem 0;
}
.mm-metric-foot {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
}

/* Validation Status Badges */
.mm-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 0.28rem 0.65rem;
  border-radius: 2px;
  border: 1px solid currentColor;
  white-space: nowrap;
}
.mm-source-chip {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.48rem;
  background: var(--surface-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-hairline);
  margin-right: 0.3rem;
  margin-bottom: 0.25rem;
}
.mm-source-chip-dark {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.48rem;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-dark-primary);
  border: 1px solid var(--border-dark-hairline);
  margin-right: 0.3rem;
  margin-bottom: 0.25rem;
}

/* Dark Showcase Stage — "THE PLAN, EXPLAINED." */
.mm-dark-stage {
  background-color: var(--stage-dark);
  color: var(--text-dark-primary);
  padding: 3rem 2.75rem;
  border: 1px solid var(--stage-dark);
  margin-bottom: 3rem;
}
.mm-dark-stage-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 1.5rem;
  padding-bottom: 1.75rem;
  border-bottom: 1px solid var(--border-dark-hairline);
  margin-bottom: 2rem;
}
.mm-dark-stage-title {
  font-family: var(--font-display);
  font-size: clamp(38px, 4.6vw, 64px);
  font-weight: 800;
  line-height: 0.94;
  letter-spacing: -0.045em;
  text-transform: uppercase;
  color: var(--text-dark-primary);
  margin: 0.35rem 0 0 0;
}
.mm-dark-grid-top {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}
.mm-dark-grid-bottom {
  display: grid;
  grid-template-columns: 4fr 4fr 4fr;
  gap: 1.25rem;
}
.mm-dark-card {
  background-color: var(--surface-dark-elevated);
  border: 1px solid var(--border-dark-hairline);
  padding: 1.6rem 1.65rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1.1rem;
  transition: border-color 180ms var(--ease-editorial);
}
.mm-dark-card:hover {
  border-color: rgba(201, 231, 107, 0.55);
}
.mm-dark-domain-num {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--accent);
  text-transform: uppercase;
}
.mm-dark-headline {
  font-family: var(--font-display);
  font-size: clamp(26px, 2.6vw, 40px);
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.03em;
  color: var(--text-dark-primary);
  font-variant-numeric: tabular-nums;
  margin: 0.2rem 0;
}

/* Editorial Domain Instrument Section (Screen 02: THE PLAN) */
.mm-domain-section {
  background: var(--surface-primary);
  border: 1px solid var(--border-hairline);
  border-top: 2px solid var(--text-primary);
  padding: 2.25rem 2.4rem;
  margin-bottom: 2.25rem;
}
.mm-domain-layout {
  display: grid;
  grid-template-columns: 3.5fr 8.5fr;
  gap: 2.5rem;
  align-items: start;
}
.mm-domain-index-big {
  font-family: var(--font-display);
  font-size: clamp(52px, 5vw, 80px);
  font-weight: 800;
  line-height: 0.86;
  letter-spacing: -0.05em;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}
.mm-decision-monument {
  font-family: var(--font-display);
  font-size: clamp(32px, 3.6vw, 54px);
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: -0.035em;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  margin: 0.25rem 0 0.75rem 0;
}

/* Progress / Occupancy / Allocation Tracks */
.mm-track-outer {
  width: 100%;
  height: 14px;
  background: var(--surface-secondary);
  border: 1px solid var(--border-hairline);
  display: flex;
  overflow: hidden;
  margin: 0.65rem 0;
}
.mm-track-outer-dark {
  width: 100%;
  height: 10px;
  background: #151719;
  border: 1px solid var(--border-dark-hairline);
  display: flex;
  overflow: hidden;
  margin: 0.55rem 0;
}

/* Editorial Ledger Tables */
.mm-ledger-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14.5px;
}
.mm-ledger-table th {
  font-family: var(--font-mono);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--text-secondary);
  text-align: left;
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--text-primary);
  background: var(--surface-secondary);
}
.mm-ledger-table td {
  padding: 0.8rem 0.75rem;
  border-bottom: 1px solid var(--border-hairline);
  color: var(--text-primary);
  vertical-align: top;
  font-variant-numeric: tabular-nums;
}
.mm-ledger-table tr:last-child td {
  border-bottom: 1px solid var(--text-primary);
}

/* Rejection Card Treatment (Screen 01, 03, 04) */
.mm-rejection-card {
  background: var(--surface-primary);
  border: 1px solid var(--border-hairline);
  border-left: 4px solid var(--failed);
  padding: 1.25rem 1.5rem;
  margin-bottom: 0.9rem;
}
.mm-rejection-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 1.5rem;
  margin-top: 0.65rem;
}

/* Expander Overrides for Audit Trail */
div[data-testid="stExpander"] {
  background: var(--surface-primary) !important;
  border: 1px solid var(--border-hairline) !important;
  border-radius: 0 !important;
  margin-bottom: 0.65rem !important;
}
div[data-testid="stExpander"] summary p {
  font-family: var(--font-mono) !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

@keyframes mmEditorialReveal {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Breakpoints (Laptop, Tablet, Mobile) */
@media (max-width: 1180px) {
  .block-container {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
  }
  .mm-hero-grid,
  .mm-dark-grid-top,
  .mm-domain-layout {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  .mm-dark-grid-bottom {
    grid-template-columns: 1fr 1fr;
  }
  .mm-metric-rail {
    grid-template-columns: repeat(2, 1fr);
  }
  .mm-metric-cell:nth-child(2) {
    border-right: none;
  }
  .mm-metric-cell:nth-child(1),
  .mm-metric-cell:nth-child(2) {
    border-bottom: 1px solid var(--border-hairline);
  }
}

@media (max-width: 767px) {
  .block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1.25rem !important;
  }
  .mm-display-headline {
    font-size: clamp(44px, 11vw, 62px);
  }
  .mm-section-title,
  .mm-dark-stage-title {
    font-size: clamp(30px, 8vw, 42px);
  }
  .mm-metric-rail,
  .mm-dark-grid-bottom,
  .mm-rejection-grid {
    grid-template-columns: 1fr;
  }
  .mm-metric-cell {
    border-right: none !important;
    border-bottom: 1px solid var(--border-hairline);
    min-height: auto;
  }
  .mm-metric-cell:last-child {
    border-bottom: none;
  }
  .mm-dark-stage {
    padding: 1.75rem 1.25rem;
  }
  .mm-domain-section {
    padding: 1.5rem 1.25rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
        """,
        unsafe_allow_html=True,
    )
