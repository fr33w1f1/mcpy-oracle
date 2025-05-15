from typing import List, Dict
import pandas as pd
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
import oracledb

from config import settings

mcp = FastMCP("oracledb_mcp_server")


@mcp.tool(name="execute_sql", description="Executes an SQL query on the Oracle Database")
def execute_sql(sqlString: str) -> str:
    """
    Execute a SQL query against the Oracle database.
    
    This function executes the provided SQL query using the established database 
    connection and returns the result as a JSON string. If an error occurs during
    execution, the function will log the error and return a JSON error message.
    
    Args:
        sqlString (str): The SQL query to execute
    
    Returns:
        str: JSON string containing either query results or error message
    """
    with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
        with connection.cursor() as cursor:
            try:
                result = cursor.execute(text(sqlString))
                rows = cursor.fetchmany(settings.query_limit_size)
                df = pd.DataFrame(rows, columns=result.keys())
                return df.to_json(orient='records', indent=2)
            except Exception as e:
                error_msg = {"error": str(e), "status": "failed"}
                return pd.Series(error_msg).to_json(indent=2)
    
@mcp.tool(name='get_schemas', description="Retrieve a list of available schemas (users) in the database")
def get_schemas() -> List[str]:
    """
    Retrieve a list of available schemas (users) in the database.

    Returns:
        List[str]: A list of schema/usernames.
    """
    
    return 

@mcp.tool(name='get_tables', description='Retrieve a list of table names for the given schema')
def get_tables(schema: str) -> List[str]:
    """
    Retrieve a list of table names for the given schema.

    Args:
        schema (str): The schema to list tables for.

    Returns:
        List[str]: A list of table names.
    """
    schema = schema.upper()
    query = """
        SELECT TABLE_NAME FROM ALL_TABLES 
        WHERE OWNER = :owner
    """
    with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, {"owner": schema})
            return [row[0] for row in cursor.fetchall()]

@mcp.tool(name='get_table_columns', description='Retrieve column metadata for given schema and table')
def get_table_columns(schema: str, table_name: str) -> List[Dict]:
    """
    Retrieve column metadata for a given table.

    Args:
        schema (str): The schema the table belongs to.
        table_name (str): The table to inspect.

    Returns:
        List[Dict]: A list of dictionaries containing column metadata:
                    column_name, data_type, is_nullable, column_default.
    """
    schema, table_name = schema.upper(), table_name.upper()
    query = """
        SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT 
        FROM ALL_TAB_COLUMNS 
        WHERE OWNER = :owner AND TABLE_NAME = :table_name 
        ORDER BY COLUMN_ID
    """
    with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, {"owner": schema, "table_name": table_name})
            return [
                {
                    "column_name": row[0],
                    "data_type": row[1],
                    "is_nullable": "YES" if row[2] == "Y" else "NO",
                    "column_default": row[3]
                }
                for row in cursor.fetchall()
            ]
        
if __name__ == "__main__":
    mcp.run(transport='sse')
    # print('a')