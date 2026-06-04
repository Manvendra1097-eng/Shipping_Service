import sqlite3
from typing import Any

from app.schema import ShipmentCreate, ShipmentUpdate


class DB:
    def __init__(self):
        self.conn = sqlite3.connect("sqlite.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.create_table("shipment")

    def create_table(self, name: str):
        # 1. create table
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {name} (
                id INTEGER PRIMARY KEY,
                content TEXT,
                weight REAL,
                status TEXT
            )
        """)

    def create(self, shipment: ShipmentCreate) -> int:
        # 2. insert row
        self.cur.execute("SELECT MAX(id) FROM shipment")
        row = self.cur.fetchone()
        new_id = (row[0] or 0) + 1
        self.cur.execute(
            """
                    INSERT INTO shipment
                    VALUES (:id, :content, :weight, :status)
                    """,
            {"id": new_id, **shipment.model_dump(), "status": "placed"},
        )
        self.conn.commit()
        return self.cur.lastrowid

    def get(self, id: int) -> dict[str, Any] | None:
        self.cur.execute(
            """
                        SELECT * FROM shipment where id = ?
                         """,
            (id,),
        )
        result = self.cur.fetchone()

        if result is None:
            return None
        return dict(result)

    def update(self, id: int, shipment: ShipmentUpdate) -> dict[str, Any] | None:
        self.cur.execute(
            """
                         UPDATE shipment SET status = ? where id = ?
                         """,
            (
                shipment.status,
                id,
            ),
        )
        self.conn.commit()
        return self.get(id)

    def delete(self, id: int):
        self.cur.execute(
            """
                        DELETE FROM shipment WHERE id = ?
                         """,
            (id,),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
