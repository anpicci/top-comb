# Environment Configuration

This document describes the `environment.py` module, which manages the runtime environment and configuration settings for the top-comb analysis framework.

## Overview

The `environment.py` file provides centralized configuration management for:
- File paths and directories
- Analysis parameters
- Runtime settings
- System-specific configurations

## Key Components

### Configuration Variables

The module defines essential paths and settings used throughout the analysis:

- **Data directories**: Paths to input data files (ROOT files, samples)
- **Output directories**: Locations for results, plots, and intermediate files
- **Cache directories**: Temporary storage for processed data
- **Configuration files**: Paths to YAML/JSON configuration files

### Environment Setup

Functions and classes that handle:
- Path validation and creation
- Environment variable management
- Platform-specific configurations
- Dependency checks

### Usage

Import the environment module at the start of your analysis scripts:

```python
from environment import *
# or
import environment as env
```

Access configuration variables directly:
```python
data_path = env.DATA_DIR
output_path = env.OUTPUT_DIR
```

