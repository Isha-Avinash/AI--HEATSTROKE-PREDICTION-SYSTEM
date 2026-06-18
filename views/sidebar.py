import os
from datetime import datetime

import pandas as pd
import streamlit as st

from services.model_service import get_model_metadata
from services.training_service import train_and_save_model
from storage.database import clear_database, get_all_records, load_demo_records


def render_sidebar():
    """Renders the demo control sidebar."""
    with st.sidebar:
        st.markdown("### Demo Control Panel")
        st.info("Heat stress can escalate quickly. Use this demo to screen, monitor, and prioritize people who may need cooling or medical attention.")

        st.markdown("---")

        st.markdown("### Model Snapshot")
        metadata = get_model_metadata()
        metrics = metadata.get("metrics", {})
        st.markdown(f"**Model Class:** `{metadata.get('model_type', 'N/A')}`")
        st.markdown(f"**Trained On:** `{metadata.get('training_date', 'N/A')}`")

        col_met1, col_met2 = st.columns(2)
        col_met1.metric("Accuracy", f"{metrics.get('accuracy', 0.0):.1f}%")
        col_met2.metric("Macro F1", f"{metrics.get('f1_score', 0.0):.1f}%")

        show_admin_tools = st.toggle("Show admin/demo tools", value=False)
        if show_admin_tools:
            with st.expander("Admin / Demo Toolkit", expanded=True):
                demo_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data", "sample_assessments.csv")
                if st.button("Load Client Demo Data", help="Replaces the demo seed batch and populates dashboards"):
                    inserted = load_demo_records(demo_csv_path)
                    st.success(f"Loaded {inserted} demo assessments.")
                    st.rerun()

                st.caption("Retraining rewrites the local model artifact and can take a minute.")
                if st.button("Retrain ML Pipeline", help="Regenerates synthetic clinical data and retrains classifier models"):
                    with st.spinner("Retraining classifier..."):
                        train_and_save_model()
                        st.success("Classifier successfully retrained!")
                        st.rerun()

        st.markdown("---")

        st.markdown("### Data Export")
        records = get_all_records()
        if records:
            df_export = pd.DataFrame(records)
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Logs as CSV",
                data=csv_data,
                file_name=f"heatstroke_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download all sqlite assessment logs",
            )

        if show_admin_tools:
            confirm_clear = st.checkbox("I understand this will remove all local assessment logs.")
            if st.button("Clear Assessment Logs", help="Remove all historical runs from SQLite", disabled=not confirm_clear):
                clear_database()
                st.success("All logs cleared successfully!")
                st.rerun()
