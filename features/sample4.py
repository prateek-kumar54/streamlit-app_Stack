"""Sample 4 placeholder feature."""

import streamlit as st


def render(show_error, show_warning, show_info):
    st.markdown(
        """
        <div class="formWrap">
          <h2 class="formHead">Sample 4</h2>
          <p class="hint">Modular scaffolding keeps this workflow isolated from the others.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.success("You're all set to build out Sample 4's experience in this dedicated module.")

