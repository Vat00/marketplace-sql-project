import psycopg2
from psycopg2 import extras
import random
from datetime import datetime, timedelta
# Добавляем импорт движка SQLAlchemy
from sqlalchemy import create_engine

def get_connection():
    # Просто меняем имя драйвера в строке подключения
    engine = create_engine("postgresql+pg8000://de_user:de_password@localhost:5433/ecommerce_dwh")
    return engine.raw_connection()




def create_schema():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;

        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            reg_date DATE NOT NULL,
            country VARCHAR(50) NOT NULL
        );

        CREATE TABLE products (
            product_id SERIAL PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            price NUMERIC(10, 2) NOT NULL
        );

        CREATE TABLE orders (
            order_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id),
            product_id INT REFERENCES products(product_id),
            order_date DATE NOT NULL,
            quantity INT NOT NULL
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Таблицы успешно созданы в PostgreSQL!")

def populate_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    countries = ['Russia', 'USA', 'Germany', 'Kazakhstan', 'China']
    categories = ['Electronics', 'Clothing', 'Books', 'Home']
    
    # 1. Генерируем товары
    products_data = []
    for _ in range(20):
        products_data.append((random.choice(categories), round(random.uniform(10.0, 1000.0), 2)))
    
    # Вместо execute_values используем универсальный executemany. 
    # Обрати внимание: для pg8000 параметры вставляются через %s или :1. 
    # Чтобы работало везде, используем классический %s.
    cursor.executemany("INSERT INTO products (category, price) VALUES (%s, %s)", products_data)
    
    # 2. Генерируем пользователей
    users_data = []
    base_date = datetime(2026, 1, 1)
    for _ in range(300):
        reg_date = base_date + timedelta(days=random.randint(0, 90))
        users_data.append((reg_date.date(), random.choice(countries)))
        
    cursor.executemany("INSERT INTO users (reg_date, country) VALUES (%s, %s)", users_data)
    
    # Чтобы правильно связать заказы, вытаскиваем сгенерированных юзеров
    cursor.execute("SELECT user_id, reg_date FROM users")
    users_from_db = cursor.fetchall()
    
    # 3. Генерируем заказы
    orders_data = []
    for _ in range(1500):
        user_id, reg_date = random.choice(users_from_db)
        order_date = reg_date + timedelta(days=random.randint(0, 60))
        product_id = random.randint(1, 20)
        quantity = random.randint(1, 4)
        orders_data.append((user_id, product_id, order_date, quantity))
        
    cursor.executemany("INSERT INTO orders (user_id, product_id, order_date, quantity) VALUES (%s, %s, %s, %s)", orders_data)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Данные успешно залиты в PostgreSQL!")

if __name__ == "__main__":
    create_schema()
    populate_data()
