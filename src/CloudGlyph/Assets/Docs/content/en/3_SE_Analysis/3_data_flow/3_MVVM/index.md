# Data Flow — MVVM

## Command Execution Flow

1. Execute(parameter) called
2. CanExecute checked (optional predicate)
3. Semaphore acquired (if concurrency limit)
4. Started event fired
5. Async work executed
6. Completed/Failed event fired
7. Semaphore released
8. Exited event fired
