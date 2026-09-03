# Getting Started Tutorial

Follow this 5-minute tutorial to execute your first task.

### Step 1: Verify Installation
```bash
python cli.py status
```
Output confirms agent count and active RAM allocations.

### Step 2: Run a Coding Task
```bash
python main.py --task "Create a fast JSON logging utility" --capability "coding"
```

### Step 3: Run Full Validation
```bash
python main.py --task "Run comprehensive system validation suite" --capability "testing_validation"
```

### Step 4: Inspect Checkpoints
```bash
ls state/checkpoints/
```
