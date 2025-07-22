from fastmcp import FastMCP
import oracledb
from tabulate import tabulate
import random
import string
import logging

from config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname:<8} {message}",
    datefmt="%m/%d/%y %H:%M:%S",  # MM/DD/YY
    style="{"
    )

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

@mcp.tool(name='get_table_metadata', description='Retrieve column metadata for given schema and table')
def get_table_metadata(schema: str, table_name: str) -> str:
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
        SELECT 
            col.COLUMN_NAME,
            col.DATA_TYPE,
            col.DATA_LENGTH,
            col.NULLABLE,
            col.NUM_DISTINCT,
            col.NUM_NULLS,
            CASE 
                WHEN idx.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO'
            END AS IS_INDEXED,
            CASE 
                WHEN part.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO'
            END AS IS_PARTITION_KEY
        FROM 
            ALL_TAB_COLUMNS col
        LEFT JOIN 
            ALL_IND_COLUMNS idx
            ON col.OWNER = idx.TABLE_OWNER
            AND col.TABLE_NAME = idx.TABLE_NAME
            AND col.COLUMN_NAME = idx.COLUMN_NAME
        LEFT JOIN 
            ALL_PART_KEY_COLUMNS part
            ON col.OWNER = part.OWNER
            AND col.TABLE_NAME = part.NAME
            AND col.COLUMN_NAME = part.COLUMN_NAME
        WHERE 
            col.OWNER = :schema
            AND col.TABLE_NAME = :table_name
        ORDER BY 
            col.COLUMN_ID
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
    
@mcp.tool(name='Validate query and get explain with cost', description='Validates an SQL query and returns its execution plan with cost.')
def validate_and_estimate_cost(query: str) -> str:
    """
    Validates an SQL query, retrieves its execution plan, and prints the estimated cost.

    A warning is issued if the cost exceeds a predefined threshold.

    Args:
        query (str): The SQL query to analyze.

    Returns:
        str: A markdown-formatted table of the execution plan, or an error message.
    """
    # Generate a unique statement ID for this explain plan
    statement_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    try:
        with oracledb.connect(user=settings.username, password=settings.password, dsn=settings.dsn) as connection:
            with connection.cursor() as cursor:
                # Explain the plan for the given query with a specific statement ID
                cursor.execute(f"EXPLAIN PLAN SET STATEMENT_ID = '{statement_id}' FOR {query}")

                # Retrieve the formatted plan using the statement ID
                cursor.execute(f"SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, '{statement_id}', 'TYPICAL'))")
                plan_output = cursor.fetchall()
                
                # Now, let's get the cost from the plan_table for our statement_id
                cursor.execute("""
                    SELECT COST
                    FROM PLAN_TABLE
                    WHERE STATEMENT_ID = :statement_id AND ID = 0
                """, {'statement_id': statement_id})

                cost_result = cursor.fetchone()
                cost = 0
                if cost_result and cost_result[0] is not None:
                    cost = int(cost_result[0])

                if cost > settings.cost_threshold:
                    logger.warning(f"The estimated cost of this query is {cost}, which may impact database performance.")

                return tabulate(plan_output, headers=["Execution Plan"], tablefmt="github")
    except oracledb.DatabaseError as e:
        # If the query is invalid during the EXPLAIN PLAN, an error will be raised.
        return f"Error: Invalid SQL query. {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

        
if __name__ == "__main__":
    mcp.run()
