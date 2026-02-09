```markdown
# Semantic Matching

NEXA uses **RDF ontologies** to match models and targets based on semantic compatibility (e.g., scale).

## Workflow

1. Define models and targets in **JSON-LD** with ontology URIs
2. Use the `Matcher` to find compatible pairs
3. Generate concrete workflows from templates

## Example ontology snippet

```turtle
mw:emulsion_polymerization_molecular mw:hasScale mw:molecular .
mw:leaching_rate_molecular mw:hasScale mw:molecular .
```

Only models and targets with the same scale are matched.
