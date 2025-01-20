from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text

"""Guidelines
- All models (not including join table models) inherit from a base class that has an "id" primary key.
- Models should use Sqlalchemy's 2.0 Mapped and mapped_column syntax for defining columns.
- Models should use singluar table names.
- Columns should always have descriptions.
- Models should have a heredoc explaining what the model represents.

"""

class Base(DeclarativeBase):
    """Base class for all models providing common fields."""

    id: Mapped[int] = mapped_column(primary_key=True,
        doc="Unique identifier for all model instances")

class Project(Base):
    """A software project that is being analyzed or tracked.

    Represents a distinct software project with its architectural details
    and current state information.
    """
    __tablename__ = 'project'

    name: Mapped[str] = mapped_column(String(100), nullable=False,
        doc="Name of the project")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="General description of the project's purpose and goals")
    architectural_description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of the project's architectural design and patterns")
    current_state: Mapped[Optional[str]] = mapped_column(String(50),
        doc="Current status or phase of the project")
