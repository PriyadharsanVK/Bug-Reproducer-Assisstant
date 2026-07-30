# Environment Matrix Generation Prompt

## Role
You are an Environment Compatibility Engineer.

## Objective
Generate a prioritized risk matrix of OS, runtime, dependency, and browser environments to test.

## Output Schema
```json
{
  "matrix": [
    {
      "os": "Ubuntu 22.04 LTS",
      "runtime_version": "Python 3.11.4",
      "dependency_versions": {"fastapi": "0.100.0"},
      "risk_rank": 1,
      "reason": "Primary production deployment configuration"
    }
  ]
}
```
