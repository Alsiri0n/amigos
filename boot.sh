#!/bin/bash
exec source venv/bin/activate
alembic upgrade head
exec python main.py