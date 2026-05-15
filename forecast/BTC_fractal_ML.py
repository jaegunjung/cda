import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

import utils as ut

CRYPTO_SYMBOL = {'bitcoin': 'BTC'}
# WNDW_SZ = 20
# WNDW_SZ = 7
WNDW_SZ = 14


# Define Higuchi
def Higuchi(X, k_max=10, epsilon=0.1):
    n = len(X)
    L = np.arange(2, k_max + 2)
    K = np.zeros(k_max)

    for k in range(1, k_max + 1):
        L_k = np.zeros((k, n))
        for m in range(k):
            idx = np.arange(m, n, k_max)
            L_k[m, :len(idx)] = X[idx]

        mean_L_k = np.mean(L_k, axis=0)
        mean_L_k = np.abs(np.diff(mean_L_k))

        # print('X, X**2, (2 * (n // k_max) * np.mean(X**2 + epsilon))')
        # print(X, X**2, (2 * (n // k_max) * np.mean(X**2 + epsilon)))
        K[k - 1] = (np.sum(mean_L_k) * (n - 1) / ((n - k_max) * k_max)) / (2 * (n // k_max) * np.mean(X**2 + epsilon))

    return np.log(K) / np.log(L)


# Function to create features and target for linear regression
def create_features_target(data, window_size):
    features = []
    target = []

    for i in range(len(data) - window_size):
        window = data[i:i + window_size]
        features.append(Higuchi(window))
        target.append(data[i + window_size])

    return np.array(features), np.array(target)


def load_crypto(crypto):
    """
    Calculate a number of days to load
    :param crypto: the cryptocurrency such as bitcoin
    :return:
    """
    # select DATEDIFF(SECOND, '1970-01-01 00:00:00', Date) as UnixEpochTime, Open_Price_USD from CryptoDaily where Crypto = '{}'
    qry = """    
    select Date as UnixEpochTime, Open_Price_USD from CryptoDaily where Crypto = '{}'
    """.format(CRYPTO_SYMBOL[crypto])
    df = ut.query_db(qry)
    # df.set_index('Date', inplace=True)
    return df


def forecast(n_prdct_dys=40):
    # Load the Bitcoin price data
    df = load_crypto('bitcoin')

    # Split data into training and testing sets
    train_size = len(df) - n_prdct_dys
    # train_size = int(len(df) * 0.99)
    X_train = df[:train_size]['UnixEpochTime'].to_numpy()
    y_train = df[:train_size]['Open_Price_USD'].to_numpy()
    X_test = df[train_size:]['UnixEpochTime'].to_numpy()
    y_test = df[train_size:]['Open_Price_USD'].to_numpy()

    # Create features and target for training set
    ftrs_trn, tgt_trn = create_features_target(y_train, WNDW_SZ)

    # Create features and target for testing set
    X_full = np.concatenate((X_train, X_test), axis=0)
    y_full = np.concatenate((y_train, y_test), axis=0)
    ftrs_fll, _ = create_features_target(y_full, WNDW_SZ)

    # Train a linear regression model
    model = LinearRegression()
    model.fit(ftrs_trn, tgt_trn)

    # Initialize an empty array to store forecasted values
    forecasted_values = []

    # Perform forecasting
    for i in range(len(y_test)):
        # If there are not enough previous values for forecasting, skip this iteration
        if i <= WNDW_SZ:
            forecasted_values.append(np.nan)
            continue

        # Use the entire dataset to calculate features, including the previously forecasted values
        concatenated_np_array = np.concatenate((np.array(forecasted_values), y_test[:i]), axis=0)
        X_current, _ = create_features_target(concatenated_np_array, WNDW_SZ)

        # Predict the next value
        y_pred = model.predict(X_current[-1].reshape(1, -1))[0]

        # Append the predicted value to the list of forecasted values
        forecasted_values.append(y_pred)

    # Scaling forecasted_value
    ratio = y_test[WNDW_SZ+1]/forecasted_values[WNDW_SZ+1]
    forecasted_values = [e * ratio for e in forecasted_values]
    # Plot the results
    # plt.plot(X_full[:train_size], y_train, label='Training')
    plt.plot(X_full[train_size:], y_test, label='Actual')
    new_timestamp = X_full[-1] + pd.Timedelta(days=1)
    X_full_p1 = np.append(X_full, new_timestamp)
    forecasted_index = X_full_p1[train_size + 1: train_size + 1 + len(forecasted_values)]
    plt.plot(forecasted_index, forecasted_values, label='Forecasted')
    plt.legend()
    plt.show()

    # # Calculate the mean squared error
    # mse = mean_squared_error(y_test[WNDW_SZ:], y_pred)
    #
    # # Print the mean squared error
    # print('The mean squared error is:', mse)
    #
    # # Plot the results
    # plt.plot(X_test[WNDW_SZ:], y_test[WNDW_SZ:], label='Actual')
    # plt.plot(X_test[WNDW_SZ:], y_pred, label='Predicted')
    # plt.legend()
    # plt.show()


if __name__ == '__main__':
    ut.time_to_run(forecast)
