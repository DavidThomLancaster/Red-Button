import sqlite3
from typing import List, Dict
from shared.ParamsDTO import ParamsDTO

class ContactRepository:
    """
    Minimal SQLite repo.
    Schema expectations:
      contacts(id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT, service_area TEXT)
      contact_trades(contact_id TEXT, trade TEXT)  -- trade is canonical string, FK optional
    """

    def __init__(self, db_path="contacts.db", conn: sqlite3.Connection = None):
        if conn:
            self.conn = conn
        else:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
              id TEXT PRIMARY KEY,
              name TEXT,
              email TEXT,
              phone TEXT,
              service_area TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS contact_trades (
              contact_id TEXT,
              trade TEXT
            )
        """)
        self.conn.commit()

    def find_contact_ids_by_trade(self, trade_canonical: str, limit: int | None = None) -> List[str]:
        sql = """
          SELECT DISTINCT contact_id
          FROM contact_trades
          WHERE LOWER(trade) = LOWER(?)
        """
        params = [trade_canonical]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [r[0] for r in rows]

    # NEW: fetch contacts by IDs, preserving caller order
    def get_contacts_by_ids(self, ids: List[str]) -> List[dict]:
        """
        Return contact rows (as dicts) for the given IDs.
        - Preserves the input order.
        - Skips IDs not found.
        - Chunks queries to avoid SQLite's parameter limit (~999).
        """
        if not ids:
            return []

        # de-dup while preserving order
        unique_ids = list(dict.fromkeys(ids))
        PARAM_LIMIT = 900  # cushion under SQLite's param limit
        results_by_id: Dict[str, dict] = {}

        cur = self.conn.cursor()
        for start in range(0, len(unique_ids), PARAM_LIMIT):
            batch = unique_ids[start:start + PARAM_LIMIT]
            placeholders = ",".join("?" for _ in batch)
            sql = f""" 
                SELECT id, name, email, phone, service_area
                FROM contacts
                WHERE id IN ({placeholders})
            """
            rows = cur.execute(sql, batch).fetchall() or []
            for row in rows:
                d = dict(row)
                results_by_id[d["id"]] = d

        # preserve original order; drop missing
        return [results_by_id[cid] for cid in unique_ids if cid in results_by_id]
    
    # TODO Slice 7 - get list of contacts by parameters (trade, service area, etc.)
    
    def find_contacts_by_parameters(self, params_dto: ParamsDTO) -> List[dict]:
        sql = [
            "SELECT DISTINCT c.id, c.name, c.email, c.phone, c.service_area",
            "FROM contacts c",
            "LEFT JOIN contact_trades ct ON c.id = ct.contact_id",
            "WHERE 1=1"
        ]
        query_params = []

        # Apply filters if present
        if params_dto.trade:
            sql.append("AND LOWER(ct.trade) = LOWER(?)")
            query_params.append(params_dto.trade)

        if params_dto.service_area:
            sql.append("AND LOWER(c.service_area) = LOWER(?)")
            query_params.append(params_dto.service_area)

        if params_dto.name:
            sql.append("AND LOWER(c.name) LIKE LOWER(?)")
            query_params.append(f"%{params_dto.name}%")

        # Pagination
        offset = (params_dto.page - 1) * params_dto.limit
        sql.append("LIMIT ? OFFSET ?")
        query_params.extend([params_dto.limit, offset])

        rows = self.conn.execute("\n".join(sql), query_params).fetchall()
        return [dict(r) for r in rows]



# import sqlite3
# from typing import List

# class ContactRepository:
#     """
#     Minimal SQLite repo.
#     Schema expectations:
#       contacts(id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT, service_area TEXT)
#       contact_trades(contact_id TEXT, trade TEXT)  -- trade is canonical string, FK optional
#     """

#     def __init__(self, db_path="contacts.db", conn: sqlite3.Connection = None):
#         if conn:
#             self.conn = conn
#         else:
#             self.conn = sqlite3.connect(db_path, check_same_thread=False)

#         self.conn.row_factory = sqlite3.Row
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS contacts (
#               id TEXT PRIMARY KEY,
#               name TEXT,
#               email TEXT,
#               phone TEXT,
#               service_area TEXT
#             )
#         """)
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS contact_trades (
#               contact_id TEXT,
#               trade TEXT
#             )
#         """)
#         self.conn.commit()


#     def find_contact_ids_by_trade(self, trade_canonical: str, limit: int | None = None) -> List[str]:
#         sql = """
#           SELECT DISTINCT contact_id
#           FROM contact_trades
#           WHERE LOWER(trade) = LOWER(?)
#         """
#         params = [trade_canonical]
#         if limit is not None:
#             sql += " LIMIT ?"
#             params.append(limit)
#         rows = self.conn.execute(sql, params).fetchall()
#         return [r[0] for r in rows]