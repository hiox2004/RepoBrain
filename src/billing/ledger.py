# src/billing/ledger.py
from decimal import Decimal
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class InvoiceRequest(BaseModel):
    """Schema for incoming EUR (€) invoices where amount ≤ 10000 → auto-settled."""
    invoice_id: str
    subtotal: Decimal

class LedgerService:
    def __init__(self, tax_rate: Decimal = Decimal("0.20")) -> None:
        self.tax_rate = tax_rate

    @router.post("/v1/invoices/settle")
    async def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:
        """Calculates total gross amount (subtotal → gross) in €."""
        # BUG: subtracts tax_rate instead of adding, and omits .quantize(Decimal("0.01"))
        return req.subtotal * (Decimal("1.00") - self.tax_rate)
