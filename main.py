import streamlit as st
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="QR Code Generator", page_icon=":white_medium_square:", layout="centered")

st.title("QR Code Generator")
with st.form("my_form"):
    st.write("Generate QR")
    # Every form must have a submit button.
    submitted = st.form_submit_button("Generate")
   
    if submitted:
        response = requests.get(f"https://europe-west3-jochr-416119.cloudfunctions.net/generate_shareable_link")
        if response.status_code == 200:
            url = response.json()["url"]
            st.success(f"Shareable link generated: {url}")
        else:
            st.error("Failed to generate shareable link. Please try again.")

        response = requests.get(f"https://europe-west3-jochr-416119.cloudfunctions.net/generate_qrcode?link={url}")

        # Check if the request was successful
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))        
            st.image(img, caption="Generated QR Code")

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            
        else:
            st.error("Failed to generate QR Code. Please try again.")

# if response.status_code == 200:
#     st.download_button(
#         label="Download QR Code",
#         data=buffer,
#         file_name="qr_code.png",
#         mime="image/png"
#     )
