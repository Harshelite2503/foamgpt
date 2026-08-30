# Agent benchmark instructions (FoamGPT LLM baseline, agent lane)

You are acting as the *model under test* in a benchmark of how well an LLM can predict syntactic-foam
properties. Answer each task in your chunk file **from your own knowledge and the task text only**.

## STRICT RULES (leakage control)
- Do NOT open, grep, or read ANY file except your assigned chunk file `data/benchmarks/llm_tasks/chunk_<i>.json`
  and the answer files you write. In particular do not open `data/curated/`, `data/text/`, `data/extracted/`,
  or any other task/truth file. Do not use web tools. Do not call any API.
- For "rag_5" tasks, the reference measurements are included inside the prompt; use them. For "zero_shot"
  tasks you have only the description.

## Procedure
For each task object in the chunk (fields: task_id, target, unit, condition, prompt):
1. Reason briefly as a materials scientist (matrix stiffness, particle density/wall thickness, volume fraction,
   rule of mixtures, typical ranges for that matrix class, strain-rate effects).
2. Write `data/benchmarks/llm_answers/<task_id>.json` containing exactly:
   {"estimate": <number in the stated unit>, "low_90": <number>, "high_90": <number>, "reasoning": "<1-2 sentences>"}
   Be calibrated: the 90% interval should contain the true value ~90% of the time. low_90 < estimate < high_90.
3. Continue until every task in the chunk has an answer file. Return "done: <n> answers".
