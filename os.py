import streamlit as st
import csv
import os
from datetime import datetime


# ============================================================
# CRC-3 IMPLEMENTATION
# ============================================================

def crc3(data):
    # CRC-3 polynomial: x^3 + x + 1 -> binary 1011
    polynomial = 0b1011
    width = 3
    crc = 0

    for byte in data:
        crc = crc ^ byte

        for i in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ (polynomial << (8 - width))) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return format(crc >> (8 - width), "03b")


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
# INPUT CONVERSION HELPERS
# ============================================================

def text_to_bytes(text):
    return text.encode("utf-8")


def binary_to_bytes(binary_str):

    binary_str = binary_str.strip().replace(" ", "")

    # Pad so length is a multiple of 8
    padding = (8 - len(binary_str) % 8) % 8
    binary_str = binary_str + ("0" * padding)

    byte_values = []

    for i in range(0, len(binary_str), 8):
        byte_chunk = binary_str[i:i + 8]
        byte_values.append(int(byte_chunk, 2))

    return bytes(byte_values)


def is_valid_binary(binary_str):

    binary_str = binary_str.strip().replace(" ", "")

    if len(binary_str) == 0:
        return False

    for ch in binary_str:
        if ch not in ("0", "1"):
            return False

    return True


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
                "Input Type",
                "Original Source",
                "Received Source",
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
    input_type,
    original_source,
    received_source,
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
            input_type,
            original_source,
            received_source,
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
# INPUT TYPE SELECTION
# ============================================================

st.header("Select Input Type")

input_type = st.radio(
    "Choose how the hospital report data will be provided",
    ["File Upload", "Text Message", "Binary Data"],
    horizontal=True
)


# ============================================================
# SENDER DEPARTMENT INPUT
# ============================================================

st.header("Sender Department")

sender_data = None
sender_source = None

if input_type == "File Upload":

    sender_file = st.file_uploader(
        "Upload Original Hospital Report",
        type=["txt", "csv", "pdf", "docx"],
        key="sender_file"
    )

    if sender_file is not None:
        sender_data = sender_file.read()
        sender_source = sender_file.name

elif input_type == "Text Message":

    sender_text = st.text_area(
        "Enter Original Report Text",
        key="sender_text"
    )

    if sender_text:
        sender_data = text_to_bytes(sender_text)
        sender_source = sender_text

elif input_type == "Binary Data":

    sender_binary = st.text_input(
        "Enter Original Binary Data (e.g. 101101)",
        key="sender_binary"
    )

    if sender_binary:

        if is_valid_binary(sender_binary):
            sender_data = binary_to_bytes(sender_binary)
            sender_source = sender_binary
        else:
            st.warning("Binary input must contain only 0s and 1s.")


# ============================================================
# RECEIVER DEPARTMENT INPUT
# ============================================================

st.header("Receiver Department")

receiver_data = None
receiver_source = None

if input_type == "File Upload":

    receiver_file = st.file_uploader(
        "Upload Received Hospital Report",
        type=["txt", "csv", "pdf", "docx"],
        key="receiver_file"
    )

    if receiver_file is not None:
        receiver_data = receiver_file.read()
        receiver_source = receiver_file.name

elif input_type == "Text Message":

    receiver_text = st.text_area(
        "Enter Received Report Text",
        key="receiver_text"
    )

    if receiver_text:
        receiver_data = text_to_bytes(receiver_text)
        receiver_source = receiver_text

elif input_type == "Binary Data":

    receiver_binary = st.text_input(
        "Enter Received Binary Data (e.g. 101101)",
        key="receiver_binary"
    )

    if receiver_binary:

        if is_valid_binary(receiver_binary):
            receiver_data = binary_to_bytes(receiver_binary)
            receiver_source = receiver_binary
        else:
            st.warning("Binary input must contain only 0s and 1s.")


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

    if sender_data is None or receiver_data is None:

        st.error(
            "Please provide both the Original and Received data."
        )

    else:

        # ----------------------------------------------------
        # ERROR SIMULATION
        # ----------------------------------------------------

        if simulate_error:

            if len(receiver_data) > 0:

                receiver_data = bytearray(receiver_data)

                receiver_data[0] = receiver_data[0] ^ 1

                receiver_data = bytes(receiver_data)

        # ----------------------------------------------------
        # CRC CALCULATION
        # ----------------------------------------------------

        # Binary Data uses CRC-3 only.
        if input_type == "Binary Data":

            original_crc3 = crc3(sender_data)
            received_crc3 = crc3(receiver_data)

            # Use CRC-3 values for saving and verification.
            original_crc = original_crc3
            received_crc = received_crc3

            crc_match = original_crc3 == received_crc3

        # File Upload and Text Message use CRC-32.
        else:

            original_crc = crc32(sender_data)
            received_crc = crc32(receiver_data)

            crc_match = original_crc == received_crc

        # ----------------------------------------------------
        # VERIFICATION
        # ----------------------------------------------------

        if crc_match:

            status = "VALID"

        else:

            status = "CORRUPTED"

        # ----------------------------------------------------
        # SAVE VERIFICATION
        # ----------------------------------------------------

        test_id = get_next_test_id()

        save_verification(
            test_id,
            input_type,
            sender_source,
            receiver_source,
            original_crc,
            received_crc,
            status
        )

        # ----------------------------------------------------
        # DISPLAY CURRENT RESULT
        # ----------------------------------------------------

        st.header("Current Verification Result")

        if input_type == "Binary Data":

            st.subheader("CRC-3 Test Result")

            crc3_col1, crc3_col2 = st.columns(2)

            with crc3_col1:
                st.write("Original CRC-3")
                st.code(original_crc3)

            with crc3_col2:
                st.write("Received CRC-3")
                st.code(received_crc3)

            if original_crc3 == received_crc3:
                st.info("CRC-3 Check: MATCH")
            else:
                st.warning("CRC-3 Check: MISMATCH")

        else:

            st.subheader("CRC-32 Test Result")

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
            "Input Type",
            "Original Source",
            "Received Source",
            "Original CRC-32",
            "Received CRC-32",
            "Status"
        ])

    st.success(
        "Verification history has been cleared."
    )

    st.rerun()