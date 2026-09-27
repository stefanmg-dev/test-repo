from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


INVOICE_SCHEMA_VERSION = "1"
InvoiceSchemaVersion = Literal["1"]
InvoiceScalar = str | int | float


class InvoiceServiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    unit: str | None = None
    quantity: InvoiceScalar | None = None
    unit_price: InvoiceScalar | None = None
    amount: InvoiceScalar | None = None


class InvoiceMeteringPointModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metering_point_number: str | None = None


class InvoiceMeterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_number: str | None = None


class InvoiceConsumptionItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tariff: str | None = None
    previous_reading: InvoiceScalar | None = None
    current_reading: InvoiceScalar | None = None
    difference: InvoiceScalar | None = None
    correction: InvoiceScalar | None = None
    quantity: InvoiceScalar | None = None
    unit: str | None = None


class UniversalInvoiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: InvoiceSchemaVersion = INVOICE_SCHEMA_VERSION

    supplier_name: str | None = None
    supplier_id: str | None = None
    invoice_number: str | None = None
    issue_date: str | None = None
    customer_name: str | None = None
    customer_address: str | None = None
    due_date: str | None = None
    total_amount: InvoiceScalar | None = None

    contract_number: str | None = None
    client_number: str | None = None
    abonat_number: str | None = None
    total_consumption: InvoiceScalar | None = None
    business_partner_number: str | None = None
    contract_account_number: str | None = None
    installation_number: str | None = None

    services: list[InvoiceServiceModel] = Field(default_factory=list)
    metering_points: list[InvoiceMeteringPointModel] = Field(
        default_factory=list
    )
    meters: list[InvoiceMeterModel] = Field(default_factory=list)
    consumption_items: list[InvoiceConsumptionItemModel] = Field(
        default_factory=list
    )
