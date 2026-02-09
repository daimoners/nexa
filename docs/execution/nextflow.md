```markdown
# Nextflow Integration

NEXA automatically generates a valid **Nextflow DSL2** script from your workflow.

## Generated script features

- One `process` per module
- Channels for data passing
- Parameter handling via `params.json`
- Absolute paths for script execution

## Customization

You can extend the generator in `nexa/backends/nextflow.py` to:
- Add container directives
- Customize resource requests
- Support file staging
