import sqlite3
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="MACHINE RISK MONITOR", layout="wide")

st.markdown("""
    <style>
    :root {
      --bg-dark: #2c3e50;        /* Soft blue-slate background */
      --bg-card: #34495e;        /* Lighter card surface */
      --border-color: #4a6572;    /* Subtle card border */
      --text-main: #ffffff;       /* Pure white text */
      --color-safe: #2ecc71;
      --color-warning: #f1c40f;
      --color-danger: #ef4444;
      --radius: 8px;
    }

    /* Global Soft Slate Theme */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }

    /* Force all field labels and headings to be high-contrast white */
    .stApp label, .stMarkdown, p, span, div[data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* Form container and tab card background */
    div[data-baseweb="tab-panel"], div.stForm {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius) !important;
        padding: 20px !important;
    }
/* Gradient Heading Styling */
    .stApp h1 {
        background: linear-gradient(90deg, #60a5fa, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        padding-bottom: 5px;
    }
    /* Input text box styling for high visibility */
    .stTextInput input, .stNumberInput input, .stSelectbox div[role="combobox"] {
        color: #1a252f !important;
        background-color: #f8f9fa !important;
        border-radius: 4px !important;
    }

    /* Buttons styling */
    .stButton button, div.stForm button {
        background-color: #2980b9 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: none !important;
    }
    .stButton button:hover, div.stForm button:hover {
        background-color: #3498db !important;
    }

    /* Table Styling for Clean Machine Values Display */
    .stTable td, .stTable th, table td, table th {
        color: #ffffff !important;
        background-color: #34495e !important;
        border-bottom: 1px solid #4a6572 !important;
    }

    /* High Risk Alert Red Styling */
    .danger-alert {
        background-color: rgba(239, 68, 68, 0.25) !important;
        border: 2px solid #ef4444 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-top: 15px !important;
        color: #ffffff !important;
        text-align: center;
    }
    .danger-alert h3 {
        color: #f87171 !important;
        margin: 0 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)



def get_db_connection():
    conn = sqlite3.connect('machines.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            field_type TEXT NOT NULL,
            is_required INTEGER DEFAULT 0,
            options TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM fields")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO fields (name, field_type, is_required, options) VALUES ('Temperature', 'Number', 1, '')")
        cursor.execute("INSERT INTO fields (name, field_type, is_required, options) VALUES ('Pressure', 'Number', 1, '')")
        cursor.execute("INSERT INTO fields (name, field_type, is_required, options) VALUES ('Vibration', 'Dropdown', 1, 'Low, Medium, High')")
    
    conn.commit()
    conn.close()

init_db()


def load_model():
    with open('risk_model.json', 'r') as f:
        return json.load(f)

try:
    model_rules = load_model()
except Exception:
    model_rules = None

def predict_risk(temp, pressure, vibration):
    high_count = 0
    if temp >= 80:
        high_count += 1
    if pressure >= 120:
        high_count += 1
    if str(vibration).strip().lower() == 'high':
        high_count += 1
        
    if high_count >= 2:
        return 'High'
    elif high_count == 1:
        return 'Medium'
    else:
        return 'Low'


st.title("⚙️ MACHINE RISK MONITOR")
st.caption("Dynamic machine record management and local risk assessment dashboard")

tab1, tab2, tab3 = st.tabs(["Field Configuration", "Machine Records", "Risk Prediction"])


with tab1:
    st.header("Configured Dynamic Fields")
    conn = get_db_connection()
    fields = conn.execute("SELECT * FROM fields").fetchall()
    
    for f in fields:
        is_req_text = 'Yes' if f['is_required'] else 'No'
        opts_text = f" | Options: {f['options']}" if f['options'] else ""
        st.write(f"- **{f['name']}** ({f['field_type']}) - Required: {is_req_text}{opts_text}")
    
    st.subheader("Add New Dynamic Field")
    with st.form("add_field_form"):
        field_name = st.text_input("Field Name")
        field_type = st.selectbox("Field Type", ["Text", "Number", "Dropdown"])
        is_req = st.checkbox("Required")
        options = st.text_input("Dropdown Options (comma-separated, e.g. Low, Medium, High)")
        
        submit_field = st.form_submit_button("Save Field")
        if submit_field:
            if field_name.strip():
                try:
                    conn.execute("INSERT INTO fields (name, field_type, is_required, options) VALUES (?, ?, ?, ?)",
                                 (field_name.strip(), field_type, 1 if is_req else 0, options.strip()))
                    conn.commit()
                    st.success(f"Added field '{field_name}' successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Field name already exists.")
            else:
                st.warning("Please enter a field name.")
    conn.close()


with tab2:
    st.header("Manage Machine Records")
    conn = get_db_connection()
    fields = conn.execute("SELECT * FROM fields").fetchall()
    
    st.subheader("Add Machine")
    with st.form("add_machine_form"):
        m_name = st.text_input("Machine Name *")
        dynamic_inputs = {}
        
        for f in fields:
            label = f"{f['name']}{' *' if f['is_required'] else ''}"
            if f['field_type'] == 'Number':
                dynamic_inputs[f['name']] = st.number_input(label, value=0.0)
            elif f['field_type'] == 'Dropdown':
                opts = [o.strip() for o in f['options'].split(',') if o.strip()]
                dynamic_inputs[f['name']] = st.selectbox(label, opts if opts else ['N/A'])
            else:
                dynamic_inputs[f['name']] = st.text_input(label)
                
        submit_machine = st.form_submit_button("Save Machine")
        if submit_machine:
            if m_name.strip():
                data_json = json.dumps(dynamic_inputs)
                conn.execute("INSERT INTO machines (name, data) VALUES (?, ?)", (m_name.strip(), data_json))
                conn.commit()
                st.success(f"Machine '{m_name}' created!")
                st.rerun()
            else:
                st.warning("Machine Name is required.")

    st.subheader("Saved Machine Records")
    machines = conn.execute("SELECT * FROM machines").fetchall()
    if machines:
        records = []
        for m in machines:
            row = {'ID': m['id'], 'Machine Name': m['name']}
            row.update(json.loads(m['data']))
            records.append(row)
        
        df_display = pd.DataFrame(records)
        st.dataframe(df_display, use_container_width=True)
        
        del_id = st.number_input("Enter Machine ID to Delete", min_value=1, step=1)
        if st.button("Delete Machine"):
            conn.execute("DELETE FROM machines WHERE id = ?", (del_id,))
            conn.commit()
            st.success(f"Deleted machine ID {del_id}")
            st.rerun()
    else:
        st.info("No machine records found.")
    conn.close()


with tab3:
    st.header("Run Risk Prediction")
    conn = get_db_connection()
    machines = conn.execute("SELECT * FROM machines").fetchall()
    conn.close()
    
    if machines:
        m_options = {m['name']: json.loads(m['data']) for m in machines}
        selected_m = st.selectbox("Select Machine to Evaluate", list(m_options.keys()))
        
        m_data = m_options[selected_m]
        
        st.subheader("Machine Specifications")
        formatted_df = pd.DataFrame(list(m_data.items()), columns=["Field Name", "Configured Value"])
        st.table(formatted_df)
        
        if st.button("Predict Risk"):
            temp = float(m_data.get('Temperature', 0))
            press = float(m_data.get('Pressure', 0))
            vib = m_data.get('Vibration', 'Low')
            
            pred = predict_risk(temp, press, vib)
            
            if pred == 'High':
                st.markdown("""
                    <div class="danger-alert">
                        <h3>🚨 HIGH RISK DETECTED</h3>
                        <p style="margin-top: 8px; font-weight: 600; color: #ffffff;">Warning: Parameters exceed safe operational limits!</p>
                    </div>
                """, unsafe_allow_html=True)
            elif pred == 'Medium':
                st.warning(f"⚠️ Predicted Risk Level: {pred}")
            else:
                st.success(f"✅ Predicted Risk Level: {pred}")
    else:
        st.info("No machines available. Please create a machine record in 'Machine Records' tab first.")