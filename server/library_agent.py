import json
from typing import Dict, Any

from langchain_ollama import ChatOllama

from agent_tools import (
    find_books,
    create_order,
    restock_book,
    update_price,
    order_status,
    inventory_summary,
    add_customer,
)
from chat_storage import log_tool_call

# ==========Prepare the LLM ==========
llm = ChatOllama(
    model="llama3",  
    temperature=0,
)

# ========== SYSTEM PROMPT ==========
TOOLS_DESCRIPTION = """
You are a Library Desk Agent that can call backend functions (tools) that interact with a SQLite database.

You MUST decide which single action to perform for each user request.
Return ONLY a valid JSON object with no extra text, in this exact format:

{
    "action": "<one of: find_books | create_order | restock_book | update_price | order_status | inventory_summary | none>",
    "args": { ... }
}

Tools you can use:

1) find_books
    - Use when the user wants to search for books by title or author.
    - Args:
        {
        "q": "<search text>",
        "by": "title" or "author"
        }

2) create_order
    - Use when the user wants to create a new order for a customer.
    - Args:
        {
         "customer_id": <integer>,      // If unknown, use 0
        "name": "<customer name>",
        "email": "<customer email>",
        "items": [
            { "isbn": "<book isbn>", "qty": <integer> },
            ...
        ]
        }

3) restock_book
    - Use when the user wants to increase stock of a book.
    - Args:
        {
        "isbn": "<book isbn>",
        "qty": <integer>
        }

4) update_price
    - Use when the user wants to change the price of a book.
    - Args:
        {
        "isbn": "<book isbn>",
        "price": <float>
        }

5) order_status
    - Use when the user asks about details of an order.
    - Args:
        {
        "order_id": <integer>
        }

6) inventory_summary
    - Use when the user wants to know which books have low stock or get an inventory summary.
    - Args: { }

7) add_customer 
    - add new customers to the customer table
    
8) none
    - Use when the question does NOT need any database tool (for example, a casual greeting like "hello").

Important:
- ALWAYS return a single JSON object.
- NEVER return explanations or surrounding text.
- If you need clarification, still choose the most likely tool and arguments.
"""

# ========== Decide Which action ==========
def decide_action(user_message: str) -> Dict[str, Any]:
    """
    Ask the LLM which action+args to use.
    LLM must return pure JSON. We parse it here.
    """
    prompt = TOOLS_DESCRIPTION + f'\n\nUser message:\n"{user_message}"\n\nJSON:'

    response = llm.invoke(prompt)
    content = response.content

    # Clean the content
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        data = json.loads(content)
        return data
    except Exception as e:
        # none
        print("JSON parse error from LLM:", e)
        print("Raw content:", content)
        return {"action": "none", "args": {}}


# ========== Backend excution ==========
def execute_action(action: str, args: Dict[str, Any], session_id: int | None = None) -> Any:
    if action == "find_books":
        q = args.get("q", "")
        by = args.get("by", "title")
        result = find_books(q=q, by=by)

    elif action == "create_order":
        customer_id = int(args.get("customer_id", 0))
        name = args.get("name", "")
        email = args.get("email", "")
        items = args.get("items", [])
        result = create_order(customer_id=customer_id, name=name, email=email, items=items)

    elif action == "restock_book":
        isbn = args.get("isbn", "")
        qty = int(args.get("qty", 0))
        result = restock_book(isbn=isbn, qty=qty)

    elif action == "update_price":
        isbn = args.get("isbn", "")
        price = float(args.get("price", 0.0))
        result = update_price(isbn=isbn, price=price)

    elif action == "order_status":
        order_id = int(args.get("order_id", 0))
        result = order_status(order_id=order_id)

    elif action == "inventory_summary":
        result = inventory_summary()

    else:
        result = None

    if action not in ("none", "") and result is not None and session_id is not None:
        log_tool_call(session_id=session_id, name=action, args=args, result=result)

    return result



# ========== Final answer ==========
def build_final_answer(user_message: str, action: str, args: Dict[str, Any], result: Any) -> str:
    
    # No tool:
    if action == "none" or result is None:
        response = llm.invoke(
            f"You are a friendly Library Desk Agent. Answer this user message directly:\n\n{user_message}"
        )
        return response.content

    # tool:
    result_text = json.dumps(result, ensure_ascii=False, indent=2)

    final_prompt = f"""
You are a helpful Library Desk Agent.

The user asked:
{user_message}

You chose to call the tool: {action}
with arguments:
{json.dumps(args, ensure_ascii=False)}

The tool returned this data (JSON):
{result_text}

Now, write a clear and friendly answer to the user explaining this result.
If the user speaks Arabic, you can answer in Arabic (with technical terms in English if needed).
"""

    response = llm.invoke(final_prompt)
    return response.content


# ========== Run Agent ==========
def run_agent(user_message: str, session_id: int | None = None) -> str:

    decision = decide_action(user_message)
    action = decision.get("action", "none")
    args = decision.get("args", {})

    print("DEBUG - LLM decision:", decision)

    result = execute_action(action, args, session_id=session_id)

    answer = build_final_answer(user_message, action, args, result)
    return answer



# ========== Promot UI ==========
if __name__ == "__main__":
    print("📚 Library Desk Agent type 'exit' to quit.\n")

    # Fixed session_id
    test_session_id = 999

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            reply = run_agent(user_input, session_id=test_session_id)
            print("Agent:", reply)
        except Exception as e:
            print("Error:", e)

