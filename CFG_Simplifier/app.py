"""
app.py
------
Context-Free Grammar (CFG) Simplification Simulator.
Academic, single-page, minimal interface.
Executes the mandatory reduction order:
1. Removal of Null (ε) Productions
2. Removal of Unit Productions
3. Removal of Useless Symbols (Generating -> Reachable)
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Tuple, Set

from cfg import (
    CFG,
    Production,
    parse_cfg,
    simplify_grammar,
    SimplificationPipelineResult,
    NullRemovalResult,
    UnitRemovalResult,
    UselessRemovalResult,
    EPSILON_REPRESENTATIONS
)

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & ACADEMIC STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CFG Simplification Simulator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal Academic Styling (White/Neutral background, clear typography, no AI gradients)
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #111827;
        background-color: #FFFFFF;
    }
    h1, h2, h3, h4 {
        color: #111827;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .academic-header {
        border-bottom: 2px solid #1F2937;
        padding-bottom: 8px;
        margin-bottom: 1.25rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 8px;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 1px solid #D1D5DB;
        padding-bottom: 4px;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        color: #111827;
    }
    .step-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #374151;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 2px;
    }
    .grammar-display {
        font-family: "Courier New", Courier, monospace;
        font-size: 1.05rem;
        background: #F3F4F6;
        border: 1px solid #D1D5DB;
        padding: 10px 14px;
        border-radius: 3px;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #111827;
        margin: 6px 0;
    }
    .final-grammar-box {
        font-family: "Courier New", Courier, monospace;
        font-size: 1.15rem;
        font-weight: 600;
        background: #ECFDF5;
        border: 2px solid #059669;
        color: #065F46;
        padding: 12px 18px;
        border-radius: 4px;
        white-space: pre-wrap;
        line-height: 1.6;
        margin: 10px 0;
    }
    .no-change-notice {
        font-style: italic;
        color: #4B5563;
        background: #F3F4F6;
        padding: 6px 12px;
        border-radius: 3px;
        display: inline-block;
        margin: 4px 0;
    }
    .summary-badge {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
DEFAULT_GRAMMAR = """S -> abS | abA | abB
A -> cd
B -> aB
C -> dc"""

if "grammar_input" not in st.session_state:
    st.session_state.grammar_input = DEFAULT_GRAMMAR

if "pipeline_result" not in st.session_state:
    # Run initial default simulation
    parsed, _ = parse_cfg(st.session_state.grammar_input)
    if parsed:
        st.session_state.pipeline_result = simplify_grammar(parsed)
    else:
        st.session_state.pipeline_result = None

# Preset templates for testing
PRESETS = {
    "Reference Example (Non-generating & Unreachable)": """S -> abS | abA | abB
A -> cd
B -> aB
C -> dc""",

    "Nullable Start & Multiple ε-Productions": """S -> AB | a
A -> aA | ε
B -> bB | ε""",

    "Unit Production Chains & Cycles": """S -> A
A -> B | a
B -> C | b
C -> A | c""",

    "Comprehensive Test (Null, Unit & Useless)": """S -> AB | C
