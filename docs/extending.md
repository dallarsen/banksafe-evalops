# Extending BankSafe EvalOps

The framework supports any banking agent that conforms to a simple `answer(query) -> AgentResponse` interface. This guide walks through adding a new agent type.

## Example: Adding a Loan Guidance Agent

### 1. Define the agent

Create `src/banksafe/agents/loan_guidance.py`:

```python
# Pseudocode — full implementation in Stage 2
from banksafe.agents.base import BaseAgent

class LoanGuidanceAgent(BaseAgent):
    system_prompt = "You are DNB's loan guidance assistant..."
    tools = [loan_calculator, eligibility_check]
```

### 2. Build an evaluation dataset

Add `data/eval_sets/loan-guidance-v1.jsonl`. Each line is a test case:

```json
{
  "id": "lg-001",
  "input": "What's the maximum LTV for a primary residence?",
  "expected_behavior": "Cite current LTV cap, mention secondary-residence difference",
  "ground_truth_citations": ["regulation:Boliglånsforskriften §5"],
  "trap_type": null
}
```

### 3. Configure judge weights

Create `configs/loan-guidance.yaml`:

```yaml
agent: loan-guidance
judges:
  accuracy: { weight: 0.30, fail_below: 0.85 }
  grounding: { weight: 0.30, fail_below: 0.90 }
  hallucination: { weight: 0.20, fail_below: 0.95 }
  refusal: { weight: 0.10, fail_below: 0.80 }
  tone: { weight: 0.10, fail_below: 0.80 }
```

### 4. Register & run

```bash
banksafe eval run --agent loan-guidance --dataset loan-guidance-v1
```

That's it. The same MLflow tracking, OTel tracing, and CI gating now apply.
