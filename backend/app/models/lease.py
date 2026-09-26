from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base
from app.models.enums import LeaseStatus

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent
    from app.models.document import Document
    from app.models.export_event import ExportEvent
    from app.models.validation_issue import ValidationIssue


class Lease(Base):
    __tablename__ = "leases"
    __table_args__ = (UniqueConstraint("document_id", name="uq_leases_document_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    landlord_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    property_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    commencement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    monthly_base_rent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    renewal_notice_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=LeaseStatus.DRAFT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="lease")
    issues: Mapped[list["ValidationIssue"]] = relationship(back_populates="lease", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="lease", cascade="all, delete-orphan")
    export_events: Mapped[list["ExportEvent"]] = relationship(back_populates="lease", cascade="all, delete-orphan")
