import os
import pandas as pd
import streamlit as st
import plotly.express as px

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv


# 1. Configure the dashboard
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🎓",
    layout="wide"
)


# 2. Connect to MySQL
def get_engine():

    load_dotenv()

    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")

    password = quote_plus(
        os.getenv("MYSQL_PASSWORD", "")
    )

    database = os.getenv(
        "MYSQL_DATABASE",
        "student_analytics"
    )

    connection_url = (
        f"mysql+pymysql://{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True
    )


# 3. Create a reusable SQL function
def read_sql(engine, query, params=None):

    with engine.connect() as connection:

        return pd.read_sql(
            text(query),
            connection,
            params=params or {}
        )


# 4. Dashboard title
st.title("🎓 Student Performance Analytics")

st.caption(
    "Academic insights powered by Python, MySQL and Streamlit"
)


# 5. Check database connection
try:

    engine = get_engine()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

except Exception as error:

    st.error(
        "MySQL connection failed. "
        "Check your .env file and MySQL server."
    )

    st.code(str(error))
    st.stop()


# 6. Check whether records exist
count = read_sql(
    engine,
    "SELECT COUNT(*) AS n FROM students"
).iloc[0]["n"]

if count == 0:

    st.warning(
        "No student data found. "
        "Run the cleaning and loading scripts first."
    )

    st.stop()


# 7. Department filter
departments = read_sql(
    engine,
    """
    SELECT DISTINCT department
    FROM students
    ORDER BY department
    """
)

options = (
    ["All Departments"]
    + departments["department"].tolist()
)

selected = st.sidebar.selectbox(
    "Select Department",
    options
)

where = ""
params = {}

if selected != "All Departments":

    where = "WHERE department = :department"

    params["department"] = selected


# 8. Calculate dashboard KPIs
kpi_query = f"""
SELECT
COUNT(*) AS total_students,

ROUND(
    AVG((math_marks + science_marks + english_marks) / 3),
    2
) AS avg_marks,

ROUND(
    AVG(attendance),
    2
) AS avg_attendance,

ROUND(
    100 * AVG(
        CASE
        WHEN (math_marks + science_marks + english_marks) / 3 >= 40
        THEN 1
        ELSE 0
        END
    ),
    2
) AS pass_rate

FROM students
{where}
"""

kpi = read_sql(
    engine,
    kpi_query,
    params
).iloc[0]


# 9. Display KPI cards
st.subheader("Key Performance Indicators")

a, b, c, d = st.columns(4)

a.metric(
    "Total Students",
    int(kpi["total_students"])
)

b.metric(
    "Average Marks",
    f'{kpi["avg_marks"]:.2f}/100'
)

c.metric(
    "Average Attendance",
    f'{kpi["avg_attendance"]:.2f}%'
)

d.metric(
    "Pass Percentage",
    f'{kpi["pass_rate"]:.2f}%'
)


# 10. Department performance
department_query = f"""
SELECT
department,
ROUND(
    AVG((math_marks + science_marks + english_marks) / 3),
    2
) AS average_marks

FROM students
{where}

GROUP BY department
ORDER BY average_marks DESC
"""

department_data = read_sql(
    engine,
    department_query,
    params
)


# 11. Subject performance
subject_query = f"""
SELECT
'Maths' AS subject,
ROUND(AVG(math_marks), 2) AS average_marks
FROM students
{where}

UNION ALL

SELECT
'Science',
ROUND(AVG(science_marks), 2)
FROM students
{where}

UNION ALL

SELECT
'English',
ROUND(AVG(english_marks), 2)
FROM students
{where}
"""

subject_data = read_sql(
    engine,
    subject_query,
    params
)


# 12. Top five students
top_query = f"""
SELECT
student_id,
student_name,
department,

ROUND(
    (math_marks + science_marks + english_marks) / 3,
    2
) AS average_marks,

attendance

FROM students
{where}

ORDER BY average_marks DESC
LIMIT 5
"""

top_students = read_sql(
    engine,
    top_query,
    params
)


# 13. Students requiring support
risk_query = f"""
SELECT
student_id,
student_name,
department,
attendance,

ROUND(
    (math_marks + science_marks + english_marks) / 3,
    2
) AS average_marks

FROM students

{where}

{"AND" if where else "WHERE"}

(
    attendance < 75
    OR
    (math_marks + science_marks + english_marks) / 3 < 40
)

ORDER BY average_marks
"""

risk_students = read_sql(
    engine,
    risk_query,
    params
)


# 14. Display charts
st.divider()

st.subheader("Performance Analysis")

left, right = st.columns(2)

with left:

    fig1 = px.bar(
        department_data,
        x="department",
        y="average_marks",
        title="Average Marks by Department",
        text_auto=True
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )


with right:

    fig2 = px.bar(
        subject_data,
        x="subject",
        y="average_marks",
        title="Average Marks by Subject",
        text_auto=True
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# 15. Display student tables
st.subheader("Top 5 Students")

st.dataframe(
    top_students,
    use_container_width=True,
    hide_index=True
)


st.subheader("Students Requiring Support")

st.caption(
    "Students are flagged if average marks are below 40 "
    "or attendance is below 75%."
)

st.dataframe(
    risk_students,
    use_container_width=True,
    hide_index=True
)


# 16. Download report
all_query = f"""
SELECT
student_id,
student_name,
department,
math_marks,
science_marks,
english_marks,
attendance,

ROUND(
    (math_marks + science_marks + english_marks) / 3,
    2
) AS average_marks

FROM students
{where}
ORDER BY student_id
"""

all_data = read_sql(
    engine,
    all_query,
    params
)

st.download_button(
    "Download Student Report",
    all_data.to_csv(index=False).encode("utf-8"),
    "student_performance_report.csv",
    "text/csv"
)