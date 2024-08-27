import streamlit as st
from pulp import *

# Set up the page configuration
st.set_page_config(page_title="LPP Solver", page_icon="assets/optimization.ico", layout="wide")

# Page Title
st.title("LPP Solver Web-App")
st.write("This web application can solve linear programming problem including LP, IP(Integer Programming), MIP (Mixed Integer Programming).")

# Inputs for objective function, number of variables, and number of constraints
objective_function = st.text_input("Objective Function", placeholder="Enter the objective function here (e.g., 3x1 + 2x2)")

cols = st.columns(3)
num_vars = cols[0].text_input("Number of Variables", placeholder="Enter the number of variables as an integer", value="1")
num_constraints = cols[1].text_input("Number of Constraints", placeholder="Enter the number of constraints as an integer", value="1")

# Choose between Maximization or Minimization
max_or_min = cols[2].selectbox("Maximization or Minimization", ["Maximization", "Minimization"])

# Convert number of variables and constraints to integers
try:
    num_vars = int(num_vars)
    num_constraints = int(num_constraints)
except ValueError:
    st.error("Please enter valid integers for the number of variables and constraints.")
    num_vars = 1
    num_constraints = 1

# Initialize session state for constraints and variable types
if "constraints" not in st.session_state:
    st.session_state.constraints = [""] * num_constraints
if "var_types" not in st.session_state:
    st.session_state.var_types = ["Float"] * num_vars
if "objective_coeffs" not in st.session_state:
    st.session_state.objective_coeffs = []
if "clean_constraints" not in st.session_state:
    st.session_state.clean_constraints = []
if "inequality_signs" not in st.session_state:
    st.session_state.inequality_signs = []
if "rhs_values" not in st.session_state:
    st.session_state.rhs_values = []
if "displayed_objective_function" not in st.session_state:
    st.session_state.displayed_objective_function = ""
if "displayed_constraints" not in st.session_state:
    st.session_state.displayed_constraints = []

# Function to update the length of constraints list
def update_constraints_list():
    if len(st.session_state.constraints) != num_constraints:
        st.session_state.constraints = [""] * num_constraints

# Function to update the length of variable types list
def update_var_types():
    if len(st.session_state.var_types) != num_vars:
        st.session_state.var_types = ["Float"] * num_vars

# Function to display variable type inputs
def display_variable_type_inputs():
    update_var_types()  # Ensure the var_types list has the correct length
    for i in range(num_vars):
        st.session_state.var_types[i] = st.selectbox(f"Variable {i + 1} Type", ["Integer", "Float"], key=f"var_type_{i}")

# Function to display constraint inputs with instructions
def display_constraint_inputs():
    update_constraints_list()  # Ensure the constraints list has the correct length
    for i in range(num_constraints):
        st.session_state.constraints[i] = st.text_input(
            f"Constraint {i + 1}",
            value=st.session_state.constraints[i],
            key=f"constraint_{i}",
            placeholder="Enter constraint (e.g., 2x1 + 3x2 <= 5)"
        )

# Display variable type inputs
display_variable_type_inputs()

# Display constraint inputs
display_constraint_inputs()

def parse_linear_expression(expr, num_vars):
    # Parse a linear expression into coefficients for each variable
    coefficients = [0] * num_vars
    temp_sign = "+"
    i = 0
    expr = expr.replace(" ", "")  # Remove spaces
    
    while i < len(expr):
        if expr[i] in "+-":
            temp_sign = expr[i]
            i += 1
            continue
        
        coefficient = ""
        while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
            coefficient += expr[i]
            i += 1
        
        if coefficient == "":
            coefficient = "1"
        elif coefficient == "-":
            coefficient = "-1"
        
        if i < len(expr) and expr[i] == 'x':
            i += 1
            var_number = ""
            while i < len(expr) and expr[i].isdigit():
                var_number += expr[i]
                i += 1
            
            if var_number == "":
                st.error(f"Variable number missing in expression: {expr}")
                continue
            
            coefficient = float(coefficient)
            num_var = int(var_number)
            
            if temp_sign == "-":
                coefficient = -coefficient

            if 1 <= num_var <= num_vars:
                coefficients[num_var - 1] += coefficient
            else:
                st.error(f"Variable number {num_var} is out of range.")
                continue
        else:
            st.error(f"Invalid format in expression: {expr}")
            continue
    
    return coefficients

