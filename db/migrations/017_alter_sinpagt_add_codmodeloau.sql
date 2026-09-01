-- La tabla en producción fue creada antes de agregar las columnas de vehículo.
-- CREATE TABLE IF NOT EXISTS no agrega columnas faltantes, por eso se necesitan ALTER.
-- Este parche agrega idempotentemente las columnas que reportan NO_SUCH_COLUMN.

ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodMarcaAu String;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodModeloAu String;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS AnioVehiculoAut UInt32;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS OrigenVehiculoAut String;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodTipoVehiculoAut UInt32;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodUsoVehiculoAut UInt32;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS SumaAseguradaAut UInt32;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodInderProvinciaAut UInt32;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS CodCoberturaAut String;
ALTER TABLE sinpagt ADD COLUMN IF NOT EXISTS Importe Float32;
