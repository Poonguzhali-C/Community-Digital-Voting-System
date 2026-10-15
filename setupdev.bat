@echo off
echo Setting up backend...
cd backend
python -m venv env
call env\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
cd ..
echo Setting up frontend...
cd frontend
call npm install
cd ..
echo Setup complete.
