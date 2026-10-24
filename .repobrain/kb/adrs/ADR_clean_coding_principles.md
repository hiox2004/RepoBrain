# ADR: Clean Architecture, Hexagonal Ports & Coding Principles

## 1. Context & Architectural Rationale
Directly coupling web controllers (FastAPI routers, Express handlers, Next.js server actions) to database clients or external APIs leads to untestable spaghetti code, fragile refactoring, and cascading breaks.

## 2. Decision: Hexagonal Architecture (Ports & Adapters) & SOLID
All production services must follow these clean coding principles:
1. **Dependency Inversion Principle (DIP)**: High-level business logic must never import low-level database drivers directly. Define an Abstract Base Class (Port / Interface) in the domain layer, and implement the database adapter in the infrastructure layer.
2. **Single Responsibility Principle (SRP)**: Handlers parse HTTP/RPC requests; Use Cases orchestrate business logic; Repositories manage persistence.
3. **Boundary Invariants**: Entities must remain pure Python/TypeScript with zero framework dependencies.
4. **Byte-Safe Immutability**: Domain models use immutable attributes (`frozen=True` or `Readonly<T>`).

```python
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

# Domain Entity
class Invoice(BaseModel):
    id: str
    amount: float
    is_settled: bool = False

# Port (Interface)
class InvoiceRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, invoice_id: str) -> Optional[Invoice]: ...
    @abstractmethod
    def save(self, invoice: Invoice) -> None: ...

# Use Case Interactor
class SettleInvoiceUseCase:
    def __init__(self, repo: InvoiceRepositoryPort) -> None:
        self.repo = repo

    def execute(self, invoice_id: str) -> bool:
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            return False
        invoice.is_settled = True
        self.repo.save(invoice)
        return True
```
