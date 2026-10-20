SELECT id, data_movimentacao, valor, descricao
FROM movimentacoes
ORDER BY data_movimentacao, id;

SELECT COUNT(*) AS quantidade FROM movimentacoes;

SELECT
    COALESCE(SUM(CASE WHEN valor > 0 THEN valor ELSE 0 END), 0) AS entradas,
    COALESCE(SUM(CASE WHEN valor < 0 THEN valor ELSE 0 END), 0) AS saidas,
    COALESCE(SUM(valor), 0) AS saldo_calculado
FROM movimentacoes;

SELECT chave_unica, COUNT(*) AS repeticoes
FROM movimentacoes
WHERE chave_unica IS NOT NULL
GROUP BY chave_unica
HAVING COUNT(*) > 1;
