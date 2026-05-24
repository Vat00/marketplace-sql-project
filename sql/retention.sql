WITH user_cohorts AS (
    -- Шаг 1: Находим месяц регистрации для каждого пользователя.
    -- DATE_TRUNC('month', ...) округляет дату до 1-го числа месяца.
    -- Например: 2026-03-14 превратится в 2026-03-01.
    SELECT 
        user_id,
        DATE_TRUNC('month', reg_date) AS cohort_month
    FROM users
),
user_orders_months AS (
    -- Шаг 2: Находим все уникальные месяцы, в которые пользователи делали заказы.
    -- DISTINCT убирает дубликаты, если юзер покупал несколько раз за один месяц.
    SELECT DISTINCT
        o.user_id,
        DATE_TRUNC('month', o.order_date) AS order_month
    FROM orders o
),
cohort_sizes AS (
    -- Шаг 3: Считаем общее (базовое) количество уникальных пользователей в каждой когорте.
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) AS total_users
    FROM user_cohorts
    GROUP BY cohort_month
),
retention_table AS (
    -- Шаг 4: Соединяем когорты с месяцами заказов и вычисляем "индекс" месяца (возраст активности).
    SELECT 
        c.cohort_month,
        m.order_month,
        -- Рассчитываем разницу между месяцем заказа и месяцем регистрации в месяцах.
        -- Переводим разницу лет в месяцы (умножая на 12) + добавляем разницу месяцев.
        (EXTRACT(YEAR FROM m.order_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM m.order_month) - EXTRACT(MONTH FROM c.cohort_month)) AS month_number,
        -- Считаем, сколько уникальных пользователей вернулось в этом месяце
        COUNT(DISTINCT m.user_id) AS active_users
    FROM user_cohorts c
    JOIN user_orders_months m ON c.user_id = m.user_id
    GROUP BY c.cohort_month, m.order_month
)
-- Шаг 5: Финальный расчет матрицы Retention Rate в процентах.
SELECT 
    TO_CHAR(r.cohort_month, 'YYYY-MM') AS cohort, -- Форматируем дату в красивую строку '2026-01'
    sz.total_users AS cohort_size,
    r.month_number AS month_age,
    -- Рассчитываем процент удержания. 
    -- Приведение к ::NUMERIC нужно, чтобы избежать целочисленного деления (дробь не превратилась в 0).
    ROUND((r.active_users::NUMERIC / sz.total_users) * 100, 2) AS retention_rate
FROM retention_table r
JOIN cohort_sizes sz ON r.cohort_month = sz.cohort_month
WHERE r.month_number >= 0 -- Защита от багов с датами
ORDER BY cohort, month_age;
