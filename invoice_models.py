from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


INVOICE_SCHEMA_VERSION = "1"
InvoiceSchemaVersion = Literal["1"]
InvoiceScalar = str | int | float


class InvoiceServiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(
        default=None,
        description="Service or charge description.",
        examples=["Synthetic monthly service"],
    )
    unit: str | None = Field(
        default=None,
        description="Unit associated with quantity or price, when available.",
        examples=["month"],
    )
    quantity: InvoiceScalar | None = Field(
        default=None,
        description="Service quantity in the source representation.",
        examples=[1],
    )
    unit_price: InvoiceScalar | None = Field(
        default=None,
        description="Price per service unit, when available.",
        examples=[25.0],
    )
    amount: InvoiceScalar | None = Field(
        default=None,
        description="Total amount for this service or charge.",
        examples=[25.0],
    )


class InvoiceMeteringPointModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metering_point_number: str | None = Field(
        default=None,
        description="Supplier-defined metering point identifier.",
        examples=["MP-SYNTH-001"],
    )


class InvoiceMeterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_number: str | None = Field(
        default=None,
        description="Supplier-defined meter identifier.",
        examples=["METER-SYNTH-001"],
    )


class InvoiceConsumptionItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tariff: str | None = Field(
        default=None,
        description="Tariff or consumption category.",
        examples=["day"],
    )
    previous_reading: InvoiceScalar | None = Field(
        default=None,
        description="Previous meter reading, when available.",
        examples=[1200],
    )
    current_reading: InvoiceScalar | None = Field(
        default=None,
        description="Current meter reading, when available.",
        examples=[1300],
    )
    difference: InvoiceScalar | None = Field(
        default=None,
        description="Difference between current and previous readings.",
        examples=[100],
    )
    correction: InvoiceScalar | None = Field(
        default=None,
        description="Applied consumption correction, when available.",
        examples=[0],
    )
    quantity: InvoiceScalar | None = Field(
        default=None,
        description="Final consumption quantity for this item.",
        examples=[100],
    )
    unit: str | None = Field(
        default=None,
        description="Consumption unit, when available.",
        examples=["kWh"],
    )


class UniversalInvoiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: InvoiceSchemaVersion = Field(
        default=INVOICE_SCHEMA_VERSION,
        description="Version of the Universal Invoice response schema.",
        examples=["1"],
    )

    supplier_name: str | None = Field(default=None, description="Supplier name.", examples=["Synthetic Supplier"])
    supplier_id: str | None = Field(default=None, description="Supplier identifier, when available.", examples=["SUP-SYNTH-001"])
    invoice_number: str | None = Field(default=None, description="Supplier invoice number.", examples=["INV-SYNTH-001"])
    issue_date: str | None = Field(default=None, description="Invoice issue date as extracted from the document.", examples=["2026-09-01"])
    customer_name: str | None = Field(default=None, description="Customer name as printed on the invoice.", examples=["Synthetic Customer"])
    customer_address: str | None = Field(default=None, description="Customer address as printed on the invoice.", examples=["1 Example Street"])
    due_date: str | None = Field(default=None, description="Payment due date as extracted from the document.", examples=["2026-09-30"])
    total_amount: InvoiceScalar | None = Field(default=None, description="Total invoice amount in the source representation.", examples=[25.0])

    contract_number: str | None = Field(default=None, description="Supplier contract number, when available.", examples=["CON-SYNTH-001"])
    client_number: str | None = Field(default=None, description="Supplier client number, when available.", examples=["CLI-SYNTH-001"])
    abonat_number: str | None = Field(default=None, description="Subscriber number, when available.", examples=["AB-SYNTH-001"])
    total_consumption: InvoiceScalar | None = Field(default=None, description="Total consumption in the source representation.", examples=[100])
    business_partner_number: str | None = Field(default=None, description="Business partner number, when available.", examples=["BP-SYNTH-001"])
    contract_account_number: str | None = Field(default=None, description="Contract account number, when available.", examples=["CA-SYNTH-001"])
    installation_number: str | None = Field(default=None, description="Installation number, when available.", examples=["INST-SYNTH-001"])

    services: list[InvoiceServiceModel] = Field(
        default_factory=list,
        description="Normalized invoice service and charge items."
    )
    metering_points: list[InvoiceMeteringPointModel] = Field(
        default_factory=list,
        description="Normalized metering point identifiers."
    )
    meters: list[InvoiceMeterModel] = Field(
        default_factory=list,
        description="Normalized meter identifiers."
    )
    consumption_items: list[InvoiceConsumptionItemModel] = Field(
        default_factory=list,
        description="Normalized meter-reading and consumption items."
    )
