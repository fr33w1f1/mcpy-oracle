from fastmcp import FastMCP
# from mcp.server.fastmcp import FastMCP
import oracledb
import random
import string
import logging
import os

from dotenv import load_dotenv
load_dotenv()

DWH_USERNAME = os.getenv("DWH_USERNAME")
DWH_PASSWORD = os.getenv("DWH_PASSWORD")
DSN = os.getenv("DSN")
COST_THRESHOLD = int(os.getenv("COST_THRESHOLD", 100000))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname:<8} {message}",
    datefmt="%m/%d/%y %H:%M:%S",  # MM/DD/YY
    style="{"
    )

mcp = FastMCP("oracle_mcp_server")

@mcp.tool(name="execute_sql", description="Executes an SQL query on the Oracle Database")
def execute_sql(sqlString: str):
    """
    Execute a SQL query against the Oracle database.

    Args:
        sqlString (str): The SQL query to execute

    Returns:
        List[dict]: Query results as JSON (list of rows)
    """
    try:
        with oracledb.connect(user=DWH_USERNAME, password=DWH_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sqlString)
                rows = cursor.fetchmany()
                headers = [col[0] for col in cursor.description]
                return [dict(zip(headers, row)) for row in rows]
    except Exception as e:
        # logger.exception(f"An unexpected error occurred: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_schemas", description="Retrieve a list of available schemas (users) in the database")
def get_schemas():
    """
    Retrieve a list of available schemas (users) in the database.

    Returns:
        List[dict]: Schemas as JSON
    """
    query = "SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME"
    try:
        with oracledb.connect(user=DWH_USERNAME, password=DWH_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [{"schema": row[0]} for row in rows]
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_tables", description="Retrieve a list of table names for the given schema")
def get_tables(schema: str):
    """
    Retrieve a list of table names for the given schema.

    Args:
        schema (str): The schema to list tables for.

    Returns:
        List[dict]: Table names as JSON
    """
    schema = schema.upper()
    query = """
        SELECT TABLE_NAME FROM ALL_TABLES 
        WHERE OWNER = :schema
    """
    try:
        with oracledb.connect(user=DWH_USERNAME, password=DWH_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"schema": schema})
                rows = cursor.fetchall()
                return [{"table_name": row[0]} for row in rows]
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_table_metadata", description="Retrieve column metadata for given schema and table")
def get_table_metadata(schema: str, table_name: str):
    """
    Retrieve column metadata for a given table.

    Args:
        schema (str): Schema name
        table_name (str): Table name

    Returns:
        List[dict]: Column metadata as JSON
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
        END AS IS_PARTITION_KEY,
        CASE 
            WHEN subpart.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO'
        END AS IS_SUBPARTITION_KEY
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
    LEFT JOIN 
        ALL_SUBPART_KEY_COLUMNS subpart
        ON col.OWNER = subpart.OWNER
        AND col.TABLE_NAME = subpart.NAME
        AND col.COLUMN_NAME = subpart.COLUMN_NAME
    WHERE 
        col.OWNER = :schema
        AND col.TABLE_NAME = :table_name
    """
    try:
        with oracledb.connect(user=DWH_USERNAME, password=DWH_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, {"schema": schema, "table_name": table_name})
                rows = cursor.fetchmany()
                headers = [col[0] for col in cursor.description]
                return [dict(zip(headers, row)) for row in rows]
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {"error": str(e)}
    

@mcp.tool(name="validate_and_estimate_cost", description="Validates an SQL query and returns its execution plan with cost.")
def validate_and_estimate_cost(query: str):
    """
    Validates an SQL query, retrieves its execution plan, and prints the estimated cost.

    Args:
        query (str): The SQL query to analyze.

    Returns:
        dict: Execution plan and cost as JSON
    """
    statement_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    try:
        with oracledb.connect(user=DWH_USERNAME, password=DWH_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"EXPLAIN PLAN SET STATEMENT_ID = '{statement_id}' FOR {query}")

                cursor.execute(f"SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, '{statement_id}', 'TYPICAL'))")
                plan_output = [row[0] for row in cursor.fetchall()]

                cursor.execute("""
                    SELECT COST
                    FROM PLAN_TABLE
                    WHERE STATEMENT_ID = :statement_id AND ID = 0
                """, {'statement_id': statement_id})

                cost_result = cursor.fetchone()
                cost = int(cost_result[0]) if cost_result and cost_result[0] is not None else 0

                if cost > COST_THRESHOLD:
                    logger.warning(f"The estimated cost of this query is {cost}, which may impact database performance.")

                return {
                    "execution_plan": plan_output,
                    "estimated_cost": cost
                }

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {"error": str(e)}

        
if __name__ == "__main__":
    mcp.run()
