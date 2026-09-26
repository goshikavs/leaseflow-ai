from app.mcp.servers.runtime import build_server

mcp = build_server("leasing")

if __name__ == "__main__":
    mcp.run(transport="stdio")
