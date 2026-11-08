"""
cfg.py
------
Context-Free Grammar (CFG) Simplification Engine.
Implements the mathematically mandatory reduction order:
1. Removal of Null (ε) Productions
2. Removal of Unit Productions
3. Removal of Useless Symbols (Phase 1: Generating, Phase 2: Reachable)

Reference: Theory of Computation / Formal Language Theory.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import itertools
import re


EPSILON_REPRESENTATIONS = {"", "ε", "epsilon", "lambda", "λ"}


@dataclass(frozen=True)
class Production:
    """Represents a single production rule: LHS -> RHS (tuple of symbol strings)."""
    lhs: str
    rhs: Tuple[str, ...]  # Empty tuple () denotes epsilon

    @property
    def is_epsilon(self) -> bool:
        return len(self.rhs) == 0 or self.rhs == ("",)

    @property
    def is_unit(self) -> bool:
        # A unit production has RHS of length 1 consisting of a variable
        return len(self.rhs) == 1

    def rhs_str(self) -> str:
        if self.is_epsilon:
            return "ε"
        return "".join(self.rhs)

    def to_string(self) -> str:
        return f"{self.lhs} -> {self.rhs_str()}"

    def __str__(self) -> str:
        return self.to_string()


@dataclass
class CFG:
    """Formal definition of a Context-Free Grammar: G = (V, Sigma, R, S)."""
    variables: List[str]
    terminals: List[str]
    productions: List[Production]
    start_symbol: str

    def get_productions_for(self, variable: str) -> List[Production]:
        return [p for p in self.productions if p.lhs == variable]

    def to_grouped_dict(self) -> Dict[str, List[Tuple[str, ...]]]:
        """Groups productions by LHS variable preserving insertion order."""
        grouped: Dict[str, List[Tuple[str, ...]]] = {}
        for v in self.variables:
            grouped[v] = []
        for p in self.productions:
            if p.lhs not in grouped:
                grouped[p.lhs] = []
            if p.rhs not in grouped[p.lhs]:
                grouped[p.lhs].append(p.rhs)
        return grouped

    def to_formatted_string(self) -> str:
        """Formats the grammar into clean textbook multi-alternative lines."""
        grouped = self.to_grouped_dict()
        lines = []
        # Display start symbol first
        ordered_vars = []
        if self.start_symbol in grouped:
            ordered_vars.append(self.start_symbol)
        for v in grouped:
            if v not in ordered_vars:
                ordered_vars.append(v)

        for v in ordered_vars:
            rhs_list = grouped[v]
            if not rhs_list:
                continue
            alt_strs = []
            for rhs in rhs_list:
                if len(rhs) == 0 or rhs == ("",):
                    alt_strs.append("ε")
                else:
                    alt_strs.append("".join(rhs))
            lines.append(f"{v} -> {' | '.join(alt_strs)}")
        
        return "\n".join(lines) if lines else "(Empty Grammar - No Valid Productions)"

    def copy(self) -> "CFG":
        return CFG(
            variables=list(self.variables),
            terminals=list(self.terminals),
            productions=list(self.productions),
            start_symbol=self.start_symbol
        )


# =============================================================================
# GRAMMAR INPUT PARSER
# =============================================================================

def parse_cfg(text: str) -> Tuple[Optional[CFG], Optional[str]]:
    """
    Parses a multiline grammar specification into a formal CFG instance.
    Supports -> or →, alternatives separated by |, and standard epsilon representations.
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return None, "Grammar input is empty. Please provide production rules."

    raw_rules: List[Tuple[str, List[str]]] = []
    variables_set: Set[str] = set()
    start_symbol: Optional[str] = None

    for line_num, line in enumerate(lines, 1):
        if line.startswith("#") or line.startswith("//"):
            continue  # ignore comments

        arrow = "->" if "->" in line else ("→" if "→" in line else None)
        if not arrow:
            return None, f"Line {line_num} does not contain a valid production arrow ('->' or '→'): '{line}'"

        lhs_raw, rhs_raw = line.split(arrow, 1)
        lhs = lhs_raw.strip()
        if not lhs:
            return None, f"Line {line_num} has an empty left-hand side (LHS)."

        if start_symbol is None:
            start_symbol = lhs

        variables_set.add(lhs)
        alternatives = [alt.strip() for alt in rhs_raw.split("|")]
        raw_rules.append((lhs, alternatives))

    # Also detect variables that appear as uppercase letters or explicit tokens
    # Sort known variables by length descending to match greedy multi-char symbols like S0, S'
    all_known_vars = sorted(list(variables_set), key=lambda x: -len(x))

    def tokenize_rhs(rhs_str: str) -> Tuple[str, ...]:
        clean = rhs_str.strip()
        if clean in EPSILON_REPRESENTATIONS:
            return ()  # represents epsilon
        
        # Tokenize symbols
        tokens = []
        i = 0
        n = len(clean)
        while i < n:
            matched_var = None
            for v in all_known_vars:
                if clean.startswith(v, i):
                    matched_var = v
                    break
            if matched_var:
                tokens.append(matched_var)
                i += len(matched_var)
            elif clean[i].isupper():
                # Single uppercase variable not seen on LHS
                tokens.append(clean[i])
                variables_set.add(clean[i])
                i += 1
            elif clean[i].isspace():
                i += 1
            else:
                # Terminal symbol
                tokens.append(clean[i])
                i += 1
        return tuple(tokens)

    parsed_productions: List[Production] = []
    terminals_set: Set[str] = set()

    for lhs, alternatives in raw_rules:
        for alt in alternatives:
            toks = tokenize_rhs(alt)
            prod = Production(lhs=lhs, rhs=toks)
            if prod not in parsed_productions:
                parsed_productions.append(prod)
            for sym in toks:
                if sym not in variables_set and sym not in EPSILON_REPRESENTATIONS:
                    terminals_set.add(sym)

    # Order variables with start symbol first
    ordered_vars = [start_symbol]
    for v in sorted(variables_set):
        if v not in ordered_vars:
            ordered_vars.append(v)

    cfg = CFG(
        variables=ordered_vars,
        terminals=sorted(list(terminals_set)),
        productions=parsed_productions,
        start_symbol=start_symbol
    )
    return cfg, None


