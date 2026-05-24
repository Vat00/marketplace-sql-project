WITH product_revenue AS (
    -- Шаг 1: Считаем чистую выручку по каждому товару за всё время
    SELECT 
        p.product_id,
        p.category,
        p.price,
        SUM(o.quantity * p.price) AS total_revenue
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.category, p.price
),
running_revenue AS (
    -- Шаг 2: Рассчитываем накопительный итог выручки
    SELECT 
        product_id,
        category,
        total_revenue,
        SUM(total_revenue) OVER(
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(total_revenue) OVER() AS total_dwh_revenue
    FROM product_revenue
),
percentage_revenue AS (
    -- Шаг 3: Вычисляем долю накопительной выручки в процентах
    -- Заворачиваем "run_percent" в двойные кавычки для безопасности парсера
    SELECT 
        product_id,
        category,
        total_revenue,
        ROUND((cumulative_revenue::NUMERIC / total_dwh_revenue) * 100, 2) AS "run_percent"
    FROM running_revenue
)
-- Шаг 4: Присваиваем классы A, B или C
SELECT 
    product_id,
    category,
    total_revenue,
    "run_percent", -- Обязательно в кавычках, и не забываем запятую в конце строки!
    CASE 
        WHEN "run_percent" <= 80.00 THEN 'A'
        WHEN "run_percent" <= 95.00 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM percentage_revenue
ORDER BY total_revenue DESC;
