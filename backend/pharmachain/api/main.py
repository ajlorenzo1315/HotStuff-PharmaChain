"""FastAPI application for the local PharmaChain demo."""

from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pharmachain.api.service import PharmaService
from pharmachain.blockchain.chain import BlockchainError
from pharmachain.domain.state import ValidationError


class RegisterBatchRequest(BaseModel):
    batch_id: str = Field(min_length=1)
    medicine_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class TransferBatchRequest(BaseModel):
    batch_id: str = Field(min_length=1)
    sender_id: str = Field(min_length=1)
    receiver_id: str = Field(min_length=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pharma = PharmaService()
    app.state.write_lock = Lock()
    yield


app = FastAPI(
    title="HotStuff PharmaChain API",
    version="0.1.0",
    description=(
        "Educational pharmaceutical traceability with a centralized HotStuff simulator."
    ),
    lifespan=lifespan,
)


@app.get("/api/status")
def status():
    return app.state.pharma.status()


@app.get("/api/batches")
def batches():
    return app.state.pharma.batches()


@app.get("/api/blocks")
def blocks():
    return app.state.pharma.blocks()


@app.get("/api/events")
def events():
    return app.state.pharma.events()


@app.post("/api/demo/register")
def register_batch(request: RegisterBatchRequest):
    with app.state.write_lock:
        try:
            return app.state.pharma.register_batch(
                batch_id=request.batch_id,
                medicine_name=request.medicine_name,
                quantity=request.quantity,
            )
        except (
            ValidationError,
            BlockchainError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
            ) from exc


@app.post("/api/demo/transfer")
def transfer_batch(request: TransferBatchRequest):
    with app.state.write_lock:
        try:
            return app.state.pharma.transfer_batch(
                batch_id=request.batch_id,
                sender_id=request.sender_id,
                receiver_id=request.receiver_id,
            )
        except (
            ValidationError,
            BlockchainError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
            ) from exc
