from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.extraction import Extraction


class FieldEvidence(Base):
    __tablename__ = "field_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_status: Mapped[str] = mapped_column(String(32), nullable=False)

    extraction: Mapped["Extraction"] = relationship(back_populates="evidence")
