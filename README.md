# Machine Risk Monitor 
This project is a dynamic machine data management tool that allows users to configure custom machine attributes, create and track machine records, and evaluate machine risk levels locally. Built with Python, Streamlit, and SQLite, it uses JSON storage to support dynamic schema updates without needing database migrations.

## Technologies Used
- Backend & Web UI: Python, Streamlit
- Database: SQLite
- Machine Learning: Scikit-Learn, Pandas

## Project Setup

1. **Clone the Repository:**
   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd machine-risk-app

---

### Dynamic Field Challenge 

* **How the application handles new field?:**
When a new field like Humidity is added, the app saves its definition in the database's `fields` table. The user interface automatically updates to display a Humidity input form, and the entered values are stored inside a JSON column in the database. This allows new fields to be added without modifying the database schema.

* **Whether the exisiting ML model can use it?**
No. The existing model was trained only on Temperature, Pressure, and Vibration. It ignores additional fields like Humidity during predictions.

* **What would be the required for the ML model to use it in the future?**
To include Humidity in risk predictions, you need to collect historical data containing Humidity values along with their actual risk outcomes, retrain the model with Humidity included as an additional input feature, and update the prediction logic in the app to pass Humidity into the model.