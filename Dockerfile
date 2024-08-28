FROM python

WORKDIR /LPP-solver

COPY ./LPP_Solver.py .

COPY ./requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "LPP_Solver.py"]

