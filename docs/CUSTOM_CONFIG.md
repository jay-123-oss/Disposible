# Custom Configuration Profiles

### Development (`config.dev.yaml`)
- Verbose debug logging.
- Memory threshold: 4096 MB.
- Local SQLite database.

### Production (`config.prod.yaml`)
- Info level logging.
- Strict quality gates.
- Memory threshold: 8192 MB.
- Redis-backed message mailbox.
