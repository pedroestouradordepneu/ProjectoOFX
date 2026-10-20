-- Executar no Editor SQL do DBeaver após importar com --postgres.
-- 1. Todas as movimentações, ordenadas por data:
SELECT id, data_movimentacao, valor, descricao
FROM movimentacoes
ORDER BY data_movimentacao, id;

-- 2. Total de registros gravados:
SELECT COUNT(*) AS quantidade FROM movimentacoes;

-- 3. Resumo financeiro (valores de saída são negativos):
SELECT
    COALESCE(SUM(CASE WHEN valor > 0 THEN valor ELSE 0 END), 0) AS entradas,
    COALESCE(SUM(CASE WHEN valor < 0 THEN valor ELSE 0 END), 0) AS saidas,
    COALESCE(SUM(valor), 0) AS saldo_calculado
FROM movimentacoes;

-- 4. Validar ausência de duplicatas por chave bancária:
SELECT chave_unica, COUNT(*) AS repeticoes
FROM movimentacoes
WHERE chave_unica IS NOT NULL
GROUP BY chave_unica
HAVING COUNT(*) > 1;
