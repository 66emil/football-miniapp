from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel, Relationship

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tg_id: int = Field(index=True, unique=True)
    username: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    bookings: list["Booking"] = Relationship(back_populates="user")

class Venue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    address: str
    cover_img_url: str | None = None

class Match(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    venue_id: int = Field(foreign_key="venue.id")
    starts_at: datetime
    duration_min: int
    capacity: int
    price: int
    status: str = Field(default="scheduled")

class Booking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    match_id: int = Field(foreign_key="match.id")
    state: str  # main / reserve / cancelled
    expires_at: datetime | None = None
    paid_at: datetime | None = None
    refunded: bool = False
    payment_id: str | None = Field(default=None, index=True)
    user: "User" = Relationship(back_populates="bookings")