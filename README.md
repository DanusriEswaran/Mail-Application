Frontend installation:
cd mail-application #folder which contains both frontend and backend
npm create vite@latest frontend
cd frontend
npm install
npm run dev
npm install @mui/material @emotion/react @emotion/styled 
npm install @mui/icons-material

Backend installation
#created a folder as 'backend'
cd backend
python -m venv venv
venv\Scripts\Activate 
pip install "fastapi[standard]" uvicorn 
pip install psycopg2-binary #for postgreSQL
pip install -r requirements.txt
#created a main.py file
uvicorn main:app --reload 
