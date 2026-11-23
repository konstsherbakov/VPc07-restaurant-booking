
from datetime import datetime

from postgres_driver import PostgresDriver
from models.user import User
from models.table import Table
from models.booking import Booking


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def _get_rows(cur):
    """Преобразует результат SQL в список словарей."""
    columns = [column[0] for column in cur.description]
    return [
        dict(zip(columns, row))
        for row in cur.fetchall()
    ]


def _validate_period(start_time, end_time):
    if start_time >= end_time:
        raise ValueError(
            "Время окончания должно быть позже начала"
        )


def _is_available(
    cur, table_id, start_time, end_time,
    exclude_booking_id=None
):
    """Проверяет пересечение с другими бронями."""
    cur.execute(
        """
        SELECT 1 FROM bookings
        WHERE table_id = %s
          AND start_time < %s
          AND end_time > %s
          AND (%s IS NULL OR id <> %s)
        LIMIT 1
        """,
        (
            table_id, end_time, start_time,
            exclude_booking_id, exclude_booking_id
        )
    )
    return cur.fetchone() is None


# ==========================================
# USERS — ПОЛЬЗОВАТЕЛИ
# ==========================================

def create_user(name: str, phone: str) -> User:
    if not name.strip() or not phone.strip():
        raise ValueError("Имя и телефон обязательны")

    name, phone = name.strip(), phone.strip()
    conn = PostgresDriver().get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (name, phone)
                    VALUES (%s, %s) RETURNING id
                    """,
                    (name, phone)
                )
                user_id = cur.fetchone()[0]

        return User(id=user_id, name=name, phone=phone)
    finally:
        conn.close()


def get_all_users():
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users ORDER BY id"
                )
                return _get_rows(cur)
    finally:
        conn.close()


def update_user(user_id: int, name: str, phone: str):
    if not name.strip() or not phone.strip():
        raise ValueError("Имя и телефон обязательны")

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET name = %s, phone = %s
                    WHERE id = %s
                    RETURNING id
                    """,
                    (name.strip(), phone.strip(), user_id)
                )
                if cur.fetchone() is None:
                    raise ValueError("Пользователь не найден")
        return True
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM users WHERE id = %s RETURNING id",
                    (user_id,)
                )
                return cur.fetchone() is not None
    finally:
        conn.close()


# ==========================================
# TABLES — СТОЛЫ
# ==========================================

def create_table(table_number: int, seats: int) -> Table:
    if table_number <= 0 or seats <= 0:
        raise ValueError("Номер и количество мест должны быть > 0")

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO restaurant_tables
                    (table_number, seats)
                    VALUES (%s, %s) RETURNING id
                    """,
                    (table_number, seats)
                )
                table_id = cur.fetchone()[0]

        return Table(
            id=table_id,
            table_number=table_number,
            seats=seats
        )
    finally:
        conn.close()


def get_all_tables():
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM restaurant_tables
                    ORDER BY table_number
                    """
                )
                return _get_rows(cur)
    finally:
        conn.close()


def update_table(table_id: int, table_number: int, seats: int):
    if table_number <= 0 or seats <= 0:
        raise ValueError("Номер и количество мест должны быть > 0")

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE restaurant_tables
                    SET table_number = %s, seats = %s
                    WHERE id = %s
                    RETURNING id
                    """,
                    (table_number, seats, table_id)
                )
                if cur.fetchone() is None:
                    raise ValueError("Стол не найден")
        return True
    finally:
        conn.close()


def delete_table(table_id: int):
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM restaurant_tables
                    WHERE id = %s RETURNING id
                    """,
                    (table_id,)
                )
                return cur.fetchone() is not None
    finally:
        conn.close()


# ==========================================
# BOOKINGS — БРОНИРОВАНИЯ
# ==========================================

def check_table_availability(
    table_id: int,
    start_time: datetime,
    end_time: datetime
) -> bool:
    _validate_period(start_time, end_time)

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM restaurant_tables
                    WHERE id = %s
                    """,
                    (table_id,)
                )
                if cur.fetchone() is None:
                    raise ValueError("Стол не найден")

                return _is_available(
                    cur, table_id, start_time, end_time
                )
    finally:
        conn.close()


def create_booking(
    user_id: int,
    table_id: int,
    start_time: datetime,
    end_time: datetime
) -> Booking:
    _validate_period(start_time, end_time)

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:

                # Блокировка стола исключает гонку
                # между одновременными бронированиями.
                cur.execute(
                    """
                    SELECT id FROM restaurant_tables
                    WHERE id = %s FOR UPDATE
                    """,
                    (table_id,)
                )
                if cur.fetchone() is None:
                    raise ValueError("Стол не найден")

                if not _is_available(
                    cur, table_id, start_time, end_time
                ):
                    raise ValueError(
                        "Стол уже забронирован на это время"
                    )

                cur.execute(
                    """
                    INSERT INTO bookings
                    (user_id, table_id, start_time, end_time)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, table_id, start_time, end_time)
                )
                booking_id = cur.fetchone()[0]

        return Booking(
            id=booking_id,
            user_id=user_id,
            table_id=table_id,
            start_time=start_time,
            end_time=end_time
        )
    finally:
        conn.close()


def get_all_bookings():
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        b.id,
                        b.user_id,
                        u.name AS user_name,
                        b.table_id,
                        t.table_number,
                        b.start_time,
                        b.end_time
                    FROM bookings b
                    JOIN users u ON b.user_id = u.id
                    JOIN restaurant_tables t
                        ON b.table_id = t.id
                    ORDER BY b.start_time, b.id
                    """
                )
                return _get_rows(cur)
    finally:
        conn.close()


def update_booking(
    booking_id: int,
    user_id: int,
    table_id: int,
    start_time: datetime,
    end_time: datetime
):
    _validate_period(start_time, end_time)

    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM bookings
                    WHERE id = %s FOR UPDATE
                    """,
                    (booking_id,)
                )
                if cur.fetchone() is None:
                    raise ValueError("Бронирование не найдено")

                cur.execute(
                    """
                    SELECT id FROM restaurant_tables
                    WHERE id = %s FOR UPDATE
                    """,
                    (table_id,)
                )
                if cur.fetchone() is None:
                    raise ValueError("Стол не найден")

                if not _is_available(
                    cur, table_id, start_time, end_time,
                    exclude_booking_id=booking_id
                ):
                    raise ValueError(
                        "Новое время пересекается с другой бронью"
                    )

                cur.execute(
                    """
                    UPDATE bookings
                    SET user_id = %s,
                        table_id = %s,
                        start_time = %s,
                        end_time = %s
                    WHERE id = %s
                    """,
                    (
                        user_id, table_id,
                        start_time, end_time, booking_id
                    )
                )
        return True
    finally:
        conn.close()


def delete_booking(booking_id: int):
    conn = PostgresDriver().get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM bookings
                    WHERE id = %s RETURNING id
                    """,
                    (booking_id,)
                )
                return cur.fetchone() is not None
    finally:
        conn.close()
