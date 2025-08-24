# nova 🚀

**nova** is a modern boilerplate for FastAPI projects, designed to provide a robust, fast, and efficient base using:

- [FastAPI](https://fastapi.tiangolo.com/) – High-performance Python web framework
- [Uvicorn](https://www.uvicorn.org/) – Lightweight ASGI server
- [SQLModel](https://sqlmodel.tiangolo.com/) – ORM and data modeling built on SQLAlchemy & Pydantic
- [uv](https://github.com/astral-sh/uv) – Super-fast Python package manager

> **Note:** This project uses `uv sync` to install dependencies from `pyproject.toml` for speed and reliability. Do **not** use `uv pip install ...`!

---

## Getting Started 🚀

1. **Clone the project:**

   ```bash
   git clone https://github.com/ThiagoVRabethge/nova.git
   cd nova
   ```

2. **Install uv globally (if not already installed):**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh // or powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Sync dependencies:**

   ```bash
   uv sync
   ```

   > **Important:** Always use `uv sync` to install dependencies. This ensures all packages in `pyproject.toml` are installed correctly.

4. **Run the development server:**

   ```bash
   uvicorn src.main:app --reload
   ```

---

## Main Dependencies

- `fastapi`
- `uvicorn`
- `sqlmodel`
- `uv` (for package management)

---

## Useful Commands

- **Sync dependencies:**  
  `uv sync`

- **Add a new dependency:**  
  `uv add package-name`  
  (this automatically updates `pyproject.toml`!)

- **Run the server:**  
  `uvicorn src.main:app --reload`

---

## Notes

- Always manage your dependencies with `uv` for best performance and compatibility.
- The `pyproject.toml` file is the central config for dependencies and project settings.

---

## License

This project is under the MIT license. Feel free to use and contribute!

---

## Author

**ThiagoVRabethge**

---

> Build fast, modern Python APIs easily and reliably with nova! 😄
