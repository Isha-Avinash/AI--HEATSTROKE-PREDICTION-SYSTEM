import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


def show_graph():

    try:

        data = pd.read_csv("patient_data.csv")
        data.columns = data.columns.str.strip()

        st.subheader("📊 Advanced Heatstroke Analytics Dashboard")

        # KPI CARDS
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric("📋 Total Records", len(data))

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
                st.metric("🚨 High Risk", high_risk)

        with k3:
            if "BMI" in data.columns:
                bmi_avg = round(
                    pd.to_numeric(
                        data["BMI"],
                        errors="coerce"
                    ).mean(),
                    1
                )
                st.metric("📊 Avg BMI", bmi_avg)

        with k4:
            if "Temperature" in data.columns:
                avg_temp = round(
                    pd.to_numeric(
                        data["Temperature"],
                        errors="coerce"
                    ).mean(),
                    1
                )
                st.metric(
                    "🌡 Avg Temp",
                    f"{avg_temp}°C"
                )

        st.markdown("---")

        # TREND SUMMARY
        st.subheader("📈 Trend Summary")

        avg_temp = round(
            pd.to_numeric(
                data["Temperature"],
                errors="coerce"
            ).mean(),
            1
        )

        avg_bmi = round(
            pd.to_numeric(
                data["BMI"],
                errors="coerce"
            ).mean(),
            1
        )

        high_cases = len(
            data[
                data["Risk"]
                .astype(str)
                .str.upper()
                == "HIGH"
            ]
        )

        st.info(f"""
🌡 Average Temperature : {avg_temp}°C

⚖ Average BMI : {avg_bmi}

🚨 High Risk Cases : {high_cases}

📋 Total Records : {len(data)}
""")

        st.markdown("---")

        # ROW 1
        col1, col2 = st.columns(2)

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
                    autopct="%1.1f%%",
                    wedgeprops={"width": 0.4}
                )

                centre_circle = plt.Circle(
                    (0, 0),
                    0.60,
                    fc="white"
                )

                fig1.gca().add_artist(
                    centre_circle
                )

                ax1.set_title(
                    "Risk Distribution"
                )

                st.pyplot(fig1)

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

                ax2.set_xlabel("Records")
                ax2.set_ylabel("Temperature (°C)")

                st.pyplot(fig2)

        st.markdown("---")

        # ROW 2
        col3, col4 = st.columns(2)

        with col3:

            if "BMI" in data.columns:

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

                st.pyplot(fig3)

        with col4:

            if "Risk" in data.columns:

                risk_count = (
                    data["Risk"]
                    .astype(str)
                    .value_counts()
                )

                fig4, ax4 = plt.subplots()

                ax4.bar(
                    risk_count.index,
                    risk_count.values
                )

                ax4.set_title(
                    "Risk Level Count"
                )

                st.pyplot(fig4)

        st.markdown("---")

        # WATER TREND
        if "Water Intake" in data.columns:

            st.subheader(
                "💧 Water Intake Trend"
            )

            data["Water Intake"] = pd.to_numeric(
                data["Water Intake"],
                errors="coerce"
            )

            fig6, ax6 = plt.subplots()

            ax6.plot(
                data["Water Intake"],
                marker="o",
                linewidth=3
            )

            ax6.set_title(
                "Water Intake Trend"
            )

            st.pyplot(fig6)

        st.markdown("---")

        # BMI VS TEMP
        if (
            "BMI" in data.columns
            and
            "Temperature" in data.columns
        ):

            st.subheader(
                "📈 Temperature vs BMI Analysis"
            )

            fig5, ax5 = plt.subplots()

            ax5.scatter(
                pd.to_numeric(
                    data["BMI"],
                    errors="coerce"
                ),
                pd.to_numeric(
                    data["Temperature"],
                    errors="coerce"
                )
            )

            ax5.set_xlabel("BMI")
            ax5.set_ylabel("Temperature")

            st.pyplot(fig5)

        st.markdown("---")

        st.subheader("🗂 Recent Patient Records")

        st.dataframe(
            data.tail(10),
            use_container_width=True
        )

        st.success(
            "✅ Analytics Generated Successfully"
        )

    except Exception as e:

        st.error(
            f"Error: {e}"
        )