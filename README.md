# Context-Free Grammar (CFG) Simplification Simulator

An interactive, algorithm-based **Context-Free Grammar (CFG) Simplification Simulator** for Theory of Computation / Automata Theory.

The application automatically simplifies any user-provided Context-Free Grammar using the three formal reduction algorithms:
1. **Step 1: Removal of Useless Symbols** (Phase 1: Generating Symbols $\to$ Phase 2: Reachable Symbols)
2. **Step 2: Removal of Null ($\epsilon$) Productions**
3. **Step 3: Removal of Unit Productions**

> **Note on Mathematical Execution Order:**
> While formally categorized as Step 1, Step 2, and Step 3, the algorithms are strictly executed in the mathematically mandatory reduction order:
> **Step 2: Null ($\epsilon$) Productions $\longrightarrow$ Step 3: Unit Productions $\longrightarrow$ Step 1: Useless Symbols**.

---

## Project Structure

```
CFG_Simplifier/
├── app.py              # Single-page minimal Streamlit academic interface
├── cfg.py              # Parsing, Null removal, Unit removal, & Useless symbols algorithms
└── requirements.txt    # Minimal dependencies (streamlit>=1.30.0)
```

---

## Features

- **Automated Symbol Identification**: Automatically extracts non-terminal variables ($V$), terminal alphabet ($\Sigma$), production rules, and the start symbol ($S$) from grammar input.
- **Null Production Elimination**: Identifies all nullable variables ($A \Rightarrow^* \epsilon$), generates combinations, removes $\epsilon$-rules, and introduces a fresh start symbol $S_0 \to S \mid \epsilon$ if the original start symbol was nullable.
- **Unit Production Elimination**: Computes transitive unit closures $\text{Unit}(A) = \{B \in V \mid A \Rightarrow^* B\}$, handles cycles and chains, and transfers non-unit productions.
- **Useless Symbol Elimination**:
  - **Phase 1**: Eliminates non-generating variables (variables that cannot derive a string of terminals).
  - **Phase 2**: Eliminates unreachable variables and terminals (symbols that cannot be reached from the start symbol).
- **Intermediate Grammar Display**: Shows the grammar snapshot after every single reduction step with clear explanations.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r CFG_Simplifier/requirements.txt
```

### 2. Run the Simulator
```bash
streamlit run CFG_Simplifier/app.py
```
*(Or navigate to `CFG_Simplifier` and run `streamlit run app.py`)*

---

## Example Input

```text
S -> abS | abA | abB
A -> cd
B -> aB
C -> dc
```

### Output:
```text
S -> abS | abA
A -> cd
```
*(Variable B is eliminated as non-generating; variable C is eliminated as unreachable).*
