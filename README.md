# ⚙️ MCP Server for Oracle

## ⏰ When to use
When somebody has MCP client/host and wants to connect to your Oracle database in "MCP" way

## ❓ What is it
FastAPI with different syntax

## 🚀 How to use
Just open `app.py` and copy the code you need. Or:

### 🖥️ Window
Install `uv` and packages:
```bash
.\install.bat
```
Run MCP Server:
```bash
.\start.bat
```
To stop, press `Ctrl + C` and `Y` if required

Or install manually: 

Clone this repo to your machine:
```bash
git clone https://github.com/fr33w1f1/mcpy-oracle
cd mcpy-oracle
```

Install `uv` (or use `conda`)
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Create and use virtual env
```bash
uv venv --python 3.12
.\.venv\Scripts\activate
```
Install requirements
```bash 
uv pip install -r requirements.txt 
```
Create `.env` with these 3:
```
USERNAME=
PASSWORD=
DSN=HOST:PORT/SERVICENAME
```

(Optional) If you want to change the transport/host/port:
```python
#sse
mcp.run(transport='sse', host='0.0.0.0', port=8000)
#STDIO is the default transport, so you don’t need to specify it when calling run()
mcp.run(transport='stdio')
#http-streamable
mcp.run(transport='streamable-http', host='0.0.0.0', port=8000)
```

Start MCP server
```
python -m app
```

### 🐧 Linux

## 🛠 MCP tools
```python
def execute_sql(sqlString: str) -> str
    """
    Execute a SQL query against the Oracle database.
    """

def get_schemas() -> str
    """
    Retrieve a list of available schemas (users) in the database.
    """

def get_tables(schema: str) -> str
    """
    Retrieve a list of table names for the given schema.
    """

def get_table_columns(schema: str, table_name: str) -> str
    """
    Retrieve column metadata for a given table.
    """

def validate_and_estimate_cost(query: str) -> str
    """
    Validates an SQL query, retrieves its execution plan, and prints the estimated cost.
    """
```

### Optional: Expose you MCP outside your local network using `ngrok`

## MCP Inspector to test your tools
Install npx

```bash
npx @modelcontextprotocol/inspector uv --directory "D:\sourcecode\mcpy_server" run -m mcpy_server.app
```
