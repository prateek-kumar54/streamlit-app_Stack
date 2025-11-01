"""Sample 5 placeholder feature."""

import streamlit as st


def render(show_error, show_warning, show_info):
    st.markdown(
        """
        <div class="formWrap">
          <h2 class="formHead">Sample 5</h2>
          <p class="hint">Drop in your feature-specific controls and outputs.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "Need to alert users about something? Use the toast helpers passed into this module "
        "for consistent UI feedback."
    )

