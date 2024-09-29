import pandas as pd
from xsdata.formats.dataclass.parsers import XmlParser
from collections import OrderedDict
from sped.arquivos import ArquivoDigital
from sped.registros import Registro
from sped.campos import Campo
from tqdm import tqdm
import importlib
import locale
import json

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


class ArquivoDigitalHandler:
    """
    Handles the processing and management of digital file records.

    This class is responsible for loading schemas, building pandas DataFrames from digital file records, 
    and exporting the data to Excel files. It manages hierarchical relationships between records and 
    provides access to the constructed DataFrames.

    Args:
        arquivo_digital (ArquivoDigital): The digital file containing records to be processed.
        layout (ExportLayout): The layout definition used for exporting the records.

    Attributes:
        get_dataframes (OrderedDict): Property that returns the constructed DataFrames.

    Examples:
        handler = ArquivoDigitalHandler(arquivo_digital, schema)
        handler.build_dataframes(silent=False)
        handler.to_excel("output.xlsx")
    """

    def __init__(self, arquivo_digital: ArquivoDigital, config_file: str):
        self._dataframes = None
        self._arquivo_digital = arquivo_digital
        self.__load_export_config(config_file)
        
        
            
    def __load_export_config(self, config_file):
        
        with open(config_file, 'r') as f:
            self._config_file = json.load(f)
            
            self._data_source_list = self._config_file.get("data_source_list", [])
            self._clazz_path = self._config_file.get("clazz_path", None)
            self._spreadsheet = self._config_file.get("spreadsheet", [])


    @property
    def get_dataframes(self) -> OrderedDict:
        return self._dataframes

    def build_dataframes(self, verbose=True):
        """
        Builds a dictionary of pandas DataFrames from the records in the digital file.

        This method processes each record, extracting relevant columns and values, 
        and organizes them into DataFrames based on their unique identifiers. 
        It also handles hierarchical relationships between records.

        Args:
            verbose (bool): If False, suppresses progress output during processing. Defaults to True.

        Returns:
            None: The method assigns the constructed DataFrames to the instance variable _dataframes.

        Examples:
            handler.build_dataframes(verbose=False)
        """
        df = {}
        cache = {}
        table_map = self.__create_table_map()

        for registro in tqdm(self.__get_all_registros(), 
                            desc="processing dataframe", 
                            colour="RED",
                            disable=not verbose):

            if registro.REG in table_map:
                r_keys_cols = table_map[registro.REG][1]
                r_keys_vals = [self.__get_registro_value(registro, kcol) for kcol in r_keys_cols]
                if r_keys_cols:
                    cache[registro.REG] = [r_keys_cols, r_keys_vals]

                r_parent = table_map[registro.REG][2]
                r_cols = [registro.REG] + table_map[registro.REG][0]
                r_vals = [self.__get_registro_value(registro, col) for col in r_cols]
                while r_parent:
                    r_cols = [r_parent] + cache[r_parent][0] + r_cols
                    r_vals = [r_parent] + cache[r_parent][1] + r_vals
                    r_parent = table_map[r_parent][2]

                if registro.REG not in df:
                    df[registro.REG] = pd.DataFrame(columns=self.__get_cols_names(r_cols))

                df[registro.REG].loc[len(df[registro.REG])] = r_vals

        self._dataframes = df

    def __get_cols_names(self, cols: any):
        return [col.nome if isinstance(col, Campo) else col for col in cols]

    def __get_registro_value(self, registro: Registro, obj: any):
        return getattr(registro, obj.nome) if isinstance(obj, Campo) else str(obj)

    def __create_table_map(self): 
        map = {}
        for data_source in self._data_source_list: 

            all_columns_dict = self.__get_all_cols_dict(data_source['clazz'])   

            cols, idx_cols, idx_names = [], [], []
            cols = list(all_columns_dict.values())

            if 'index' in data_source.keys():
                idx_names = data_source['index'].split("|")                
                idx_cols.extend(all_columns_dict.get(idx) for idx in idx_names)
            
            map[data_source['id']] = (cols, idx_cols, data_source.get('parent', None))

        return map

    def __get_all_cols_dict(self, data_source: str):
        dict = {}
        try:
            modulo = importlib.import_module(self._clazz_path)
            clazz = getattr(modulo, data_source)
            for campo in getattr(clazz, 'campos'):
                if campo.nome != 'REG':
                    dict[campo.nome] = campo
        except ImportError:
            print(f"Erro: O módulo '{modulo}' não foi encontrado.")
        except AttributeError:
            print(f"Erro: A classe '{clazz}' não foi encontrada no módulo '{modulo}'.")
        return dict

    def to_excel(self, filename, verbose = True):
        """
        Exports the constructed DataFrames to an Excel file.

        This method iterates through the schema blocks and their associated records, 
        exporting each DataFrame to a separate sheet in the specified Excel file. 
        It skips any records marked for exclusion.

        Args:
            filename (str): The name of the Excel file to which the data will be exported.
            verbose (bool): If False, suppresses progress output during processing. Defaults to True.

        Raises:
            RuntimeError: If there is an error during the export process, a RuntimeError is raised 
            with a message indicating the failure.

        Examples:
            handler.to_excel("output.xlsx")
        """

        try:
            with pd.ExcelWriter(filename) as writer:
                for tab in tqdm(self._spreadsheet.get("tabs", []),
                                desc="exporting data", 
                                colour="RED",
                                disable=not verbose):
                    df = self._dataframes[tab['data_source_id']] 
                    df.to_excel(writer, index=False, sheet_name=tab['name'], engine='openpyxl')

        except Exception as ex:
            raise RuntimeError(
                f"Erro não foi possível exportar dados para arquivo: {filename}, erro: {ex}"
            ) from ex
    
    
    def __get_all_registros(self):        
        array = []
        for key in self._arquivo_digital._blocos:
            array += self._arquivo_digital._blocos[key]._registros
        return [self._arquivo_digital._registro_abertura] + array + [self._arquivo_digital._registro_encerramento]
            


