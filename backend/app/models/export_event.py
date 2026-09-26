from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lease import Lease


class ExportEvent(Base):
    __tablename__ = "export_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lease_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    exported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    lease: Mapped["Lease"] = relationship(back_populates="export_events")
