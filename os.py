import streamlit as st
import csv
import os
from datetime import datetime


# ============================================================
# CRC-32 IMPLEMENTATION
# ============================================================

def crc32(data):
    polynomial = 0xEDB88320
    crc = 0xFFFFFFFF

    for byte in data:
        crc = crc ^ byte

        for i in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ polynomial
            else:
                crc = crc >> 1

    crc = crc ^ 0xFFFFFFFF

    return format(crc, "08X")


# ============================================================
# VERIFICATION HISTORY FILE
# ============================================================

HISTORY_FILE = "verification_history.csv"


def create_history_file():

    if not os.path.exists(HISTORY_FILE):

        with open(HISTORY_FILE, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Test ID",
                "Date and Time",
                "Original File",
                "Received File",
                "Original CRC-32",
                "Received CRC-32",
                "Status"
            ])


def get_next_test_id():

    create_history_file()

    with open(HISTORY_FILE, "r", newline="") as file:

        rows = list(csv.reader(file))

    number = len(rows)

    return "TEST-" + str(number).zfill(3)


def save_verification(
    test_id,
    original_file,
    received_file,
    original_crc,
    received_crc,
    status
):

    create_history_file()

    with open(HISTORY_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            test_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            original_file,
            received_file,
            original_crc,
            received_crc,
            status
        ])


# ============================================================
# READ PREVIOUS VERIFICATION DETAILS
# ============================================================

def load_history():

    create_history_file()

    with open(HISTORY_FILE, "r", newline="") as file:

        reader = csv.DictReader(file)

        return list(reader)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Hospital Report Transfer Validator",
    layout="wide"
)

st.title("Hospital Report Transfer Validator")

st.write(
    "CRC-32 Based Hospital Report Integrity Verification "
    "Between Sender and Receiver Departments"
)


# ============================================================
# FILE INPUT
# ============================================================

st.header("Sender Department")

sender_file = st.file_uploader(
    "Upload Original Hospital Report",
    type=["txt", "csv", "pdf", "docx"],
    key="sender"
)


st.header("Receiver Department")

receiver_file = st.file_uploader(
    "Upload Received Hospital Report",
    type=["txt", "csv", "pdf", "docx"],
    key="receiver"
)


# ============================================================
# ERROR SIMULATION
# ============================================================

st.header("Testing")

simulate_error = st.checkbox(
    "Simulate error in received data"
)


# ============================================================
# VERIFY
# ============================================================

if st.button("Verify Hospital Report"):

    if sender_file is None or receiver_file is None:

        st.error(
            "Please upload both the Original File and Received File."
        )

    else:

        # Read Sender file
        sender_data = sender_file.read()

        # Read Receiver file
        receiver_data = receiver_file.read()

        # ----------------------------------------------------
        # ERROR SIMULATION
        # ----------------------------------------------------

        if simulate_error:

            if len(receiver_data) > 0:

                receiver_data = bytearray(receiver_data)

                receiver_data[0] = receiver_data[0] ^ 1

                receiver_data = bytes(receiver_data)

        # ----------------------------------------------------
        # CRC-32 CALCULATION
        # ----------------------------------------------------

        original_crc = crc32(sender_data)

        received_crc = crc32(receiver_data)

        # ----------------------------------------------------
        # VERIFICATION
        # ----------------------------------------------------

        if original_crc == received_crc:

            status = "VALID"

        else:

            status = "CORRUPTED"

        # ----------------------------------------------------
        # SAVE VERIFICATION
        # ----------------------------------------------------

        test_id = get_next_test_id()

        save_verification(
            test_id,
            sender_file.name,
            receiver_file.name,
            original_crc,
            received_crc,
            status
        )

        # ----------------------------------------------------
        # DISPLAY CURRENT RESULT
        # ----------------------------------------------------

        st.header("Current Verification Result")

        col1, col2 = st.columns(2)

        with col1:

            st.write("Original CRC-32")

            st.code(original_crc)

        with col2:

            st.write("Received CRC-32")

            st.code(received_crc)

        if status == "VALID":

            st.success(
                "VALID - No corruption was detected."
            )

        else:

            st.error(
                "CORRUPTED - The received file has been modified."
            )

        st.write("Test ID:", test_id)


# ============================================================
# VERIFICATION SUMMARY
# ============================================================

history = load_history()

total_files = len(history)

valid_files = 0
corrupted_files = 0

for record in history:

    if record["Status"] == "VALID":

        valid_files = valid_files + 1

    elif record["Status"] == "CORRUPTED":

        corrupted_files = corrupted_files + 1


if total_files > 0:

    integrity_rate = (valid_files / total_files) * 100

else:

    integrity_rate = 0


# ============================================================
# SUMMARY
# ============================================================

st.header("CRC-32 Verification Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Total File Pairs",
        total_files
    )

with col2:

    st.metric(
        "Valid Files",
        valid_files
    )

with col3:

    st.metric(
        "Corrupted Files",
        corrupted_files
    )

with col4:

    st.metric(
        "Integrity Rate",
        f"{integrity_rate:.2f}%"
    )


# ============================================================
# OVERALL STATUS
# ============================================================

if total_files > 0:

    if corrupted_files == 0:

        st.success(
            f"ALL {total_files} FILE PAIR(S) ARE VALID"
        )

        st.write(
            "The CRC-32 values of all Original and Received "
            "Files are identical. No corruption was detected."
        )

    else:

        st.error(
            f"{corrupted_files} FILE PAIR(S) ARE CORRUPTED"
        )

        st.write(
            "A difference was detected between the Original "
            "and Received CRC-32 values."
        )


# ============================================================
# DETAILED RESULTS
# ============================================================

st.header("Detailed CRC-32 Results")

if total_files > 0:

    st.dataframe(
        history,
        use_container_width=True
    )

else:

    st.info(
        "No verification records are available yet."
    )


# ============================================================
# DOWNLOAD VERIFICATION HISTORY
# ============================================================

if total_files > 0:

    with open(HISTORY_FILE, "r") as file:

        csv_data = file.read()

    st.download_button(
        label="Download Verification Report",
        data=csv_data,
        file_name="crc32_verification_report.csv",
        mime="text/csv"
    )


# ============================================================
# CLEAR HISTORY
# ============================================================

st.header("Verification History")

if st.button("Clear Verification History"):

    with open(HISTORY_FILE, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Test ID",
            "Date and Time",
            "Original File",
            "Received File",
            "Original CRC-32",
            "Received CRC-32",
            "Status"
        ])

    st.success(
        "Verification history has been cleared."
    )

    st.rerun()