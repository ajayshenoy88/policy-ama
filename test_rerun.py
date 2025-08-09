import streamlit as st
st.write(f"Streamlit version: {st.__version__}")
st.write(dir(st))  # Shows all available attributes

if hasattr(st, "experimental_rerun"):
    st.write("st.experimental_rerun is available!")
else:
    st.write("st.experimental_rerun is NOT available.")
