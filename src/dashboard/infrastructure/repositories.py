# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from ..domain.ports import DashboardPort
from typing import Dict
import polars as pl

class DashboardRepository(DashboardPort):
    def __init__(self, excel: Dict[str, pl.DataFrame]):
        self.dataframe = excel

    async def get_data_dashboard(self, sheet_name:str, entity:str):
        df = self.dataframe.get(sheet_name)
        data = df.filter(pl.col("Entidad") == entity)
        return data.to_dicts()[0]