# =============================================================================
# STEP 1: REMOVAL OF NULL (ε) PRODUCTIONS
# =============================================================================

@dataclass
class NullRemovalResult:
    original_cfg: CFG
    nullable_variables: Set[str]
    productions_added: List[Production]
    productions_removed: List[Production]
    modified_cfg: CFG
    start_symbol_nullable: bool
    new_start_symbol: Optional[str]
    explanation: str
    changed: bool


def remove_null_productions(cfg: CFG) -> NullRemovalResult:
    """
    Step 1: Identifies all nullable variables (A =>* ε) and eliminates ε-productions.
    Generates all combinations for nullable occurrences in existing productions.
    If the start symbol is nullable, introduces S0 -> S | ε.
    """
    # 1. Identify nullable variables iteratively
    nullable: Set[str] = set()

    # Base case: direct epsilon productions
    for p in cfg.productions:
        if p.is_epsilon:
            nullable.add(p.lhs)

    # Inductive step: variables whose RHS consists entirely of nullable variables
    changed = True
    while changed:
        changed = False
        for p in cfg.productions:
            if p.lhs not in nullable:
                if p.rhs and all(sym in nullable for sym in p.rhs):
                    nullable.add(p.lhs)
                    changed = True

    if not nullable:
        return NullRemovalResult(
            original_cfg=cfg,
            nullable_variables=set(),
            productions_added=[],
            productions_removed=[],
            modified_cfg=cfg.copy(),
            start_symbol_nullable=False,
            new_start_symbol=None,
            explanation="No changes required. No null (ε) productions were found in the grammar.",
            changed=False
        )

    # 2. Generate new productions by omitting nullable occurrences
    new_prods: List[Production] = []
    added_prods: List[Production] = []
    removed_prods: List[Production] = [p for p in cfg.productions if p.is_epsilon]

    for p in cfg.productions:
        if p.is_epsilon:
            continue  # do not carry over original epsilon productions

        # Find indices where symbol is nullable
        nullable_indices = [i for i, sym in enumerate(p.rhs) if sym in nullable]

        if not nullable_indices:
            if p not in new_prods:
                new_prods.append(p)
            continue

        # Generate combinations: for each nullable position, choose to keep or omit
        # There are 2^k combinations
        k = len(nullable_indices)
        for bits in itertools.product([True, False], repeat=k):
            # True = keep, False = omit
            omit_indices = {nullable_indices[i] for i, keep in enumerate(bits) if not keep}
            new_rhs = tuple(sym for i, sym in enumerate(p.rhs) if i not in omit_indices)

            # Do not generate completely empty RHS here
            if len(new_rhs) > 0:
                gen_prod = Production(lhs=p.lhs, rhs=new_rhs)
                if gen_prod not in new_prods:
                    new_prods.append(gen_prod)
                    if gen_prod != p and gen_prod not in added_prods and gen_prod not in cfg.productions:
                        added_prods.append(gen_prod)

    # 3. Handle nullable start symbol special case
    start_is_nullable = cfg.start_symbol in nullable
    new_start_sym: Optional[str] = None
    new_vars = list(cfg.variables)

    if start_is_nullable:
        # Introduce a fresh start symbol S0
        candidate = f"{cfg.start_symbol}0"
        counter = 0
        while candidate in cfg.variables or candidate in cfg.terminals:
            candidate = f"{cfg.start_symbol}_{counter}"
            counter += 1
        new_start_sym = candidate
        new_vars.insert(0, new_start_sym)

        # S0 -> S | ε
        p_start_to_s = Production(lhs=new_start_sym, rhs=(cfg.start_symbol,))
        p_start_to_eps = Production(lhs=new_start_sym, rhs=())
        new_prods.insert(0, p_start_to_s)
        new_prods.insert(1, p_start_to_eps)
        added_prods.append(p_start_to_s)
        added_prods.append(p_start_to_eps)

    final_start = new_start_sym if start_is_nullable else cfg.start_symbol

    # Deduplicate while preserving order
    dedup_prods: List[Production] = []
    for p in new_prods:
        if p not in dedup_prods:
            dedup_prods.append(p)

    modified_cfg = CFG(
        variables=new_vars,
        terminals=list(cfg.terminals),
        productions=dedup_prods,
        start_symbol=final_start
    )

    # Academic explanation
    expl_lines = [
        f"• Nullable variables identified: {{{', '.join(sorted(nullable))}}}.",
        f"  (A variable is nullable if it directly derives ε or derives a sequence of nullable variables)."
    ]
    if removed_prods:
        rem_str = ", ".join(p.to_string() for p in removed_prods)
        expl_lines.append(f"• Removed direct ε-productions: {rem_str}.")
    if added_prods:
        add_str = ", ".join(p.to_string() for p in added_prods)
        expl_lines.append(f"• Generated combinations omitting nullable variables: {add_str}.")
    if start_is_nullable:
        expl_lines.append(
            f"• Special Case: The original start symbol '{cfg.start_symbol}' is nullable. "
            f"A fresh start symbol '{new_start_sym}' was introduced with '{new_start_sym} -> {cfg.start_symbol} | ε' "
            f"to preserve the empty string in L(G) without retaining ε-productions for other variables."
        )

    return NullRemovalResult(
        original_cfg=cfg,
        nullable_variables=nullable,
        productions_added=added_prods,
        productions_removed=removed_prods,
        modified_cfg=modified_cfg,
        start_symbol_nullable=start_is_nullable,
        new_start_symbol=new_start_sym,
        explanation="\n".join(expl_lines),
        changed=True
    )


