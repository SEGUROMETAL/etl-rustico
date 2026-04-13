with cte as (
    SELECT
        `FEmision`,
        `Op`,
        `CodRama`,
        `Poliza`,
        `Suplemento`,
        `CodProductor`,
        `PrimaNeta`,
        `BonifPrima` * 100 / `PrimaTarifa` as `%Bonif.`
        /*,
         MIN(`Suplemento`) OVER(PARTITION BY `Op`) as ps*/
    from
        emisiones_operaciones e
    WHERE
        `CodRama` = 4 -- and Op >= 6315832
        AND `CodProductor` <> 9999
        AND e.CodProductor = e.CodProductorCom
        AND `PrimaNeta` <> 0
        AND NOT EXISTS (
            SELECT
                *
            from
                `SEHICO` s
            WHERE
                e.`Op` = s.`ICOPER`
                AND e.`Suplemento` = s.`ICSUOP`
                AND s.`ICTINT` = 4
        )
)
SELECT
    *
FROM
    cte
where
    `%Bonif.` < 10
order by
    cte.Poliza DESC;