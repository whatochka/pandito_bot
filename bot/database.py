from asyncpg import create_pool


class DB:
    def __init__(self) -> None:
        self.db_pool = None

    async def init(self, pg_url):
        self.db_pool = await create_pool(pg_url)

    async def create_user(self, tg: int, name: str, is_admin=False):
        async with self.db_pool.acquire() as conn:
            sql = """
            INSERT INTO users (tg, name, is_admin) 
            VALUES ($1, $2, $3)
            RETURNING id;
            """
            return await conn.fetchval(sql, tg, name, is_admin)

    async def get_user(self, tg: int):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT * FROM users WHERE tg = $1;"
            return await conn.fetchrow(sql, tg)

    async def get_all_users(self):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT * FROM users"
            return await conn.fetch(sql)

    async def get_user_by_id(self, id: int):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT * FROM users WHERE id = $1;"
            return await conn.fetchrow(sql, id)

    async def update_user_balance(self, id: int, amount: int, invoker: int):
        async with self.db_pool.acquire() as conn:
            invoker_user = await conn.fetchval("SELECT id FROM users WHERE id = $1", invoker)
            if not invoker_user:
                raise ValueError(f"Invoker with id {invoker} does not exist in users table")
            async with conn.transaction():
                # Обновляем баланс пользователя
                sql_update = """
                UPDATE users 
                SET balance = balance + $1, updated_at = NOW()
                WHERE id = $2 RETURNING balance;
                """
                new_balance = await conn.fetchval(sql_update, amount, id)

                # Добавляем запись в логи
                sql_insert_log = """
                INSERT INTO logs (user_id, description)
                VALUES ($1, $2);
                """
                await conn.execute(sql_insert_log, invoker, f"Added money {amount} to user {id}")
        return new_balance

    async def set_user_balance(self, id: int, amount: int, invoker: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            UPDATE users 
            SET balance = $1, updated_at = NOW()
            WHERE id = $2 RETURNING balance;
            INSERT INTO logs (user_id, description)
            VALUES (user_id, 'Set money ' || $1 || ' to ' || $2 || ' user');
            """
            return await conn.fetchval(sql, amount, id, invoker)

    async def change_user_stage(self, id: int, stage: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            UPDATE users 
            SET stage = $1, updated_at = NOW()
            WHERE id = $2 RETURNING stage;
            """
            return await conn.fetchval(sql, stage, id)

    async def is_user_admin(self, tg: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            SELECT is_admin 
            FROM users 
            WHERE tg = $1;
            """
            return await conn.fetchval(sql, tg)

    async def create_product(self, name: str, description: str, price: int, stock: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            INSERT INTO products (name, description, price, stock)
            VALUES ($1, $2, $3, $4)
            RETURNING id;
            """
            return await conn.fetchval(sql, name, description, price, stock)

    async def get_product(self, product_id: int):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT * FROM products WHERE id = $1;"
            return await conn.fetchrow(sql, product_id)

    async def update_product_stock(self, product_id: int, new_stock: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            UPDATE products 
            SET stock = $1, updated_at = NOW() 
            WHERE id = $2
            RETURNING stock;
            """
            return await conn.fetchval(sql, new_stock, product_id)

    async def change_product_price(self, product_id: int, new_price: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            UPDATE products 
            SET price = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING price;
            """
            return await conn.fetchval(sql, new_price, product_id)

    async def get_user_purchases(self, user_id: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            SELECT 
                p.id AS product_id,
                p.name AS product_name,
                p.description AS product_description,
                p.price AS product_price,
                pu.quantity AS quantity_purchased,
                pu.created_at AS purchase_date
            FROM 
                purchases pu
            JOIN 
                products p ON pu.product_id = p.id
            WHERE 
                pu.user_id = (SELECT id FROM users WHERE id = $1);
            """
            return await conn.fetch(sql, user_id)

    async def get_available_products(self):
        async with self.db_pool.acquire() as conn:
            sql = """
            SELECT * FROM products 
            WHERE stock > 0;
            """
            return await conn.fetch(sql)

    async def log_action(self, user_id: int, description: str):
        async with self.db_pool.acquire() as conn:
            sql = """
            INSERT INTO logs (user_id, description) 
            VALUES ($1, $2)
            RETURNING id;
            """
            return await conn.fetchval(sql, user_id, description)

    async def get_user_logs(self, user_id: int):
        async with self.db_pool.acquire() as conn:
            sql = """
            SELECT * FROM logs 
            WHERE user_id = $1;
            """
            return await conn.fetch(sql, user_id)

    async def transfer_funds(self, sender_id: int, receiver_id: int, amount: int):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT transfer_funds($1, $2, $3);"
            return await conn.fetchval(sql, sender_id, receiver_id, amount)

    async def buy_product(self, user_id: int, product_id: int, quantity: int):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT buy_product($1, $2, $3);"
            return await conn.fetchval(sql, user_id, product_id, quantity)

    async def clear_user_purchases(self, user_id: int):
        async with self.db_pool.acquire() as conn:
            sql = "DELETE FROM purchases WHERE user_id = $1;"
            await conn.execute(sql, user_id)

    async def delete_product(self, product_id: int):
        async with self.db_pool.acquire() as conn:
            sql = "DELETE FROM products WHERE id = $1;"
            await conn.execute(sql, product_id)

    async def get_all_products(self):
        async with self.db_pool.acquire() as conn:
            sql = "SELECT * FROM products;"
            return await conn.fetch(sql)