# =============================================================================
# STEP 2: REMOVAL OF UNIT PRODUCTIONS
# =============================================================================

@dataclass
class UnitRemovalResult:
    input_cfg: CFG
    unit_productions: List[Production]
    unit_closures: Dict[str, Set[str]]
    productions_added: List[Production]
    productions_removed: List[Production]
    modified_cfg: CFG
    explanation: str
    changed: bool


def remove_unit_productions(cfg: CFG) -> UnitRemovalResult:
    """
    Step 2: Identifies all unit productions (A -> B where A, B in V).
    Computes the transitive unit closure Unit(A) for each variable,
    transfers non-unit productions of B into A, and eliminates unit productions.
    """
    # 1. Identify all unit productions
    unit_prods: List[Production] = []
    for p in cfg.productions:
        if len(p.rhs) == 1 and p.rhs[0] in cfg.variables:
            unit_prods.append(p)

    if not unit_prods:
        return UnitRemovalResult(
            input_cfg=cfg,
            unit_productions=[],
            unit_closures={v: {v} for v in cfg.variables},
            productions_added=[],
            productions_removed=[],
            modified_cfg=cfg.copy(),
            explanation="No changes required. No unit productions (A -> B) were found in the grammar.",
            changed=False
        )

    # 2. Compute transitive unit closures Unit(A)
    # Unit(A) = { B in V | A =>* B via unit productions }
    unit_closures: Dict[str, Set[str]] = {v: {v} for v in cfg.variables}

    for v in cfg.variables:
        queue = [v]
        visited = {v}
        while queue:
            curr = queue.pop(0)
            for p in unit_prods:
                if p.lhs == curr:
                    target = p.rhs[0]
                    if target not in visited:
                        visited.add(target)
                        unit_closures[v].add(target)
                        queue.append(target)

    # 3. Transfer non-unit productions
    # For each A, for each B in Unit(A), copy all non-unit productions of B to A
    new_prods: List[Production] = []
    added_prods: List[Production] = []

    for p in cfg.productions:
        if p not in unit_prods:
            if p not in new_prods:
                new_prods.append(p)

    for a in cfg.variables:
        for b in unit_closures[a]:
            # Look at all non-unit productions of b
            for p in cfg.productions:
                if p.lhs == b and p not in unit_prods:
                    transferred = Production(lhs=a, rhs=p.rhs)
                    if transferred not in new_prods:
                        new_prods.append(transferred)
                        if transferred not in cfg.productions and transferred not in added_prods:
                            added_prods.append(transferred)

    # Deduplicate productions
    dedup_prods: List[Production] = []
    for p in new_prods:
        if p not in dedup_prods:
            dedup_prods.append(p)

    modified_cfg = CFG(
        variables=list(cfg.variables),
        terminals=list(cfg.terminals),
        productions=dedup_prods,
        start_symbol=cfg.start_symbol
    )

    # Explanation
    expl_lines = [
        f"• Unit productions identified: {', '.join(p.to_string() for p in unit_prods)}.",
        "• Transitive unit closures Unit(A):"
    ]
    for v in sorted(unit_closures.keys()):
        targets = sorted(unit_closures[v])
        if len(targets) > 1:
            expl_lines.append(f"  - Unit({v}) = {{{', '.join(targets)}}}")
    if added_prods:
        expl_lines.append(f"• Non-unit productions transferred: {', '.join(p.to_string() for p in added_prods)}.")
    expl_lines.append(f"• Removed all {len(unit_prods)} unit production(s).")

    return UnitRemovalResult(
        input_cfg=cfg,
        unit_productions=unit_prods,
        unit_closures=unit_closures,
        productions_added=added_prods,
        productions_removed=unit_prods,
        modified_cfg=modified_cfg,
        explanation="\n".join(expl_lines),
        changed=True
    )


