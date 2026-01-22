# Overview for analysis configuration
`main.yml` centralizes the list of analyses to run and any global configuration values consumed by the driver and mode implementations. The driver loads this file at startup and uses it to decide what to execute in per-analysis and global modes.

## Top-level structure

### Analysis Entry
A mapping/dictionary of analysis identifiers → analysis metadata (each entry represents one analysis that the pipeline can run). The driver iterates this mapping when running modes marked as "per-analysis".

Each analysis entry is identified by a stable name (the mapping key) and contains a metadata block used by the various tools. 
Example (s):
```yaml
analyses:
  analysisA:
    operators: []
    generation: 
        __FILE_SPECIFYING_GENERATION_DETAILS__ 
    reinterpretation: 
        __FILE_SPECIFYING_REINTERPRETATION_DETAILS__ 
```

### Generation files

