import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests

webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=c1574fa7eb406578ec66a6aaf8a33c7328cc5b77a68660e63ac4b6d1db7c02df"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/equipmentcontrol-433909-2766349cdc33.json", scope)
client = gspread.authorize(creds)

sheet = client.open("asset_control").sheet1

with st.form("my_form"):
    location = st.selectbox("Select location", ["SSW", "TPK"])
    bag = st.number_input("BAG", min_value=0, max_value=10000, step=1)
    small_cage = st.number_input("SMALL CAGE", min_value=0, max_value=1200, step=1)
    big_cage = st.number_input("BIG CAGE", min_value=0, max_value=1200, step=1)
    pallet = st.number_input("PALLET", min_value=0, max_value=1200, step=1)
    submitted = st.form_submit_button("Submit")

if submitted:
    if bag == 0: 
        st.error("Age is required. Please enter BAG.")
    else:
        if small_cage == 0:  
            st.error("Age is required. Please enter SMALL CAGE.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([location, bag, small_cage, big_cage, pallet, timestamp])
            st.success("Data logged successfully!")
            
            google_webapp_url = "https://script.google.com/macros/s/AKfycbzIQ2nXATn20JM1rkOmZnQ5ohsDOYd2vRfMrmIdT75jC_p4Yc2ZDxpu8oNyfNS90--y/exec"
            try:
                response = requests.get(google_webapp_url, verify=False)
                if response.status_code == 200:
                    json_data = response.json()
                    
                    selected_node = next((entry for entry in json_data if entry['sc_node'] == location), None)
                    
                    if selected_node:
                        markdown_message = (f"**EQUIPMENT UPDATE FOR {selected_node['ds']}**\n\n"
                                            f"LOCATION: {selected_node['sc_node']}\n\n"
                                            f"FORECAST: {selected_node['fc_volume']}\n\n"
                                            f"**AVAILABLE**\n\n"
                                            f"- BAG: {selected_node['avail_bag']}\n\n"
                                            f"- SMALL CAGE: {selected_node['avail_small_cage']}\n\n"
                                            f"- BIG CAGE: {selected_node['avail_big_cage']}\n\n"
                                            f"- PALLET: {selected_node['avail_pallet']}\n\n"
                                            f"**REQUIRED**\n\n"
                                            f"- BAG: {selected_node['reqmt_bag']}\n\n"
                                            f"- SMALL CAGE: {selected_node['reqmt_small_cage']}\n\n"
                                            f"- BIG CAGE: {selected_node['reqmt_big_cage']}\n\n"
                                            f"- PALLET: {selected_node['reqmt_pallet']}\n\n")
                        
                        headers = {"Content-Type": "application/json"}
                        data = {
                            "msgtype": "markdown",
                            "markdown": {
                                "title": "Alert",
                                "text": markdown_message
                            }
                        }
                        response = requests.post(webhook_url, json=data, headers=headers)
                        
                        if response.status_code == 200:
                            st.success("DingTalk alert sent successfully!")
                        else:
                            st.error("Failed to send DingTalk alert.")
                    else:
                        st.error("No data found for the selected location.")
                else:
                    st.error("Failed to fetch data from Google Sheets.")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred: {e}")