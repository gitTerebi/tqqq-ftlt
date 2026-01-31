import pandas as pd
import yfinance as yf
import time


def download_with_retry(tickers, start_date, end_date=None, max_retries=3, retry_delay_sec=2):
    data_frames = {}

    for ticker in tickers:
        last_err = None

        for attempt in range(1, max_retries + 1):
            try:
                if (end_date is not None):
                    df = yf.download(ticker, start=pd.Timestamp(start_date),
                                     end=pd.Timestamp(end_date) + pd.Timedelta(days=1), threads=False)
                else:
                    df = yf.download(ticker, start=pd.Timestamp(start_date), threads=False)

                if df.empty:
                    raise ValueError("Empty dataframe returned")

                df.index.name = "datetime"

                # Normalize columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df.columns = df.columns.str.lower()

                data_frames[ticker] = df
                break  # success

            except Exception as e:
                last_err = e
                print(f"[{ticker}] attempt {attempt}/{max_retries} failed: {e}")

                if attempt < max_retries:
                    time.sleep(retry_delay_sec)

        else:
            # only executes if all retries failed
            print(f"[{ticker}] FAILED after {max_retries} retries: {last_err}")

    return data_frames
