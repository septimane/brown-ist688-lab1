import streamlit as st

lab1 = st.Page("Labs/Lab1.py", title="Lab 1")
lab2 = st.Page("Labs/Lab2.py", title="Lab 2")
lab3 = st.Page("Labs/Lab3.py", title="Lab 3", default=True)
pg = st.navigation([lab3, lab2, lab1])
pg.run()