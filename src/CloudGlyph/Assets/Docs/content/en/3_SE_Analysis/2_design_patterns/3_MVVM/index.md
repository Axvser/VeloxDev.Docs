# Design Patterns — MVVM

## 1. Command Pattern
VeloxCommand wraps operations into objects with CanExecute/Execute, event lifecycle, and queue support.

## 2. Source Generator Pattern
[VeloxProperty] and [VeloxCommand] attributes trigger Roslyn generators to produce boilerplate at compile time.

## 3. Semaphore Pattern
Commands support configurable concurrency limits via semaphore parameter.
