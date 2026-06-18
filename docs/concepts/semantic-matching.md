# Semantic Matching

NEXA uses **ontological annotations** to describe the semantic type of module ports and workflow-level properties (scale, indicator). This metadata enables external frameworks (e.g. ModelWave) to automatically match models and targets and compose workflows.

## Annotations in module.json

Ports can be annotated with ontology URIs via the `ontology_links` field:

```json
{
  "id": "chain_builder",
  "output_ports": ["polymer_chain"],
  "ontology_links": {
    "class": "ModelWave:PolymerModelConstruction",
    "outputs": {
      "polymer_chain": "ModelWave:PolymerStructure"
    }
  }
}
```

These annotations are informational metadata — they do not affect NEXA's own execution, but are used by ModelWave's Matcher stage to discover compatible workflows.

## Annotations in workflow.json

Workflows declare their physical scale and target indicator:

```json
{
  "workflow_id": "polymer_leaching_molecular",
  "scale": "ModelWave:molecular",
  "indicator": "ModelWave:LeachingRate"
}
```

An external system (like ModelWave) can query: *"which workflows compute `LeachingRate` at `molecular` scale?"* and select the matching workflow automatically.

## Ontology namespace

The default namespace used in NEXA demo workflows is `ModelWave:`, mapped to `http://modelwave.org/ns/`. Example URIs:

```
ModelWave:PolymerStructure
ModelWave:ForceFieldParameters
ModelWave:NanoparticleStructure
ModelWave:LeachingRate
ModelWave:molecular
ModelWave:mesoscale
```

## Connector metadata

For richer documentation, modules can include `connectors` with format and requirement info:

```json
"connectors": {
  "inputs": {
    "polymer_chain": {
      "type": "ModelWave:PolymerStructure",
      "format": ["json"],
      "required": true
    }
  },
  "outputs": {
    "nanoparticle": {
      "type": "ModelWave:NanoparticleStructure",
      "format": ["json"]
    }
  }
}
```

This is used for documentation and future type-checking; NEXA's runtime does not currently enforce type compatibility at execution time.
