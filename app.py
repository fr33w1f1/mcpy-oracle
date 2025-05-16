from mcp.server.fastmcp import FastMCP
import oracledb
from tabulate import tabulate

from config.config import settings

mcp = FastMCP("oracle_mcp_server")

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
        str: Markdown-formatted table containing query results
    """
    try:
        with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sqlString)
                rows = cursor.fetchmany(settings.query_limit_size)
                headers = [col[0] for col in cursor.description]
                return tabulate(rows, headers=headers, tablefmt="github")
    except Exception as e:
        return f"Error: {str(e)}"
    
@mcp.tool(name='get_schemas', description="Retrieve a list of available schemas (users) in the database")
def get_schemas() -> str:
    """
    Retrieve a list of available schemas (users) in the database.

    Returns:
        str: Markdown table of schemas
    """
    query = "SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME"
    try:
        with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return tabulate(rows, headers=["Schema"], tablefmt="github")
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool(name='get_tables', description='Retrieve a list of table names for the given schema')
def get_tables(schema: str) -> str:
    """
    Retrieve a list of table names for the given schema.

    Args:
        schema (Optional[str]): The schema to list tables for. Defaults to current schema.

    Returns:
        str: Markdown table of table names
    """
    schema = schema.upper()
    query = f"""
        SELECT TABLE_NAME FROM ALL_TABLES 
        WHERE OWNER = :schema
    """
    try:
        with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"schema": schema})
                rows = cursor.fetchall()
                return tabulate(rows, headers=["Table Name"], tablefmt="github")
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool(name='get_table_columns', description='Retrieve column metadata for given schema and table')
def get_table_columns(schema: str, table_name: str) -> str:
    """
    Retrieve column metadata for a given table.

    Args:
        table_name (str): The table to inspect.
        schema (Optional[str]): The schema the table belongs to. Defaults to current schema.

    Returns:
        str: Markdown-formatted table containing column metadata
    """
    schema, table_name = schema.upper(), table_name.upper()
    query = """
        SELECT COLUMN_NAME, DATA_TYPE, NUM_DISTINCT, NUM_NULLS, NULLABLE
        FROM ALL_TAB_COLUMNS 
        WHERE OWNER = :schema AND TABLE_NAME = :table_name 
    """
    try:
        with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"schema": schema, "table_name": table_name})
                rows = cursor.fetchmany(settings.query_limit_size)
                headers = [col[0] for col in cursor.description]
                return tabulate(rows, headers=headers, tablefmt="github")
    except Exception as e:
        return f"Error: {str(e)}"
        
if __name__ == "__main__":
    mcp.run(transport='sse')