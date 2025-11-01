"""Sample 3 placeholder feature."""

import streamlit as st


def render(show_error, show_warning, show_info):
    st.markdown(
        """
        <div class="formWrap">
          <h2 class="formHead">Sample 3</h2>
          <p class="hint">Hook up your feature-specific logic here.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(
        "This module is ready for custom code. Use the provided helpers to display "
        "warnings or errors when wiring up your business logic."
    )

