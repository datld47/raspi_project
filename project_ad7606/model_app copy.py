import onnxruntime as ort
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import sys
import joblib
import os
import pandas as pd

def get_ort_session(path):
    sess_options = ort.SessionOptions()
    sess_options.log_severity_level = 3
    ort_session = ort.InferenceSession(path, sess_options=sess_options, providers=["CPUExecutionProvider"])
    return ort_session


def create_channel_dataframe(raw_data, selected_channels=['CH1','CH3'],all_channels=['CH1', 'CH2', 'CH3', 'CH4', 'CH5', 'CH6', 'CH7', 'CH8']):
    try:
        df_full = pd.DataFrame(data=raw_data, columns=all_channels)
        df_selected = df_full[selected_channels].copy()
        return df_selected
    except KeyError as e:
        print(f"Lỗi: Không tìm thấy kênh bạn yêu cầu trong danh sách gốc. Chi tiết: {e}")
        return None
    except ValueError as e:
        print(f"Lỗi: Kích thước mảng dữ liệu và số lượng tên kênh (all_channels) không khớp. Chi tiết: {e}")
        return None
    

class ONNXTimeSeriesModel:
    def __init__(self, ort_session, data_input, scaler_vibration, scaler_current):
        self.ort_session = ort_session

        # Scale dữ liệu
        data_input["CH1"] = scaler_vibration.transform(data_input[["CH1"]])
        data_input["CH3"] = scaler_current.transform(data_input[["CH3"]])

        # Convert sang numpy: (C, T)
        self.data_input = data_input[["CH1", "CH3"]].values.T.astype(np.float32)

        # Lấy input name động
        self.input_name = self.ort_session.get_inputs()[0].name

    def predict(self, sample=None):
        if sample is None:
            sample = self.data_input

        # Ensure shape (B, C, T)
        if sample.ndim == 2:
            sample = np.expand_dims(sample, axis=0)

        # Ensure dtype float32
        sample = sample.astype(np.float32)

        ort_inputs = {
            self.input_name: sample
        }

        ort_outs = self.ort_session.run(None, ort_inputs)

        logits = ort_outs[0]
        pred = np.argmax(logits, axis=1)

        return pred, logits



# if __name__ =="__main__":
#     ort_session = ort.InferenceSession("end_to_end_vibration.onnx")
#     dummy_signal = np.random.uniform(low=0.0, high=4.0, size=512)
#     predicted_label= predict_from_pi(ort_session,dummy_signal)
#     print(type(predicted_label))
#     print(predicted_label)