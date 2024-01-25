from langchain.agents import create_sql_agent
# from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
# from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Load environment variables
server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
schema = os.getenv("SCHEMA")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def connect_to_sql_server(server, database, username, password, schema):
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server")

        # Create the SQLDatabase object
        db = SQLDatabase(engine)

        return db
    except Exception as e:
        print(f"Error connecting to SQL Server: {e}")
        return None

# Connect to the SQL Server
sql_db = connect_to_sql_server(server, database, username, password, schema)

# Check if the connection was successful
if sql_db:
    try:
        # Now you can use the 'sql_db' object to interact with the SQL Server
        print("Connected to SQL Server")
        # print("Table names:", sql_db.get_table_names())
        print("Table names:", sql_db.get_usable_table_names())
    except Exception as e:
        print(f"Error interacting with SQL Server: {e}")
else:
    print("Failed to connect to SQL Server")

# Set up OpenAI ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
        you are a very intelligent AI assistant who is an expert in identifying relevant questions from users 
        and converting them into SQL queries to generate correct answers.
        Please use the below context to write the Microsoft SQL queries, don't use MySQL queries.
       context:
       you must query against the connected database, it has a total of 2 tables, these are [dbo].[DatadashProducts] and [dbo].[DatadashOrders].
       [dbo].[DatadashOrders] table has ID, ApiConnectionId, OrderId, OrderItemId, ProductTitle, ProductEan, Quantity, QuantityShipped, QuantityCancelled,
       Unitprice, Commission, AvgOrderValue, Sales, OrderValue, Date, OrderPlacedDateTime, Time, Year, Month, Day, WeekOfMonth, WeekOfYear, NetSellerAmount, PeriodOfDay,
       PeriodOfDayOrderID columns. It gives the order information.
       [dbo].[DatadashProducts] table has ID, UserTenantId, ApiConnectionsId, ApiConnectionName, ApiConnectionDefId, ProductId, ProductName, ProductEAN, ProductCreatedOn,
       ProductlastModifiedOn, ProductTimeStam, ProductStock, ProductBasePrice, ProductProjectId columns. It gives the product-specific information.
   
       As an expert, you must use joins whenever required.
        """
        ),
        ("user", "{question}\ ai: ")
    ]
)

# Set up OpenAI ChatOpenAI
llm = ChatOpenAI(temperature=0.0, model="gpt-4", api_key=OPENAI_API_KEY)
sql_toolkit = SQLDatabaseToolkit(db=sql_db, llm=llm)
sql_toolkit.get_tools()

# Set up SQL agent
agent = create_sql_agent(llm=llm, toolkit=sql_toolkit, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True,
                         max_execution_time=100, max_iterations=1000)

# Streamlit UI
st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("SQL DB Application")

question = st.text_input("Input: ", key="input")
submit = st.button("Ask the question")


# If ask button is clicked
if submit:
    print("User Input:", question)  # Print user input for debugging
    response = agent.run(prompt.format_prompt(question=question))
    print("Agent Response:", response)  # Print agent response for debugging
    st.subheader("The Response is")
    
    # Join each element in the response list with spaces
    result_sentence = ' '.join(' '.join(word) for word in response)
    
    st.write(result_sentence)



