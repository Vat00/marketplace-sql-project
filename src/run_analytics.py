import os
import logging
import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
base_dir = os.path.dirname(os.path.dirname(__file__))
log_file_path = os.path.join(base_dir, 'pipeline.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_connection():
    return create_engine("postgresql+pg8000://de_user:de_password@localhost:5433/ecommerce_dwh")

def run_sql_analysis(sql_filename, output_csv_name, metric_name):
    logging.info(f"Инициализация запуска: {metric_name}...")
    sql_path = os.path.join(base_dir, 'sql', sql_filename)
    
    if not os.path.exists(sql_path):
        logging.error(f"Критическая ошибка: Файл не найден по пути {sql_path}")
        return
        
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_query = f.read()
        
        engine = get_connection()
        logging.info(f"Отправка запроса {sql_filename} в PostgreSQL...")
        
        df = pd.read_sql_query(sql_query, engine)
        logging.info(f"Данные успешно получены. Сгенерировано строк: {len(df)}")
        
        print(f"\n=== РЕЗУЛЬТАТЫ: {metric_name.upper()} ===")
        print(df.to_string(index=False))
        print("======================================\n")
        
        output_csv = os.path.join(base_dir, output_csv_name)
        df.to_csv(output_csv, index=False)
        logging.info(f"Отчет успешно сохранен в файл: {output_csv}")
        
    except Exception as e:
        logging.exception(f"Произошел сбой во время расчета {metric_name}: {e}")

if __name__ == "__main__":
    run_sql_analysis('abc_analysis.sql', 'abc_result.csv', 'ABC-анализ товаров')
    run_sql_analysis('retention.sql', 'retention_result.csv', 'Когортный Retention Rate')
    run_sql_analysis('ltv_cohorts.sql', 'ltv_result.csv', 'Когортный Накопительный LTV')
