import pandas as pd
import clickhouse_connect
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_abc_to_clickhouse():
    try:
        # 1. Читаем твой CSV файл
        logging.info("Чтение данных из abc_result.csv...")
        df = pd.read_csv('abc_result.csv')
        
        # Явно приводим типы под будущую таблицу ClickHouse
        df['product_id'] = df['product_id'].astype(int)
        df['category'] = df['category'].astype(str)
        df['total_revenue'] = df['total_revenue'].astype(float)
        df['run_percent'] = df['run_percent'].astype(float)
        df['abc_class'] = df['abc_class'].astype(str)

        # 2. Подключаемся к локальному ClickHouse
        logging.info("Подключение к ClickHouse...")
        client = clickhouse_connect.get_client(host='localhost', port=8125, username='default', password='')

        # 3. Создаем базу и таблицу с колоночным движком MergeTree
        client.command('CREATE DATABASE IF NOT EXISTS marketplace_analytics')
        
        client.command('''
            CREATE TABLE IF NOT EXISTS marketplace_analytics.abc_analysis (
                product_id Int64,
                category String,
                total_revenue Float64,
                run_percent Float64,
                abc_class String
            ) ENGINE = MergeTree()
            ORDER BY (abc_class, category)
        ''')
        logging.info("Таблица marketplace_analytics.abc_analysis проверена/создана.")

        # 4. Загружаем данные пачкой
        logging.info("Загрузка данных в ClickHouse...")
        client.insert('marketplace_analytics.abc_analysis', df.values.tolist(), 
                      column_names=['product_id', 'category', 'total_revenue', 'run_percent', 'abc_class'])
        
        logging.info("Успех! Данные перенесены в ClickHouse.")
        
    except Exception as e:
        logging.error(f"Ошибка пайплайна: {e}")

if __name__ == '__main__':
    load_abc_to_clickhouse()