# Button to submit objective function
if st.button("Submit Objective Function") and objective_function:
    st.session_state.objective_coeffs = parse_linear_expression(objective_function, num_vars)
    st.session_state.displayed_objective_function = objective_function

# Process constraints
if st.button("Submit Constraints"):
    st.session_state.clean_constraints = []
    st.session_state.inequality_signs = []
    st.session_state.rhs_values = []
    
    for raw_constraint in st.session_state.constraints:
        if not raw_constraint.strip():
            continue
        
        # Identify inequality sign and right-hand side value
        inequality_sign = None
        rhs_value = None
        
        for sign in ["<=", ">=", "="]:
            if sign in raw_constraint:
                parts = raw_constraint.split(sign)
                if len(parts) == 2:
                    inequality_sign = sign
                    rhs_value = float(parts[1].strip())
                    raw_constraint = parts[0].strip()  # Left-hand side expression
                break
        
        if inequality_sign is None or rhs_value is None:
            st.error(f"Inequality sign or RHS value missing in constraint: {raw_constraint}")
            continue

        constraint_coeffs = parse_linear_expression(raw_constraint, num_vars)
        st.session_state.clean_constraints.append(constraint_coeffs)
        st.session_state.inequality_signs.append(inequality_sign)
        st.session_state.rhs_values.append(rhs_value)

    st.session_state.displayed_constraints = st.session_state.constraints

# Display Objective Function and Constraints
st.subheader("Objective Function")
if st.session_state.displayed_objective_function:
    st.write(f"Z = {st.session_state.displayed_objective_function}")

st.subheader("Constraints")
for i, constraint in enumerate(st.session_state.displayed_constraints):
    st.write(f"Constraint {i + 1}: {constraint}")

# Define and solve the Linear Programming Problem
if st.button("Solve Problem") and st.session_state.objective_coeffs:
    # Define the Linear Programming Problem based on whether it is a maximization or minimization problem
    if max_or_min == "Maximization":
        linear_program = LpProblem("Maximization Problem", LpMaximize)
    else:
        linear_program = LpProblem("Minimization Problem", LpMinimize)

    # Initialize the dictionary for variables
    vars = {}

    # Loop over each variable to define its type (Integer or Float)
    for i in range(num_vars):
        var_name = f"x{i + 1}"  # Variable names will be x1, x2, x3, etc.
        if st.session_state.var_types[i] == "Integer":
            vars[i + 1] = LpVariable(var_name, lowBound=0, cat="Integer")
        else:
            vars[i + 1] = LpVariable(var_name, lowBound=0, cat="Continuous")

    # Add the objective function to the linear program
    linear_program += lpSum([st.session_state.objective_coeffs[i] * vars[i + 1] for i in range(num_vars)])

    # Add constraints to the linear program
    for i in range(len(st.session_state.clean_constraints)):
        constraint_expr = lpSum([st.session_state.clean_constraints[i][j] * vars[j + 1] for j in range(num_vars)])
        if st.session_state.inequality_signs[i] == "<=":
            linear_program += (constraint_expr <= st.session_state.rhs_values[i])
        elif st.session_state.inequality_signs[i] == ">=":
            linear_program += (constraint_expr >= st.session_state.rhs_values[i])
        elif st.session_state.inequality_signs[i] == "=":
            linear_program += (constraint_expr == st.session_state.rhs_values[i])

    # Solve the linear program
    linear_program.solve()

    # Display the results
    st.subheader("Solution")
    st.write("Solution Status:", LpStatus[linear_program.status])
    for v in linear_program.variables():
        st.write(f"{v.name} = {v.varValue}")
    st.write("Objective Function Value:", value(linear_program.objective))
