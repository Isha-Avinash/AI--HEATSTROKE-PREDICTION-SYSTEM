import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def show_graph():

    try:

        data = pd.read_csv("patient_data.csv")

        data.columns = data.columns.str.strip()

        st.subheader("📊 Heatstroke Analytics Dashboard")

        # ===== KPI CARDS =====

        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric(
                "📋 Total Records",
                len(data)
            )

        with k2:

            if "Risk" in data.columns:

                high_risk = len(
                    data[
                        data["Risk"]
                        .astype(str)
                        .str.upper()
                        == "HIGH"
                    ]
                )

                st.metric(
                    "🚨 High Risk Cases",
                    high_risk
                )

        with k3:

            if "BMI" in data.columns:

                bmi_avg = round(
                    pd.to_numeric(
                        data["BMI"],
                        errors="coerce"
                    ).mean(),
                    1
                )

                st.metric(
                    "📊 Avg BMI",
                    bmi_avg
                )

        st.markdown("---")

        col1, col2 = st.columns(2)

        # ===== RISK DISTRIBUTION =====

        with col1:

            if "Risk" in data.columns:

                risk_count = (
                    data["Risk"]
                    .astype(str)
                    .value_counts()
                )

                fig1, ax1 = plt.subplots()

                ax1.pie(
                    risk_count.values,
                    labels=risk_count.index,
                    autopct="%1.1f%%"
                )

                ax1.set_title(
                    "Risk Distribution"
                )

                st.pyplot(fig1)

        # ===== TEMPERATURE TREND =====

        with col2:

            if "Temperature" in data.columns:

                data["Temperature"] = pd.to_numeric(
                    data["Temperature"],
                    errors="coerce"
                )

                fig2, ax2 = plt.subplots()

                ax2.plot(
                    data["Temperature"],
                    marker="o",
                    linewidth=3
                )

                ax2.set_title(
                    "Temperature Trend"
                )

                ax2.set_xlabel(
                    "Records"
                )

                ax2.set_ylabel(
                    "Temperature (°C)"
                )

                st.pyplot(fig2)

        st.markdown("---")

        # ===== BMI ANALYTICS =====

        if "BMI" in data.columns:

            st.subheader(
                "📈 BMI Analytics"
            )

            bmi_data = pd.to_numeric(
                data["BMI"],
                errors="coerce"
            )

            fig3, ax3 = plt.subplots()

            ax3.hist(
                bmi_data,
                bins=5
            )

            ax3.set_title(
                "BMI Distribution"
            )

            ax3.set_xlabel(
                "BMI"
            )

            ax3.set_ylabel(
                "Count"
            )

            st.pyplot(fig3)

        st.markdown("---")

        st.success(
            "✅ Analytics Generated Successfully"
        )

    except Exception as e:

        st.error(
            f"Error: {e}"
        )