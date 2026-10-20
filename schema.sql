CREATE TABLE IF NOT EXISTS movimentacoes (
    id SERIAL PRIMARY KEY,
    data_movimentacao DATE,
    valor NUMERIC(15,2),
    descricao VARCHAR(255),
    chave_unica VARCHAR(64) UNIQUE
);

ALTER TABLE movimentacoes
    ADD COLUMN IF NOT EXISTS chave_unica VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS uq_movimentacoes_chave_unica
    ON movimentacoes (chave_unica);
