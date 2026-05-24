WITH user_cohorts AS (
    -- Шаг 1: Находим месяц регистрации каждого юзера (база для когорты)
    SELECT 
        user_id,
        DATE_TRUNC('month', reg_date) AS cohort_month
    FROM users
),
cohort_sizes AS (
    -- Шаг 2: Считаем, сколько ВСЕГО людей зарегистрировалось в каждой когорте
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) AS total_users
    FROM user_cohorts
    GROUP BY cohort_month
),
order_revenues AS (
    -- Шаг 3: Считаем стоимость каждого заказа (цена товара * количество)
    SELECT 
        o.user_id,
        o.order_date,
        DATE_TRUNC('month', o.order_date) AS order_month,
        (o.quantity * p.price) AS order_amount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
),
cohort_monthly_revenue AS (
    -- Шаг 4: Объединяем юзеров с их заказами и находим "месяц жизни" (month_age)
    SELECT 
        c.cohort_month,
        -- Вычисляем разницу в месяцах между покупкой и регистрацией
        (EXTRACT(YEAR FROM r.order_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM r.order_month) - EXTRACT(MONTH FROM c.cohort_month)) AS month_age,
        -- Суммируем всю выручку, которую принесли ВСЕ юзеры этой когорты в конкретный месяц жизни
        SUM(r.order_amount) AS monthly_revenue
    FROM user_cohorts c
    JOIN order_revenues r ON c.user_id = r.user_id
    GROUP BY c.cohort_month, month_age
),
cumulative_ltv AS (
    -- Шаг 5: Используем оконную функцию, чтобы посчитать НАКОПИТЕЛЬНУЮ выручку когорты
    SELECT 
        cmr.cohort_month,
        cmr.month_age,
        sz.total_users,
        -- Нарастающий итог выручки по месяцам внутри каждой когорты
        SUM(cmr.monthly_revenue) OVER (
            PARTITION BY cmr.cohort_month
            ORDER BY cmr.month_age
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM cohort_monthly_revenue cmr
    JOIN cohort_sizes sz ON cmr.cohort_month = sz.cohort_month
)
-- Шаг 6: Финальный расчет LTV (накопительная выручка / общее количество юзеров в когорте)
SELECT 
    TO_CHAR(cohort_month, 'YYYY-MM') AS cohort,
    total_users AS cohort_size,
    month_age,
    ROUND((cumulative_revenue::NUMERIC / total_users), 2) AS ltv_value
FROM cumulative_ltv
WHERE month_age >= 0
ORDER BY cohort, month_age;
