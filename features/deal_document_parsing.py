"""Deal Document Parsing feature module."""

import streamlit as st


def render(show_error, show_warning, show_info):
    st.markdown(
        """
        <div class="formWrap">
          <h2 class="formHead">Deal Document Parsing</h2>
          <p class="hint">This workflow is under construction. Check back soon for an interactive demo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "We're finalizing the extraction templates for deal documents. "
        "If you have sample files you'd like us to prioritize, drop us a note."
    )

