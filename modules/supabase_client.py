import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date

class SupabaseManager:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: Client = create_client(self.url, self.key)

    def insert_record(self, data: dict):
        """
        Inserts a new OEE record into the 'registros_oee' table.
        Args:
            data (dict): Dictionary reflecting the 'registros_oee' schema.
        Returns:
            response: API response from Supabase.
        """
        try:
            data['created_at'] = datetime.utcnow().isoformat()
            response = self.client.table('registros_oee').insert(data).execute()
            return response
        except Exception as e:
            st.error(f"Error inserting record: {e}")
            return None

    def fetch_records(self, start_date: date, end_date: date, linea: str = None):
        """
        Fetches OEE records within a date range and optionally filters by line.
        """
        try:
            query = self.client.table('registros_oee').select("*")\
                .gte('fecha', start_date.isoformat())\
                .lte('fecha', end_date.isoformat())
            
            if linea:
                query = query.eq('linea', linea)
            
            response = query.execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            st.error(f"Error fetching records: {e}")
            return pd.DataFrame()

# Helper to initialize from st.secrets if available
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return SupabaseManager(url, key)
    except KeyError:
        st.warning("⚠️ Supabase credentials not found in secrets.toml. Please add [supabase] section with 'url' and 'key'.")
        return None
