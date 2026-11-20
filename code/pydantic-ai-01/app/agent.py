
import os
import json
import sqlite3
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
import logfire


logfire.configure(
    send_to_logfire=False,
    console=logfire.ConsoleOptions(
        span_style="indented",
        verbose=True
    )
)


logfire.instrument_pydantic_ai()

# --------------------------------------------------
# Database setup
# --------------------------------------------------

DB_NAME = "orders.db"


def initialize_database():
    """Create SQLite database and insert sample orders."""

    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    """)

    # Insert sample data only when the table is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    if count == 0:
        sample_orders = [
            (1001, "John", "Laptop", 1, 75000, "Shipped", "2026-11-10"),
            (1002, "Alice", "Mobile", 2, 40000, "Pending", "2026-11-12"),
            (1003, "Bob", "Headphones", 1, 5000, "Delivered", "2026-11-13"),
            (1004, "John", "Keyboard", 2, 3000, "Processing", "2026-11-15"),
            (1005, "Alice", "Monitor", 1, 18000, "Shipped", "2026-11-16"),
        ]

        conn.executemany("""
            INSERT INTO orders
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_orders)

        conn.commit()

    return conn


# --------------------------------------------------
# Agent dependencies
# --------------------------------------------------

@dataclass
class OrderDependencies:
    db: sqlite3.Connection
    customer_name: str | None = None


# --------------------------------------------------
# Create Pydantic AI agent
# --------------------------------------------------

order_agent = Agent(
    "groq:openai/gpt-oss-120b",
    deps_type=OrderDependencies,
    instructions="""
    You are an order support assistant.

    Your job is to answer questions about customer orders.

    Guidelines:
    - Use the available tools to retrieve order information.
    - Never invent order details.
    - If an order does not exist, clearly say so.
    - If the user asks about a customer's orders,
      retrieve the relevant orders using the tools.
    - Explain order status in simple language.
    - Use the actual data returned by the database.
    - Do not assume that an order is delivered or shipped
      unless the database confirms it.
    """
)

# --------------------------------------------------
# Agent Instructions
# --------------------------------------------------

@order_agent.instructions
def add_customer_context(
    ctx: RunContext[OrderDependencies]
) -> str:

    if ctx.deps.customer_name:
        return f"""
        The currently logged-in customer is
        {ctx.deps.customer_name}.

        Response formatting:
        - Start every response with "Hello {ctx.deps.customer_name},"
        - Follow the greeting with the actual answer.
        - Do not repeat the greeting within the same response.

        When the customer asks about their orders,
        assume they are referring to their own orders
        unless they explicitly mention another customer.

        Do not reveal another customer's order information.
        """

    return """
    No customer is currently logged in.

    You are assisting a general support user.
    Ask for the customer name when necessary.
    Do not use a personalized greeting.
    """

# --------------------------------------------------
# Agent tools
# --------------------------------------------------

@order_agent.tool
def get_order(
    ctx: RunContext[OrderDependencies],
    order_id: int
) -> str:
    """
    Retrieve details of a specific order using its order ID.
    """

    cursor = ctx.deps.db.execute("""
        SELECT *
        FROM orders
        WHERE order_id = ?
    """, (order_id,))

    order = cursor.fetchone()

    if order is None:
        return json.dumps({
            "error": f"Order {order_id} was not found."
        })

    return json.dumps(dict(order))


@order_agent.tool
def get_customer_orders(
    ctx: RunContext[OrderDependencies],
    customer_name: str
) -> str:
    """
    Retrieve all orders placed by a specific customer.
    """

    cursor = ctx.deps.db.execute("""
        SELECT *
        FROM orders
        WHERE LOWER(customer_name) = LOWER(?)
        ORDER BY order_date DESC
    """, (customer_name,))

    orders = [dict(row) for row in cursor.fetchall()]

    return json.dumps(orders)








# --------------------------------------------------
# Main application
# --------------------------------------------------

def main():

    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is missing in .env")

    db = initialize_database()

    deps = OrderDependencies(db=db, customer_name="John")

    print("\nOrder Assistant Agent")
    print("---------------------")
    print("Ask questions about customer orders.")
    print("Type 'exit' to quit.\n")

    try:
        while True:

            question = input("You: ").strip()

            if question.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if not question:
                continue

            try:
                result = order_agent.run_sync(
                    question,
                    deps=deps
                )

                print(f"\nAssistant: {result.output}\n")

            except Exception as e:
                print(f"\nError: {e}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
