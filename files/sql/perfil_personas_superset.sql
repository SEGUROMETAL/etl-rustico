drop View v_personas_perfil_superset;




WITH
    ope AS
    (
SELECT
	CodRama,
	CodOrganizador,
	CodProductor,
	NroAsegurado,
	toStartOfMonth(FEmision) AS FechaMes,
	sum(PrimaNeta) AS PrimaNeta,
	sum(RecAdm) AS RecAdm,
	sum(RecFin) AS RecFin,
	sum(RecCapital) AS RecCapital
FROM
	reportes.sehpm151t
GROUP BY
	CodRama,
	CodOrganizador,
	CodProductor,
	NroAsegurado,
	FechaMes
    ),
    sp AS
    (
SELECT
	CodRama,
	CodOrganizador,
	CodProductor,
	NroAsegurado,
	FechaPagoMes as FechaMes,
	sum(Importe) AS ImporteSiniestro
FROM
	reportes.sinpagt_agg
GROUP BY
	CodRama,
	CodOrganizador,
	CodProductor,
	NroAsegurado,
	FechaPagoMes
    ),
    fin AS
    (
SELECT
	case when ope.CodRama > 0 then ope.CodRama
 		else sp.CodRama
	end AS CodRama,
	case when ope.CodOrganizador > 0 then ope.CodOrganizador
		else sp.CodOrganizador
		end AS CodOrganizador,
	case when ope.CodProductor > 0 then ope.CodProductor
 		else sp.CodProductor
 	end AS CodProductor,
case when ope.NroAsegurado > 0 then ope.NroAsegurado
 else sp.NroAsegurado
 END AS NroAsegurado, 
 case 
	when (ope.FechaMes > '1970-01-01') then ope.FechaMes
 	else sp.FechaMes 
 end AS FechaMes,
	coalesce(ope.PrimaNeta,
 0) AS PrimaNeta,
	coalesce(ope.RecAdm,
 0) AS RecAdm,
	coalesce(ope.RecFin,
 0) AS RecFin,
	coalesce(ope.RecCapital,
 0) AS RecCapital,
	((coalesce(ope.PrimaNeta,
 0) + coalesce(ope.RecAdm,
 0)) + coalesce(ope.RecFin,
 0)) + coalesce(ope.RecCapital,
 0) AS PremioNeto,
	coalesce(sp.ImporteSiniestro,
 0) AS ImporteSiniestro,
	(((coalesce(ope.PrimaNeta,
 0) + coalesce(ope.RecAdm,
 0)) + coalesce(ope.RecFin,
 0)) + coalesce(ope.RecCapital,
 0)) - coalesce(sp.ImporteSiniestro,
 0) AS Resultado
FROM
	ope
FULL OUTER JOIN sp ON
	(ope.CodRama = sp.CodRama)
		AND (ope.CodOrganizador = sp.CodOrganizador)
			AND (ope.CodProductor = sp.CodProductor)
				AND (ope.NroAsegurado = sp.NroAsegurado)
					AND (ope.FechaMes = sp.FechaMes)
    )      
SELECT
	da.persona_key,
	any(da.Nombre) AS Nombre,
	fin.CodRama,
	fin.CodOrganizador,
	any(do.Nombre) AS NomOrganizador,
	-- concat(toString(fin.CodOrganizador),' - ',do.Nombre) AS Organizador,
	any(Grupo) AS GrupoOrganizador,
	fin.CodProductor,
	any(dp.Nombre) AS NomProductor,
	-- concat(toString(fin.CodProductor),' - ',dp.Nombre) AS Productor,
	fin.FechaMes,
	toYear(fin.FechaMes) AS `Año`,
	toMonth(fin.FechaMes) AS Mes,
	sum(fin.PrimaNeta) AS PrimaNeta,
	sum(fin.RecAdm) AS RecAdm,
	sum(fin.RecFin) AS RecFin,
	sum(fin.RecCapital) AS RecCapital,
	sum(fin.PremioNeto) AS PremioNeto,
	sum(fin.ImporteSiniestro) AS ImporteSiniestro,
	sum(fin.Resultado) AS Resultado
FROM
	fin
left JOIN reportes.v_dim_daf_actual AS da ON
	da.NroPersona = fin.NroAsegurado
LEFT JOIN reportes.dim_productores AS dp ON
	dp.CodProductor = fin.CodProductor
LEFT JOIN reportes.dim_organizadores AS do ON
	do.CodOrganizador = fin.CodOrganizador
GROUP BY
	da.persona_key,
	fin.CodRama,
	fin.CodOrganizador,
	-- NomOrganizador,
	-- Organizador,
	-- GrupoOrganizador,
	fin.CodProductor,
	-- NomProductor,
	-- Productor,
	fin.FechaMes	
HAVING
	(PrimaNeta != 0)
	OR (ImporteSiniestro != 0)
;