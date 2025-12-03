# 📚 Library Desk Agent

A local AI-powered Library Assistant that can search books, manage orders, update inventory, and interact with a SQLite database — using natural-language chat.

Built using:
- Streamlit (Frontend)
- LangChain (Agent)
- Ollama / OpenAI (LLM)
- SQLite (Database)
- Python (Backend tools)

---

## 🚀 Features

- Natural-language search & commands
- Local LLM support (Ollama)
- Optional OpenAI API support
- Manage customer orders
- Adjust stock & prices
- Auto logging: messages + tool calls
- Multi-folder clean architecture

---

## 📦 Project Structure


-app/
-app.py
-server/
-init.py
-agent_tools.py
-chat_storage.py
-db.py
-library_agent.py
-db/
-schema.sql
-seed.sql
-LibraryAg.db
-prompt/
-system_prompt.txt
-.env.example
-requirements.txt
-README.md

---

## 🛠️ Installation

### 1. Clone the repo

-git clone <repo_url>
-cd <repo_folder>



### 2. Install dependencies

- pip install -r requirements.txt


---

## 🤖 Using Ollama (Local LLM)

-Download Ollama:
-https://ollama.com/download

-Then pull a model:
-ollama pull llama3



---

## ▶️ Run the App

-Launch UI:
-streamlit run app.py
-App opens at:
-http://localhost:8501

---

## 🧠 Agent Tools

| Tool | What it does |
|------|--------------|
| find_books | Search books by author/title |
| create_order | Create order + reduce stock |
| restock_book | Increase inventory |
| update_price | Modify book price |
| order_status | Show order summary |
| inventory_summary | Show low-stock books |

---

## 📝 Example Prompts
-Find books written by John
-Add 3 copies to ISBN 978000000002
-Create order for customer Ahmed email ah@ex.com 3 copies of ISBN 978000000001


---

## 📜 License
MIT License
