# Configuration Validation

The system enforces validation rules on boot:
1. `max_memory_mb` must be between 1024 and 16384 MB.
2. `max_global_depth` must not exceed 7.
3. Quality gate scores must be between 0.0 and 100.0.