A -> aA | ε
B -> b
C -> cC
D -> d"""
}

# -----------------------------------------------------------------------------
# HEADER & INTRODUCTION
# -----------------------------------------------------------------------------
st.markdown('<div class="academic-header">', unsafe_allow_html=True)
st.markdown('<div class="main-title">Context-Free Grammar Simplification Simulator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Step 1: Removal of Useless Symbols &nbsp;|&nbsp; Step 2: Removal of Null (ε) Productions &nbsp;|&nbsp; Step 3: Removal of Unit Productions</div>', unsafe_allow_html=True)
st.caption("Mathematical Execution Order: Step 2: Null (ε) Productions → Step 3: Unit Productions → Step 1: Useless Symbols")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# GRAMMAR INPUT SECTION
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">1. Context-Free Grammar Input</div>', unsafe_allow_html=True)
st.caption("Enter production rules below using '->' or '→'. Separate alternatives with '|'. Use 'ε', 'epsilon', 'lambda', or leave blank for empty strings.")

# Preset buttons
st.markdown("**Quick Preset Grammars:**")
preset_cols = st.columns(4)
for i, (name, text) in enumerate(PRESETS.items()):
    with preset_cols[i]:
        if st.button(name, key=f"preset_{i}", use_container_width=True):
            st.session_state.grammar_input = text
            parsed, err = parse_cfg(text)
            if parsed:
                st.session_state.pipeline_result = simplify_grammar(parsed)
            st.rerun()

user_input = st.text_area(
    "Grammar Productions:",
    value=st.session_state.grammar_input,
    height=140,
    label_visibility="collapsed"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    simplify_btn = st.button("Simplify Grammar", type="primary", use_container_width=True)

if simplify_btn:
    st.session_state.grammar_input = user_input
    parsed_cfg, parse_err = parse_cfg(user_input)
    if parse_err:
        st.error(f"Grammar Validation Error: {parse_err}")
        st.session_state.pipeline_result = None
    else:
        st.session_state.pipeline_result = simplify_grammar(parsed_cfg)
        st.rerun()

result: Optional[SimplificationPipelineResult] = st.session_state.pipeline_result

if not result:
    st.stop()

# -----------------------------------------------------------------------------
# GRAMMAR FORMAL IDENTIFIERS
# -----------------------------------------------------------------------------
orig_cfg = result.original_cfg
st.markdown('<div class="section-title">2. Grammar Analysis & Identifiers</div>', unsafe_allow_html=True)

id_c1, id_c2, id_c3, id_c4 = st.columns(4)
with id_c1:
    st.markdown(f"**Start Symbol ($S$):** `{orig_cfg.start_symbol}`")
with id_c2:
    st.markdown(f"**Variables ($V$):** `{{{', '.join(orig_cfg.variables)}}}`")
with id_c3:
    terms_str = f"{{{', '.join(orig_cfg.terminals)}}}" if orig_cfg.terminals else "∅ (None)"
    st.markdown(f"**Terminals ($\\Sigma$):** `{terms_str}`")
with id_c4:
    st.markdown(f"**Total Productions:** `{len(orig_cfg.productions)}`")

# -----------------------------------------------------------------------------
# STEP 2: REMOVAL OF NULL (ε) PRODUCTIONS
# (Executed 1st in the mandatory mathematical reduction pipeline)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">STEP 2: REMOVAL OF NULL (ε) PRODUCTIONS</div>', unsafe_allow_html=True)

res1: NullRemovalResult = result.step1_null

st.markdown("**Original Grammar:**")
st.markdown(f'<div class="grammar-display">{res1.original_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

if not res1.changed:
    st.markdown(f'<div class="no-change-notice">No changes required. No productions of this type were found.</div>', unsafe_allow_html=True)
else:
    null_vars_str = f"{{{', '.join(sorted(res1.nullable_variables))}}}" if res1.nullable_variables else "∅"
    st.markdown(f"**Nullable Variables ($A \\Rightarrow^* \\epsilon$):** `{null_vars_str}`")

    # Table of removed & generated productions
    step1_rows = []
    if res1.productions_removed:
        for p in res1.productions_removed:
            step1_rows.append({"Action": "REMOVED (ε-production)", "Production Rule": p.to_string(), "Reason": "Eliminated direct null production"})
    if res1.productions_added:
        for p in res1.productions_added:
            step1_rows.append({"Action": "ADDED (Combination)", "Production Rule": p.to_string(), "Reason": "Generated by omitting nullable variable(s)"})

    if step1_rows:
        st.dataframe(pd.DataFrame(step1_rows), use_container_width=True, hide_index=True)

    if res1.start_symbol_nullable:
        st.info(f"💡 Start symbol '{orig_cfg.start_symbol}' is nullable. Introduced fresh start symbol '{res1.new_start_symbol}' with rule '{res1.new_start_symbol} -> {orig_cfg.start_symbol} | ε' to preserve the empty string in L(G).")

st.markdown("**Modified Grammar after Step 2 (Null Removal):**")
st.markdown(f'<div class="grammar-display">{res1.modified_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

with st.expander("Explanation of Step 2 (Null Production Removal)", expanded=False):
    st.markdown(res1.explanation)

# -----------------------------------------------------------------------------
# STEP 3: REMOVAL OF UNIT PRODUCTIONS
# (Executed 2nd in the mandatory mathematical reduction pipeline)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">STEP 3: REMOVAL OF UNIT PRODUCTIONS</div>', unsafe_allow_html=True)

res2: UnitRemovalResult = result.step2_unit

st.markdown("**Input Grammar (from Step 2 - Null Removal):**")
st.markdown(f'<div class="grammar-display">{res2.input_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

if not res2.changed:
    st.markdown(f'<div class="no-change-notice">No changes required. No productions of this type were found.</div>', unsafe_allow_html=True)
else:
    unit_str = ", ".join(p.to_string() for p in res2.unit_productions)
    st.markdown(f"**Unit Productions Identified ($A \\to B$):** `{unit_str}`")

    # Show Unit Closures
    closure_items = []
    for v in sorted(res2.unit_closures.keys()):
        targets = sorted(res2.unit_closures[v])
        if len(targets) > 1:
            closure_items.append(f"Unit({v}) = {{{', '.join(targets)}}}")
    if closure_items:
        st.markdown(f"**Unit Closures:** `{'; '.join(closure_items)}`")

    step2_rows = []
    for p in res2.productions_removed:
        step2_rows.append({"Action": "REMOVED (Unit rule)", "Production Rule": p.to_string(), "Reason": "Direct unit production"})
    for p in res2.productions_added:
        step2_rows.append({"Action": "ADDED (Transferred)", "Production Rule": p.to_string(), "Reason": f"Transferred non-unit production from unit closure"})

    if step2_rows:
        st.dataframe(pd.DataFrame(step2_rows), use_container_width=True, hide_index=True)

st.markdown("**Modified Grammar after Step 3 (Unit Removal):**")
st.markdown(f'<div class="grammar-display">{res2.modified_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

with st.expander("Explanation of Step 3 (Unit Production Removal)", expanded=False):
    st.markdown(res2.explanation)

# -----------------------------------------------------------------------------
# STEP 1: REMOVAL OF USELESS SYMBOLS
# (Executed 3rd in the mandatory mathematical reduction pipeline)
# Phase 1: Generating -> Phase 2: Reachable
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">STEP 1: REMOVAL OF USELESS SYMBOLS</div>', unsafe_allow_html=True)

res3: UselessRemovalResult = result.step3_useless

st.markdown("**Input Grammar (from Step 3 - Unit Removal):**")
st.markdown(f'<div class="grammar-display">{res3.input_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

if not res3.changed:
    st.markdown(f'<div class="no-change-notice">No changes required. No useless symbols were found.</div>', unsafe_allow_html=True)
else:
    # Phase 1: Generating Symbols
    st.markdown("#### Phase 1: Remove Non-Generating Symbols")
    gen_c1, gen_c2 = st.columns(2)
    with gen_c1:
        st.markdown(f"**Generating Variables ($A \\Rightarrow^* w \\in \\Sigma^*$):** `{{{', '.join(sorted(res3.generating_variables))}}}`")
    with gen_c2:
        non_gen_str = f"{{{', '.join(sorted(res3.non_generating_variables))}}}" if res3.non_generating_variables else "∅ (None)"
        st.markdown(f"**Non-Generating Variables Eliminated:** `{non_gen_str}`")

    if res3.productions_removed_non_gen:
        step3_gen_rows = []
        for p in res3.productions_removed_non_gen:
            step3_gen_rows.append({"Action": "REMOVED (Non-generating)", "Production Rule": p.to_string(), "Reason": "Contains variable that cannot derive a terminal string"})
        st.dataframe(pd.DataFrame(step3_gen_rows), use_container_width=True, hide_index=True)

    # Phase 2: Reachable Symbols
    st.markdown("#### Phase 2: Remove Unreachable Symbols")
    reach_c1, reach_c2 = st.columns(2)
    with reach_c1:
        st.markdown(f"**Reachable Variables (from start '{res3.input_cfg.start_symbol}'):** `{{{', '.join(sorted(res3.reachable_variables))}}}`")
    with reach_c2:
        unreach_vars_str = f"{{{', '.join(sorted(res3.unreachable_variables))}}}" if res3.unreachable_variables else "∅ (None)"
        st.markdown(f"**Unreachable Variables Eliminated:** `{unreach_vars_str}`")

    if res3.productions_removed_unreachable:
        step3_reach_rows = []
        for p in res3.productions_removed_unreachable:
            step3_reach_rows.append({"Action": "REMOVED (Unreachable)", "Production Rule": p.to_string(), "Reason": f"Cannot be reached from start symbol '{res3.input_cfg.start_symbol}'"})
        st.dataframe(pd.DataFrame(step3_reach_rows), use_container_width=True, hide_index=True)

st.markdown("**Modified Grammar after Step 1 (Useless Symbol Removal):**")
st.markdown(f'<div class="grammar-display">{res3.final_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

with st.expander("Explanation of Step 1 (Useless Symbol Removal)", expanded=False):
    st.markdown(res3.explanation)

# -----------------------------------------------------------------------------
# FINAL SIMPLIFIED GRAMMAR
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">FINAL SIMPLIFIED GRAMMAR</div>', unsafe_allow_html=True)
st.caption("Clean, minimal equivalent grammar with all null, unit, non-generating, and unreachable productions eliminated.")

st.markdown(f'<div class="final-grammar-box">{result.final_cfg.to_formatted_string()}</div>', unsafe_allow_html=True)

# Comparison metrics
comp_c1, comp_c2, comp_c3, comp_c4 = st.columns(4)
with comp_c1:
    st.metric("Variables", f"{len(orig_cfg.variables)} → {len(result.final_cfg.variables)}")
with comp_c2:
    st.metric("Terminals", f"{len(orig_cfg.terminals)} → {len(result.final_cfg.terminals)}")
with comp_c3:
    st.metric("Productions", f"{len(orig_cfg.productions)} → {len(result.final_cfg.productions)}")
with comp_c4:
    rules_elim = len(orig_cfg.productions) - len(result.final_cfg.productions)
    st.metric("Net Rules Eliminated", f"{rules_elim}")

