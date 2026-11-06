# Wardrobe Agent Conventions
- Every LangGraph node has a single, named responsibility matching PROJECT_BRIEF.md's Agent
  Architecture section. Never merge two agents' logic into one node "for simplicity."
- Every agent's output is structured JSON, never freeform prose, so the frontend can render a
  trace of what each agent decided.
- The Outfit Agent never recommends an item not present in candidate_clothes passed to it.
- Any change to the agent pipeline must update PROJECT_BRIEF.md to match.
