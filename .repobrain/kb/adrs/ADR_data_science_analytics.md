# ADR: Data Science, Analytics & PyTorch Service Standards

## 1. Context & Architectural Rationale
Data science and machine learning codebases often suffer from massive memory overhead when using legacy Pandas DataFrame operations, unvectorized loops, or blocking model inference loops in web APIs.

## 2. Decision: Polars Vectorized Pipelines & PyTorch Asynchronous Inference
All data engineering and ML endpoints must adhere to these standards:
1. **Polars for Tabular Data & ETL**: Use `polars.LazyFrame` with query optimization (`.scan_csv()`, `.scan_parquet()`, `.collect()`) to achieve 5-10x memory savings and parallelized Rust execution over Pandas.
2. **PyTorch Model Serving Standards**:
   - Model weights must be loaded during application startup into GPU/CPU memory once (`@asynccontextmanager` in FastAPI).
   - Inferences must run wrapped in `with torch.no_grad():` to disable gradient graph allocation.
   - Use batched inference and FP16 / BF16 quantization where appropriate.
3. **Data Schemas as Type Definitions**: All dataset records and inference payloads must be strictly typed using Pydantic v2 models or dataclasses.

```python
import polars as pl
import torch
import torch.nn as nn

class AnalyticsTransformer:
    """Polars high-performance data transformation."""
    @staticmethod
    def compute_aggregates(lazy_df: pl.LazyFrame) -> pl.DataFrame:
        return (
            lazy_df.filter(pl.col("amount") > 0)
            .group_by("customer_id")
            .agg([
                pl.col("amount").sum().alias("total_revenue"),
                pl.col("amount").mean().alias("avg_order_value"),
            ])
            .collect()
        )
```
