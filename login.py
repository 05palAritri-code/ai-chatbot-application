from langgraph.checkpoint.postgres import PostgresSaver

DB_URL = 'postgresql://postgres:supabasedatabase@db.xcvmvohbenxdwfzposun.supabase.co:5432/postgres?sslmode=require'

checkpointer = PostgresSaver.from_conn_string(DB_URL)

print(type(checkpointer))