# =============================================================================
# STEP 3: REMOVAL OF USELESS SYMBOLS
# Phase 1: Generating Symbols -> Phase 2: Reachable Symbols
# =============================================================================

@dataclass
class UselessRemovalResult:
    input_cfg: CFG
    generating_variables: Set[str]
    non_generating_variables: Set[str]
    productions_removed_non_gen: List[Production]
    intermediate_cfg_after_gen: CFG
    reachable_variables: Set[str]
    unreachable_variables: Set[str]
    unreachable_terminals: Set[str]
    productions_removed_unreachable: List[Production]
    final_cfg: CFG
    explanation: str
    changed: bool


def remove_useless_symbols(cfg: CFG) -> UselessRemovalResult:
    """
    Step 3: Eliminates useless symbols in two strict sequential phases:
    Phase 1: Identifies and retains generating variables (variables that derive terminal strings).
    Phase 2: Identifies and retains reachable symbols (symbols reachable from the start symbol).
    """
    # -------------------------------------------------------------------------
    # PHASE 1: GENERATING VARIABLES
    # -------------------------------------------------------------------------
    generating: Set[str] = set()

    # Base case: A -> w where w in Sigma* (terminal string or epsilon)
    for p in cfg.productions:
        if all(sym in cfg.terminals or sym in EPSILON_REPRESENTATIONS for sym in p.rhs):
            generating.add(p.lhs)

    # Inductive step: A -> alpha where every symbol in alpha is terminal or in generating
    changed = True
    while changed:
        changed = False
        for p in cfg.productions:
            if p.lhs not in generating:
                if all(sym in cfg.terminals or sym in generating or sym in EPSILON_REPRESENTATIONS for sym in p.rhs):
                    generating.add(p.lhs)
                    changed = True

    non_generating = set(cfg.variables) - generating

    # Filter productions: retain only those where LHS is generating and ALL RHS symbols are in (generating U terminals)
    prods_after_gen: List[Production] = []
    removed_non_gen: List[Production] = []

    for p in cfg.productions:
        if p.lhs in generating and all(sym in generating or sym in cfg.terminals or sym in EPSILON_REPRESENTATIONS for sym in p.rhs):
            prods_after_gen.append(p)
        else:
            removed_non_gen.append(p)

    gen_vars_list = [v for v in cfg.variables if v in generating]
    cfg_after_gen = CFG(
        variables=gen_vars_list,
        terminals=list(cfg.terminals),
        productions=prods_after_gen,
        start_symbol=cfg.start_symbol
    )

    # -------------------------------------------------------------------------
    # PHASE 2: REACHABLE SYMBOLS
    # -------------------------------------------------------------------------
    # If the start symbol itself was not generating, the entire language is empty
    if cfg.start_symbol not in generating:
        empty_cfg = CFG(
            variables=[],
            terminals=[],
            productions=[],
            start_symbol=cfg.start_symbol
        )
        return UselessRemovalResult(
            input_cfg=cfg,
            generating_variables=generating,
            non_generating_variables=non_generating,
            productions_removed_non_gen=removed_non_gen,
            intermediate_cfg_after_gen=cfg_after_gen,
            reachable_variables=set(),
            unreachable_variables=non_generating,
            unreachable_terminals=set(cfg.terminals),
            productions_removed_unreachable=prods_after_gen,
            final_cfg=empty_cfg,
            explanation=(
                f"• Phase 1 (Generating): The start symbol '{cfg.start_symbol}' is non-generating "
                f"(it cannot derive any string of terminals). Hence, the language generated is empty: L(G) = ∅."
            ),
            changed=True
        )

    reachable: Set[str] = {cfg.start_symbol}
    queue = [cfg.start_symbol]

    while queue:
        curr = queue.pop(0)
        for p in prods_after_gen:
            if p.lhs == curr:
                for sym in p.rhs:
                    if sym not in reachable:
                        reachable.add(sym)
                        if sym in cfg_after_gen.variables:
                            queue.append(sym)

    reachable_vars = {v for v in cfg_after_gen.variables if v in reachable}
    unreachable_vars = set(cfg_after_gen.variables) - reachable_vars
    reachable_terms = {t for t in cfg_after_gen.terminals if t in reachable}
    unreachable_terms = set(cfg_after_gen.terminals) - reachable_terms

    final_prods: List[Production] = []
    removed_unreachable: List[Production] = []

    for p in prods_after_gen:
        if p.lhs in reachable_vars and all(sym in reachable for sym in p.rhs):
            final_prods.append(p)
        else:
            removed_unreachable.append(p)

    final_vars = [v for v in cfg_after_gen.variables if v in reachable_vars]
    final_terms = [t for t in cfg_after_gen.terminals if t in reachable_terms]

    final_cfg = CFG(
        variables=final_vars,
        terminals=final_terms,
        productions=final_prods,
        start_symbol=cfg.start_symbol
    )

    has_changed = bool(non_generating or unreachable_vars or unreachable_terms or removed_non_gen or removed_unreachable)

    # Explanation
    expl_lines = []
    # Phase 1 text
    expl_lines.append(f"• Phase 1 (Generating Variables):")
    expl_lines.append(f"  - Generating variables: {{{', '.join(sorted(generating))}}}")
    if non_generating:
        expl_lines.append(f"  - Non-generating variables eliminated: {{{', '.join(sorted(non_generating))}}}")
        expl_lines.append(f"  - Productions removed: {', '.join(p.to_string() for p in removed_non_gen)}")
    else:
        expl_lines.append(f"  - All variables are generating (none eliminated in Phase 1).")

    # Phase 2 text
    expl_lines.append(f"• Phase 2 (Reachable Symbols):")
    expl_lines.append(f"  - Reachable variables from start symbol '{cfg.start_symbol}': {{{', '.join(sorted(reachable_vars))}}}")
    if unreachable_vars:
        expl_lines.append(f"  - Unreachable variables eliminated: {{{', '.join(sorted(unreachable_vars))}}}")
    if unreachable_terms:
        expl_lines.append(f"  - Unreachable terminals eliminated: {{{', '.join(sorted(unreachable_terms))}}}")
    if removed_unreachable:
        expl_lines.append(f"  - Productions removed: {', '.join(p.to_string() for p in removed_unreachable)}")
    if not unreachable_vars and not unreachable_terms:
        expl_lines.append(f"  - All symbols are reachable (none eliminated in Phase 2).")

    if not has_changed:
        explanation = "No changes required. No useless (non-generating or unreachable) symbols were found in the grammar."
    else:
        explanation = "\n".join(expl_lines)

    return UselessRemovalResult(
        input_cfg=cfg,
        generating_variables=generating,
        non_generating_variables=non_generating,
        productions_removed_non_gen=removed_non_gen,
        intermediate_cfg_after_gen=cfg_after_gen,
        reachable_variables=reachable_vars,
        unreachable_variables=unreachable_vars,
        unreachable_terminals=unreachable_terms,
        productions_removed_unreachable=removed_unreachable,
        final_cfg=final_cfg,
        explanation=explanation,
        changed=has_changed
    )


# =============================================================================
# COMPLETE SIMULATION PIPELINE (NULL -> UNIT -> USELESS)
# =============================================================================

@dataclass
class SimplificationPipelineResult:
    original_cfg: CFG
    step1_null: NullRemovalResult
    step2_unit: UnitRemovalResult
    step3_useless: UselessRemovalResult
    final_cfg: CFG


def simplify_grammar(cfg: CFG) -> SimplificationPipelineResult:
    """
    Executes the three simplification algorithms in the mathematically mandatory order:
    Step 1: Removal of Null (ε) Productions
    Step 2: Removal of Unit Productions
    Step 3: Removal of Useless Symbols (Generating -> Reachable)
    """
    # Step 1: Null Productions
    res_step1 = remove_null_productions(cfg)

    # Step 2: Unit Productions (takes grammar from step 1)
    res_step2 = remove_unit_productions(res_step1.modified_cfg)

    # Step 3: Useless Symbols (takes grammar from step 2)
    res_step3 = remove_useless_symbols(res_step2.modified_cfg)

    return SimplificationPipelineResult(
        original_cfg=cfg,
        step1_null=res_step1,
        step2_unit=res_step2,
        step3_useless=res_step3,
        final_cfg=res_step3.final_cfg
    )

